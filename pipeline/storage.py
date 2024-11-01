import sqlite3
import os
import time
from enum import Enum

import orjson as json

from pipeline.bibframesource import BibframeSource
from pipeline.swepublog import logger as log

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
SQL_SCHEMA_FILE = os.path.join(FILE_PATH, "../resources/schema.sql")


def _set_pragmas(cursor):
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=OFF")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA cache_size=-64000")  # negative number = kibibytes
    cursor.execute("PRAGMA temp_store=MEMORY")


def get_sqlite_path():
    return os.getenv(
        "SWEPUB_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../swepub.sqlite3")
    )


def storage_exists():
    return os.path.exists(get_sqlite_path())


def clean_and_init_storage():
    sqlite_path = get_sqlite_path()

    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    if os.path.exists(f"{sqlite_path}-wal"):
        os.remove(f"{sqlite_path}-wal")
    if os.path.exists(f"{sqlite_path}-shm"):
        os.remove(f"{sqlite_path}-shm")
    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()
    _set_pragmas(cur)

    with open(SQL_SCHEMA_FILE, "r") as sql_schema_file:
        sql_script = sql_schema_file.read()
    cur.executescript(sql_script)

    con.commit()


def store_original(
    oai_id,
    deleted,
    original,
    source,
    source_subset,
    accepted,
    connection,
    incremental,
    min_level_errors,
    harvest_id,
):
    cur = connection.cursor()
    deleted_from_db = False
    if incremental:
        # For bookkeeping purposes
        if deleted:
            for row in cur.execute("SELECT id FROM original WHERE oai_id = ?", (oai_id,)):
                deleted_from_db = True
                break

        cur.execute(
            "DELETE FROM original WHERE oai_id = ?",
            (oai_id,),
        )
    else:
        # If we're doing a full harvest from scratch, we still need to store the fact
        # that a certain record was marked as deleted, otherwise it can happen - during
        # certain circumstances - that the legacy search db never learns about the deletion.
        if deleted:
            cur.execute(
                """
            INSERT INTO
                converted(oai_id, data, deleted)
            VALUES
                (?, null, 1)
            ON CONFLICT(oai_id) DO UPDATE SET
                oai_id = excluded.oai_id, data = null, deleted = 1, modified = ?
            """,
                (oai_id, int(time.time()),)
            )

    if deleted:
        connection.commit()
        return None, deleted_from_db

    if not accepted:
        cur.execute(
            "INSERT INTO rejected(harvest_id, oai_id, rejection_cause) VALUES(?, ?, ?)",
            (harvest_id, oai_id, json.dumps(min_level_errors)),
        )

    # It *shouldn't* happen that an OAI ID occurs twice in the same dataset, but it can happen...
    original_rowid = cur.execute(
        """
    INSERT INTO
        original(source, source_subset, data, accepted, oai_id)
    VALUES
        (?, ?, ?, ?, ?)
    ON CONFLICT(oai_id) DO NOTHING
    """,
        (source, source_subset, original, accepted, oai_id),
    ).lastrowid

    # ...and in the rare case that it does happen, we skip this record
    if not original_rowid:
        connection.commit()
        return None, False

    connection.commit()
    return original_rowid, deleted_from_db


def serialize(obj):
    if isinstance(obj, Enum):
        return str(obj)
    return obj.__dict__


def store_converted(original_rowid, converted, audit_events, field_events, record_info, connection, clear_record_info=False, original_converted_id=None):
    try:
        cur = connection.cursor()
        # If a we're reprocessing a record, clear its converted_record_info data, otherwise that data
        # will be duplicated and the processing stats will be wrong
        if clear_record_info and original_converted_id:
            cur.execute("DELETE FROM converted_record_info WHERE converted_id = ?", [original_converted_id])

        doc = BibframeSource(converted)
        converted_events = {"audit_events": audit_events, "field_events": field_events}

        cur.execute(
            """
        INSERT INTO
            converted(data, original_id, oai_id, date, source, is_open_access, has_ssif_1, classification_level, events)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(oai_id) DO UPDATE SET
            data = excluded.data, original_id = excluded.original_id, oai_id = excluded.oai_id, date = excluded.date, source = excluded.source, is_open_access = excluded.is_open_access, has_ssif_1 = excluded.has_ssif_1, classification_level = excluded.classification_level, events = excluded.events, deleted = 0, should_be_reprocessed = 0
        """,
            (
                json.dumps(converted),
                original_rowid,
                doc.record_id,
                doc.publication_just_the_year,
                doc.source_org_master,
                doc.open_access,
                (len(doc.ssif_1_codes) > 0),
                doc.level,
                json.dumps(converted_events, default=serialize) #default=lambda o: o.__dict__),
            ),
        )

        # This is necessary because of .lastrowid weirdness on conflict
        converted_rowid = cur.execute(
            "SELECT id FROM converted WHERE oai_id = ?", [doc.record_id]
        ).fetchone()[0]

        for ssif_1 in doc.ssif_1_codes:
            cur.execute(
                """
            INSERT INTO converted_ssif_1(converted_id, value) VALUES(?, ?)
            """,
                (converted_rowid, ssif_1,)
            )

        for field, value in record_info.items():
            cur.execute(
                """
            INSERT INTO converted_record_info(
                converted_id, source, date, field_name, validation_status, enrichment_status, normalization_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    converted_rowid,
                    doc.source_org_master,
                    doc.publication_just_the_year,
                    field,
                    int(value["validation_status"]),
                    int(value["enrichment_status"]),
                    int(value["normalization_status"]),
                ),
            )

        for name, events in audit_events.items():
            for event in events:
                cur.execute(
                    """
                INSERT INTO converted_record_info(converted_id, source, date, audit_code, audit_result, audit_name) VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        converted_rowid,
                        doc.source_org_master,
                        doc.publication_just_the_year,
                        event.get("code", None),
                        event.get("result", None),
                        name
                    ),
                )

        identifiers = []

        # To loosely/speculatively "search" for simliar (but possibly misspelled) summaries/titles,
        # add the vowels of the last N chars of the summary as a clustering identifier
        vowels = "AaEeIiOoUuYyÅåÄäÖö"

        for title in converted["instanceOf"]["hasTitle"]:
            combined_title = title.get("mainTitle")
            sub_title = title.get("subtitle")
            if sub_title is not None and isinstance(sub_title, str) and isinstance(combined_title, str):
                combined_title += sub_title
            if combined_title is not None and isinstance(combined_title, str):
                ending = combined_title[-60:]
                degraded = "".join([c for c in ending if c in vowels]).lower()
                identifiers.append(degraded)

        for id_object in converted["identifiedBy"]:
            if id_object["@type"] != "Local":
                identifier = id_object["value"]
                if identifier is not None and isinstance(identifier, str):
                    identifiers.append(identifier)

        work = converted["instanceOf"]
        if "summary" in work:
            for summary in work["summary"]:
                ending = summary["label"][-60:]
                degraded = "".join([c for c in ending if c in vowels]).lower()
                identifiers.append(degraded)

        for identifier in identifiers:
            if len(identifier) > 4:
                cur.execute(
                    """
                INSERT INTO clusteringidentifiers(identifier, converted_id) VALUES (?, ?)
                """,
                    (identifier, converted_rowid),
                )

        connection.commit()
        return converted_rowid
    except Exception as e:
        log.warning(f"Failed saving converted record for original_rowid {original_rowid} ({doc.record_id})")
        raise e


def get_connection():
    connection = sqlite3.connect(get_sqlite_path())
    cursor = connection.cursor()
    _set_pragmas(cursor)
    return connection


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def checkpoint():
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
