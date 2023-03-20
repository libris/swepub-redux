import time

from os import environ, path
import json
from datetime import datetime
import dateutil.parser
import sys
import traceback

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
#
# CREATE TABLE `server` (
#   `server_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
#   `name` varchar(128) NOT NULL,
#   `base_url` varchar(256) NOT NULL,
#   `origin` varchar(32) NOT NULL,
#   `admin_email` varchar(256) NOT NULL,
#   `datetimeformat` varchar(32) NOT NULL DEFAULT 'YYYY-MM-DD',
#   `selective_harvesting` tinyint(1) NOT NULL DEFAULT '0',
#   PRIMARY KEY (`server_id`),
#   UNIQUE KEY `origin` (`origin`) USING BTREE
# ) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8mb4

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


def _mods(xml):
    try:
        root = ET.fromstring(xml)
        mods = root.find('.//{http://www.loc.gov/mods/v3}mods')
        return ET.tostring(mods).decode('UTF-8')
    except Exception:
        return ""


def _update_records(hours=24):
    with get_connection() as con, _get_mysql_connection() as mysql_con:
        cur = con.cursor()
        cur.row_factory = dict_factory
        mysql_cur = mysql_con.cursor(prepared=True)

        # Process records modified < `hours` ago. -1 = all records.
        if hours == -1:
            modified_since = 0
            log.info("Syncing all records")
        else:
            modified_since = int(time.time()) - 60 * 60 * hours
            log.info(f"Syncing records modified < {hours} hours ago")

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
            if counter % 20000 == 0:
                log.info(f"Processed {counter} records")

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

            origin = f"{row['source'].upper()}_SWEPUB"
            target = "SWEPUB"
            mods = _mods(xml_data)
            sets = _sets(xml_data)
            timestamp = datetime.fromtimestamp(row["modified"]).isoformat()
            remote_timestamp = dateutil.parser.isoparse(_remote_timestamp(xml_data))
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
                    "swepub_mods",
                    mods,
                    sets,
                    timestamp,
                    remote_timestamp,
                    deleted,
                    origin,
                    mods,
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
                    "swepub_json",
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
        log.info(f"Inserted/updated {counter} records")


def _update_server_info():
    source_file = environ.get("SWEPUB_SOURCE_FILE", path.join(path.dirname(path.abspath(__file__)), "../resources/sources.json"))
    sources = json.load(open(source_file))

    log.info("Updating server metadata")
    with get_connection() as con, _get_mysql_connection() as mysql_con:
        cur = con.cursor()
        cur.row_factory = dict_factory
        mysql_cur = mysql_con.cursor(prepared=True)

        for source in sources.values():
            name = f"{source['name']} - Swepub"
            base_url = source["sets"][0]["url"]
            origin = f"{source['code'].upper()}_SWEPUB"

            try:
                mysql_cur.execute(
                    """
                    INSERT INTO
                        server(name, base_url, origin, admin_email)
                    VALUES
                        (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        name=%s, base_url=%s, origin=%s, admin_email=%s
                """,
                (
                    name,
                    base_url,
                    origin,
                    "",
                    name,
                    base_url,
                    origin,
                    "",
                    ),
                )
            except Exception as e:
                log.warning(f"Failed updating legacy server info: {e}")
                log.warning(traceback.format_exc())
        mysql_con.commit()
    log.info("Finished updating server metadata")


def legacy_sync(hours=24):
    _update_records(hours)
    _update_server_info()


# For debugging
if __name__ == "__main__":
    if len(sys.argv) == 2:
        try:
            legacy_sync(int(sys.argv[1]))
        except ValueError:
            log.error("Please specify an integer (number of hours, or -1 for all records)")
            sys.exit(1)
    else:
        legacy_sync()
