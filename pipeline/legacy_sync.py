import time

from os import environ
import json
from datetime import datetime

import mysql.connector
from lxml import etree as ET
from mysql.connector import errorcode
import orjson

from .storage import get_connection, dict_factory
from .legacy_publication import Publication
from .swepublog import logger as log

LEGACY_SEARCH_USER = environ.get("SWEPUB_LEGACY_SEARCH_USER")
LEGACY_SEARCH_PASSWORD = environ.get("SWEPUB_LEGACY_SEARCH_PASSWORD")
LEGACY_SEARCH_HOST = environ.get("SWEPUB_LEGACY_SEARCH_HOST")
LEGACY_SEARCH_DATABASE = environ.get("SWEPUB_LEGACY_SEARCH_DATABASE")

# To set up a local database for testing, install mysql-server, create a database:
# create database swepub_legacy;
# use swepub_legacy;
# ...and execute the following CREATE TABLE statements, and set the env vars above.

# CREATE TABLE `enriched` (
#   `record_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
#   `identifier` varchar(128) NOT NULL,
#   `origin` varchar(32) NOT NULL,
#   `target` varchar(32) NOT NULL,
#   `format` varchar(32) NOT NULL,
#   `data` mediumtext NOT NULL,
#   `sets` text NOT NULL,
#   `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
#   `remote_timestamp` varchar(32) NOT NULL DEFAULT '1950-01-01T00:00:00Z',
#   `deleted` tinyint(1) NOT NULL DEFAULT 0,
#   `duplicateof` varchar(128) DEFAULT NULL,
#   PRIMARY KEY (`record_id`),
#   UNIQUE KEY `identifier` (`identifier`) USING BTREE,
#   KEY `deleted` (`deleted`) USING BTREE,
#   KEY `target_deleted` (`deleted`) USING BTREE,
#   KEY `target` (`target`) USING BTREE,
#   KEY `ts` (`timestamp`) USING BTREE,
#   KEY `origin` (`origin`) USING BTREE,
#   KEY `sets` (`sets`(100)) USING BTREE,
#   KEY `pri_tar_ts_idx` (`record_id`,`target`,`timestamp`)
# ) ENGINE=InnoDB AUTO_INCREMENT=53683352 DEFAULT CHARSET=utf8mb4;
#
# CREATE TABLE `record` (
#   `record_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
#   `identifier` varchar(128) NOT NULL,
#   `origin` varchar(32) NOT NULL,
#   `target` varchar(32) NOT NULL,
#   `format` varchar(32) NOT NULL,
#   `data` mediumtext NOT NULL,
#   `sets` text NOT NULL,
#   `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
#   `remote_timestamp` varchar(32) NOT NULL DEFAULT '1950-01-01T00:00:00Z',
#   `deleted` tinyint(1) NOT NULL DEFAULT 0,
#   PRIMARY KEY (`record_id`),
#   UNIQUE KEY `identifier` (`identifier`) USING BTREE,
#   KEY `deleted` (`deleted`) USING BTREE,
#   KEY `target_deleted` (`deleted`) USING BTREE,
#   KEY `target` (`target`) USING BTREE,
#   KEY `ts` (`timestamp`) USING BTREE,
#   KEY `origin` (`origin`) USING BTREE,
#   KEY `sets` (`sets`(100)) USING BTREE,
#   KEY `pri_tar_ts_idx` (`record_id`,`target`,`timestamp`)
# ) ENGINE=InnoDB AUTO_INCREMENT=53683825 DEFAULT CHARSET=utf8mb4;


def _get_mysql_connection():
    try:
        cnx = mysql.connector.connect(
            user=LEGACY_SEARCH_USER,
            password=LEGACY_SEARCH_PASSWORD,
            host=LEGACY_SEARCH_HOST,
            database=LEGACY_SEARCH_DATABASE,
        )
        # This charset and collation is what is needed and matches table's (but is also default):
        # cnx.set_charset_collation(charset="utf8mb4", collation="utf8mb4_general_ci")
        return cnx
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            log.warning("Something is wrong with your username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            log.warning("Database does not exist")
        else:
            log.error(err)
    return None


def _sets(xml):
    sets = []
    root = ET.fromstring(xml)
    for setSpec in root.xpath("//*[local-name() = 'setSpec']"):
        sets.append(setSpec.text)
    if len(sets) > 0:
        return ", ".join(sets)
    return ""


def _remote_timestamp(xml):
    root = ET.fromstring(xml)
    datestamps = root.xpath("//*[local-name() = 'datestamp']")
    if len(datestamps) > 0:
        return datestamps[0].text
    return datetime.now().isoformat()


def legacy_sync(hours=24):
    with get_connection() as con, _get_mysql_connection() as mysql_con:
        cur = con.cursor()
        cur.row_factory = dict_factory
        mysql_cur = mysql_con.cursor(prepared=True)

        # Process records modified < `hours` ago, default < 24 hours agos
        # TODO: look at last_harvest_time (different for each source)?
        modified_since = int(time.time()) - 60 * 60 * hours

        # We need to INSERT/UPDATE any records that have been modified since some time ago.
        # This is done by looking at the `modified` timestamp of everything in `converted`:
        # when a `converted` record is updated, the timestamp is bumped. When something is
        # deleted from original, the corresponding `converted` record is not _actually_
        # deleted: we just set deleted=1 with a trigger and bump the timestamp.
        #
        # We also need to handle records whose status might have been affected by the
        # deletion of another record: namely, given records A and B where A is a duplicate of B
        # (B then being the "finalized" record), B is then deleted, we need to make sure A is
        # processed below as well (since A will now be the master). This is handled by
        # a trigger that, when a record is deleted, bumps the timestamp of related records
        # in converted (related = belonging to the same cluster). See storage.py.
        counter = 0
        for row in cur.execute(
            """
        SELECT
            converted.oai_id, converted.data AS converted_json, converted.source, converted.deleted, finalized.oai_id AS duplicateof, finalized.data AS finalized_json, original.data AS xml, original.source_subset, modified
        FROM
            converted
        LEFT JOIN
            original ON original.id=converted.original_id
        LEFT JOIN
            cluster ON cluster.converted_id=converted.id
        LEFT JOIN finalized ON cluster.cluster_id=finalized.cluster_id
        WHERE
            converted.modified > ?
        """,
            [modified_since],
        ):
            counter += 1
            if counter % 1000 == 0:
                mysql_con.commit()

            if row["deleted"]:
                mysql_cur.execute(
                    "UPDATE record SET deleted=1 WHERE identifier=%s", (row["oai_id"],)
                )
                mysql_cur.execute(
                    "UPDATE enriched SET deleted=1 WHERE identifier=%s", (row["oai_id"],)
                )
                continue

            identifier = row["oai_id"]
            # If the publication is a "duplicate" of itself, it means that it's the "master" publication.
            # For every publication, insert its original xml into `record`.
            # For every publication that's a "master" publication, insert its _finalized_ JSON into enriched.
            # For every publication that's a duplicate, insert its _converted_ JSON into enriched.
            duplicateof = None
            if row["duplicateof"] != identifier:
                duplicateof = row["duplicateof"]

            if duplicateof:
                json_data = row["converted_json"]
                body = orjson.loads(row["converted_json"])
            else:
                json_data = row["finalized_json"]
                body = orjson.loads(row["finalized_json"])

            publication_body = Publication(body).body_with_required_legacy_search_fields
            # TODO: Don't store the following in the actual document?
            publication_body.pop("_publication_ids", None)
            publication_body.pop("_publication_orgs", None)
            updated_json = json.dumps(publication_body, ensure_ascii=False)

            xml_data = row["xml"]

            origin = row["source_subset"]  # SwePub-ths
            target = "SWEPUB"
            format = "swepub_mods"
            sets = _sets(xml_data)
            timestamp = datetime.fromtimestamp(row["modified"]).isoformat()
            remote_timestamp = _remote_timestamp(xml_data)
            deleted = row["deleted"]

            mysql_cur.execute(
                """
                INSERT INTO
                    record(identifier, origin, target, format, data, sets, timestamp, remote_timestamp, deleted)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    origin=%s, data=%s, sets=%s, timestamp=%s, remote_timestamp=%s, deleted=%s
                """,
                (
                    identifier,
                    origin,
                    target,
                    format,
                    xml_data,
                    sets,
                    timestamp,
                    remote_timestamp,
                    deleted,
                    origin,
                    xml_data,
                    sets,
                    timestamp,
                    remote_timestamp,
                    deleted,
                ),
            )

            mysql_cur.execute(
                """
                INSERT INTO
                    enriched(identifier, origin, target, format, data, sets, timestamp, remote_timestamp, deleted, duplicateof)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    origin=%s, data=%s, sets=%s, timestamp=%s, remote_timestamp=%s, deleted=%s, duplicateof=%s
                """,
                (
                    identifier,
                    origin,
                    target,
                    format,
                    updated_json,
                    sets,
                    timestamp,
                    remote_timestamp,
                    deleted,
                    duplicateof,
                    origin,
                    updated_json,
                    sets,
                    timestamp,
                    remote_timestamp,
                    deleted,
                    duplicateof,
                ),
            )
        mysql_con.commit()


# For debugging
if __name__ == "__main__":
    legacy_sync()
