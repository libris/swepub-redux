#!/usr/bin/env python3
import re
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Lock, Manager
import sys
from datetime import datetime, timezone
import uuid
from functools import partial
import psutil
from json import load
from os import getenv, path, environ
from contextlib import closing
import codecs
import csv
from pathlib import Path
from argparse import ArgumentParser
import traceback

import orjson as json
import requests

from pipeline import sickle
from pipeline.merge import merge
from pipeline.convert import convert
from pipeline.deduplicate import deduplicate
from pipeline.storage import (
    clean_and_init_storage,
    store_original,
    store_converted,
    get_connection,
    storage_exists,
    get_sqlite_path, dict_factory,
)
from pipeline.index import generate_search_tables
from pipeline.stats import generate_processing_stats
from pipeline.oai import RecordIterator
from pipeline.validate import validate, should_be_rejected
from pipeline.audit import audit
from pipeline.legacy_sync import legacy_sync

# To change log level, set SWEPUB_LOG_LEVEL environment variable to DEBUG, INFO, ..
from pipeline.swepublog import logger as log
from pipeline.util import chunker, get_common_json_paths, RandomisedRetry


# TODO: Move configuration (some of which is shared with service/swepub.py) to a separate file
DEFAULT_SWEPUB_ENV = getenv("SWEPUB_ENV", "DEV")  # or QA, PROD
FILE_PATH = path.dirname(path.abspath(__file__))
DEFAULT_SWEPUB_DB = path.join(FILE_PATH, "../swepub.sqlite3")
DEFAULT_ANNIF_EN_URL = getenv("ANNIF_EN_URL", "http://127.0.0.1:8083/v1/projects/swepub-en")
DEFAULT_ANNIF_SV_URL = getenv("ANNIF_SV_URL", "http://127.0.0.1:8083/v1/projects/swepub-sv")

CACHE_DIR = path.join(FILE_PATH, "../cache/")

SWEPUB_DOAB_URL = getenv(
    "SWEPUB_DOAB_URL", "https://directory.doabooks.org/download-export?format=csv"
)
DOAB_CACHE_FILE = path.join(FILE_PATH, "../cache/doab.json")
DOAB_CACHE_TIME = 604800

ID_CACHE_FILE = path.join(FILE_PATH, "../cache/id_cache.json")
KNOWN_ISSN_FILE = path.join(FILE_PATH, "../resources/known_valid_issn.txt")
KNOWN_DOI_FILE = path.join(FILE_PATH, "../resources/known_valid_doi.txt")


DEFAULT_SWEPUB_SOURCE_FILE = path.join(FILE_PATH, "../resources/sources.json")
TABLES_DELETED_ON_INCREMENTAL_OR_PURGE = [
    "cluster",
    "finalized",
    "search_single",
    "search_doi",
    "search_genre_form",
    "search_subject",
    "search_creator",
    "search_org",
    "search_fulltext",
    "stats_field_events",
    "stats_audit_events",
    "stats_converted",
    "stats_ssif_1",
]

SWEPUB_USER_AGENT = getenv("SWEPUB_USER_AGENT", "https://github.com/libris")

cached_paths = get_common_json_paths()


# Wrap the harvest function just to easily log errors from subprocesses
def harvest_wrapper(source):
    harvest_cache["meta"]["sources_to_go"].remove(source["code"])
    harvest_cache["meta"]["sources_in_progress"].append(source["code"])
    try:
        success = harvest(source)
        if success:
            harvest_cache["meta"]["sources_in_progress"].remove(source["code"])
            harvest_cache["meta"]["sources_succeeded"].append(source["code"])
    except Exception as e:
        log.warning(f"Error harvesting {source['code']}: {e}")
        log.warning(traceback.format_exc())
        if source["code"] in harvest_cache["meta"]["sources_in_progress"]:
            harvest_cache["meta"]["sources_in_progress"].remove(source["code"])
            harvest_cache["meta"]["sources_failed"].append(source["code"])

    if harvest_cache["meta"]["sources_succeeded"]:
        log.info(f'Sources finished: {harvest_cache["meta"]["sources_succeeded"]}')
    if harvest_cache["meta"]["sources_failed"]:
        log.info(f'Sources failed: {harvest_cache["meta"]["sources_failed"]}')
    if harvest_cache["meta"]["sources_in_progress"]:
        log.info(f'Sources in progress: {harvest_cache["meta"]["sources_in_progress"]}')
    if harvest_cache["meta"]["sources_to_go"]:
        log.info(f'Sources not yet started: {harvest_cache["meta"]["sources_to_go"]}')


def harvest(source):
    log.info(f"[STARTED]\t{source['code']}")
    fromtime = None
    # If we're doing an incremental update (default), first check if we've successfully harvested the source before.
    # If we have, then we only need to fetch records created/updated/modified since that time.
    # If we haven't, it's either because we've never tried harvesting that source before, or we tried but failed. In
    # that case fromtime will be None, meaning we fetch everything.
    if incremental:
        with get_connection() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT strftime('%Y-%m-%dT%H:%M:%SZ', last_successful_harvest) from last_harvest WHERE source = ?",
                (source["code"],),
            )
            rows = cur.fetchall()
            if rows:
                fromtime = rows[0][0]

    start_time = time.time()
    harvest_id = str(uuid.uuid4())
    harvest_cache["meta"][harvest_id] = [0, 0, 0]  # for keeping track of records accepted/rejected/deleted
    harvest_succeeded = True

    with get_connection() as con:
        cur = con.cursor()
        lock.acquire()
        try:
            cur.execute(
                "INSERT INTO harvest_history(id, source, harvest_start) VALUES (?, ?, ?)",
                (harvest_id, source["code"], datetime.now(timezone.utc).isoformat()),
            )
            con.commit()
        finally:
            lock.release()

    harvest_start = datetime.now(timezone.utc)
    record_count = 0
    num_deleted_without_persistent = 0
    num_failed = 0

    for source_set in source["sets"]:
        if environ.get("SWEPUB_LOCAL_SERVER"):
            if "diva" in source_set["url"]:
                source_set["url"] = f"{environ.get('SWEPUB_LOCAL_SERVER')}/diva/{source['code']}"
            else:
                source_set["url"] = f"{environ.get('SWEPUB_LOCAL_SERVER')}/foo/{source['code']}"
        record_iterator = RecordIterator(source["code"], source_set, fromtime, None, SWEPUB_USER_AGENT)
        # For each set we put records into batches and let a number of workers handle these batches.
        try:
            with ProcessPoolExecutor(
                max_workers=4,
                initializer=init,
                initargs=(
                    lock,
                    harvest_cache,
                    added_converted_rowids,
                    log,
                    incremental,
                ),
            ) as executor:
                # fromtime = "2020-05-05T00:00:00Z"  # Only while debugging, use to force FROM date to get some incremental test data.
                batch = []
                for record in record_iterator:
                    if record.is_successful():
                        batch.append(record)
                        if len(batch) >= 128:
                            # Partial to add additional arguments to threaded_handle_harvested.
                            # Note: `batch` will appear as the _last_ argument.
                            func = partial(
                                threaded_handle_harvested,
                                source["code"],
                                source_set["subset"],
                                harvest_id,
                                cached_paths,
                            )
                            executor.submit(func, batch)
                            batch = []
                        record_count += 1
                    else:
                        num_failed += 1
                func = partial(
                    threaded_handle_harvested, source["code"], source_set["subset"], harvest_id, cached_paths
                )
                executor.submit(func, batch)
                executor.shutdown(wait=True)

            # If we're doing incremental updating: Check if the source uses <deletedRecord>persistent</deletedRecord>.
            # If it does not, we need to "ListIdentifiers" all of their records to figure out if any were deleted.
            if incremental and not _get_has_persistent_deletes(source_set):
                all_source_ids = _get_source_ids(source_set)
                obsolete_ids = []
                with get_connection() as con:
                    cur = con.cursor()
                    for original_id_row in cur.execute(
                        "SELECT oai_id FROM original WHERE source = ?", (source["code"],)
                    ):
                        existing_oai_id = original_id_row[0]
                        if existing_oai_id not in all_source_ids:
                            obsolete_ids.append(existing_oai_id)
                    if obsolete_ids:
                        lock.acquire()
                        # We can't do `WHERE oai_id IN ({','.join('?'*len(obsolete_ids))})` because len(obsolete_ids)
                        # could be > SQLITE_MAX_VARIABLE_NUMBER ("defaults to 999 for SQLite versions prior to 3.32.0
                        # (2020-05-22) or 32766 for SQLite versions after 3.32.0."). So, we do it by chunks.
                        try:
                            for group in chunker(obsolete_ids, 100):
                                # Keep track of number of actually deleted records for stat purposes
                                num_deleted_without_persistent += cur.execute(
                                    f"""
                                SELECT COUNT(*) AS total FROM original
                                WHERE oai_id IN ({','.join('?'*len(group))})
                                """,
                                    group,
                                ).fetchone()[0]

                                cur.execute(
                                    f"""
                                DELETE FROM
                                    original
                                WHERE oai_id IN ({','.join('?'*len(group))});
                                """,
                                    group,
                                )
                            log.info(
                                f"Deleted {len(obsolete_ids)} obsolete records from {source['code']}, after checking their ID list."
                            )
                            con.commit()
                        finally:
                            lock.release()
        except Exception as e:
            log.warning(f'[FAILED]\t{source["code"]}. Error: {e}')
            log.warning(traceback.format_exc())
            harvest_cache["meta"]["sources_in_progress"].remove(source["code"])
            harvest_cache["meta"]["sources_failed"].append(source["code"])
            harvest_succeeded = False

    num_accepted, num_rejected, num_deleted = harvest_cache["meta"][harvest_id]
    num_deleted += num_deleted_without_persistent
    with get_connection() as con:
        cur = con.cursor()
        lock.acquire()
        try:
            if harvest_succeeded:
                cur.execute(
                    """
                INSERT INTO last_harvest(source, last_successful_harvest) VALUES (?, ?)
                ON CONFLICT(source) DO UPDATE SET last_successful_harvest = ?;""",
                    (source["code"], harvest_start, harvest_start),
                )

            cur.execute(
                """
            UPDATE
                harvest_history
            SET
                harvest_completed = ?, successes = ?, rejected = ?, deleted = ?, failures = ?, harvest_succeeded = ?
            WHERE
                id = ?""",
                (
                    datetime.now(timezone.utc).isoformat(),
                    num_accepted,
                    num_rejected,
                    num_deleted,
                    num_failed,
                    harvest_succeeded,
                    harvest_id,
                ),
            )
            con.commit()
        finally:
            lock.release()

    finish_time = time.time()
    record_per_s = round(record_count / (finish_time - start_time), 2)
    if harvest_succeeded:
        log.info(
            f'[FINISHED]\t{source["code"]} ({round(finish_time-start_time, 2)} seconds, {record_count} records, {record_per_s} records/s)'
        )
    else:
        log.info(
            f'[ABORTED]\t{source["code"]} ({round(finish_time-start_time, 2)} seconds, {record_count} records, {record_per_s} records/s)'
        )
    return harvest_succeeded


def threaded_handle_harvested(source, source_subset, harvest_id, cached_paths, batch):
    converted_rowids = []
    num_accepted = 0
    num_rejected = 0
    num_deleted = 0

    with requests.Session() as session:
        adapter = requests.adapters.HTTPAdapter(max_retries=RandomisedRetry(total=4, backoff_factor=2))
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        with get_connection() as read_only_connection:
            read_only_cursor = read_only_connection.cursor()
            for record in batch:
                xml = record.xml
                rejected, min_level_errors = should_be_rejected(xml)
                accepted = not rejected

                try:
                    if accepted:
                        num_accepted += 1
                        converted = convert(xml)
                        (field_events, record_info) = validate(converted, harvest_cache, session, source, cached_paths, read_only_cursor)
                        (audited, audit_events) = audit(converted, harvest_cache, session)
                    elif not record.deleted:
                        num_rejected += 1
                except Exception:
                    log.warning(traceback.format_exc())
                    continue

                lock.acquire()
                try:
                    with get_connection() as connection:
                        original_rowid, deleted_from_db = store_original(
                            record.oai_id,
                            record.deleted,
                            xml,
                            source,
                            source_subset,
                            accepted,
                            connection,
                            incremental,
                            min_level_errors,
                            harvest_id,
                        )
                        if deleted_from_db:
                            num_deleted += 1
                        if accepted and original_rowid:
                            converted_rowid = store_converted(
                                original_rowid,
                                audited.body,
                                audit_events.data,
                                field_events,
                                record_info,
                                connection,
                            )
                            converted_rowids.append(converted_rowid)
                except Exception:
                    log.warning(traceback.format_exc())
                finally:
                    lock.release()

    if incremental:
        for rowid in converted_rowids:
            added_converted_rowids[rowid] = None

    harvest_cache["meta"][harvest_id] = [
        harvest_cache["meta"][harvest_id][0] + num_accepted,
        harvest_cache["meta"][harvest_id][1] + num_rejected,
        harvest_cache["meta"][harvest_id][2] + num_deleted,
    ]


def _get_source_ids(source_set):
    source_ids = set()
    sickle_client = sickle.Sickle(source_set["url"], max_retries=8, timeout=90, headers={"User-Agent": SWEPUB_USER_AGENT})
    list_ids_params = {
        "metadataPrefix": source_set["metadata_prefix"],
        "ignore_deleted": False,
    }
    if source_set["subset"]:
        list_ids_params["set"] = source_set["subset"]
    headers = sickle_client.ListIdentifiers(**list_ids_params)
    for header in headers:
        source_ids.add(header.identifier)
    return source_ids


def _get_has_persistent_deletes(source_set):
    sickle_client = sickle.Sickle(source_set["url"], max_retries=8, timeout=90, headers={"User-Agent": SWEPUB_USER_AGENT})
    identify = sickle_client.Identify()
    return identify.deletedRecord == "persistent" or identify.deletedRecord == "transient"


def _load_doab():
    doab_data = {}
    if Path(DOAB_CACHE_FILE).is_file() and (
        time.time() - path.getmtime(DOAB_CACHE_FILE) < DOAB_CACHE_TIME
    ):
        log.info(f"DOAB data still fresh enough (< {DOAB_CACHE_TIME} seconds), not refreshing")
        with open(DOAB_CACHE_FILE, "rb") as f:
            doab_data = json.loads(f.read())
    elif not environ.get("SWEPUB_SKIP_REMOTE"):
        try:
            log.info("Refreshing DOAB data")
            with closing(requests.get(SWEPUB_DOAB_URL, stream=True, timeout=30, headers={"User-Agent": SWEPUB_USER_AGENT})) as r:
                r.raise_for_status()
                reader = csv.DictReader(codecs.iterdecode(r.iter_lines(), "utf-8"), delimiter=",")
                for idx, row in enumerate(reader, 1):
                    if row["oapen.relation.isbn"]:
                        for isbn in re.split(r";|\|\|", row["oapen.relation.isbn"]):
                            if len(isbn) > 9:  # sanity check
                                cleaned_isbn = isbn.strip().replace("-", "")
                                doab_data[cleaned_isbn] = row["BITSTREAM Download URL"]
                    if row["oapen.identifier.doi"]:
                        for doi in row["oapen.identifier.doi"].split("||"):
                            if "10." in doi:
                                cleaned_doi = doi[doi.find("10.") :]
                                if "/" in cleaned_doi and len(cleaned_doi) > 5:
                                    doab_data[cleaned_doi] = row["BITSTREAM Download URL"]
            with open(DOAB_CACHE_FILE, "wb") as f:
                f.write(json.dumps(doab_data))
        except Exception as e:
            log.warning(f"Failed reading DOAB data: {e}")
            log.warning(traceback.format_exc())
    log.info(f"Finished loading DOAB data (cached to disk for {DOAB_CACHE_TIME} seconds)")
    return doab_data


def _get_harvest_cache_manager(manager):
    # We check if ISSN and DOI numbers really exist through HTTP requests to external servers,
    # so we cache the results to avoid unnecessary requests. Such requests were previously
    # cached in Redis. We don't care about the whole response, just whether the ISSN/DOI
    # was found or not, so all we need to store is the ISSN/DOI itself.
    # (This can't be a set because that's not supported by multiprocessing.Manager, and anyway
    # both set and dict lookups are O(1).)
    # After harvesting we save the cache to disk so that we can use it again next time, greatly
    # improving harvesting speed. This is all optional: harvesting will work fine even if the
    # cache file is missing/corrupt/whatever.
    previously_validated_ids = {"doi": {}, "issn": {}}
    try:
        with open(ID_CACHE_FILE, "rb") as f:
            previously_validated_ids = json.loads(f.read())
        log.info(
            f"Cache populated with {len(previously_validated_ids['doi'])+len(previously_validated_ids['issn'])} previously validated IDs from {ID_CACHE_FILE}"
        )
    except FileNotFoundError:
        log.warning("ID cache file not found, starting fresh")
    except Exception as e:
        log.warning(f"Failed loading ID cache file, starting fresh (error: {e})")

    # If we have files with known ISSN/DOI numbers, use them to populate the cache
    known_issn = {}
    known_doi = {}
    try:
        with open(KNOWN_ISSN_FILE, "r") as issn, open(KNOWN_DOI_FILE, "r") as doi:
            issn_count = 0
            doi_count = 0
            for line in issn:
                known_issn[line.strip()] = 1
                issn_count += 1
            for line in doi:
                known_doi[line.strip()] = 1
                doi_count += 1
            log.info(
                f"Cache populated with {issn_count} ISSNs from {KNOWN_ISSN_FILE}, {doi_count} DOIs from {KNOWN_DOI_FILE}"
            )
    except Exception as e:
        log.warning(f"Failed loading ISSN/DOI files: {e}")

    # Stuff seen during requests to external sources should be saved for future use,
    # but we don't want to waste time saving ISSN/DOIs already known from the 'static' files,
    # hence separating "stuff learned during harvest" from "stuff learned from static files".
    doi_not_in_static = set(previously_validated_ids["doi"].keys()) - set(known_doi.keys())
    issn_not_in_static = set(previously_validated_ids["issn"].keys()) - set(known_issn.keys())

    doi_new = manager.dict(dict.fromkeys(doi_not_in_static, 1))
    doi_static = manager.dict(known_doi)
    issn_new = manager.dict(dict.fromkeys(issn_not_in_static, 1))
    issn_static = manager.dict(known_issn)
    harvest_meta = manager.dict({})
    doab = manager.dict(_load_doab())
    localid_to_orcid = manager.dict({})
    localid_without_orcid = manager.dict({})
    enriched_from_other_record = manager.dict({})

    return manager.dict(
        {
            "doi_new": doi_new,
            "doi_static": doi_static,
            "issn_new": issn_new,
            "issn_static": issn_static,
            "meta": harvest_meta,
            "doab": doab,
            "localid_to_orcid": localid_to_orcid,
            "localid_without_orcid": localid_without_orcid,
            "enriched_from_other_record": enriched_from_other_record,
        }
    )


def _annif_health_check():
    for url in [getenv("ANNIF_EN_URL"), getenv("ANNIF_SV_URL")]:
        r = requests.get(url=url)
        data = r.json()
        assert data["is_trained"], f"Annif not trained for {url}"


def _add_localid_orcid_to_db(harvest_cache):
    with get_connection() as connection:
        cursor = connection.cursor()
        for cache_key, value in harvest_cache["localid_to_orcid"].items():
            cursor.execute("""
                INSERT INTO localid_to_orcid(source_oai_id, cache_key, orcid)
                VALUES(?, ?, ?)
                ON CONFLICT(cache_key) DO NOTHING
                """,
                (value["oai_id"], cache_key, value["orcid"]),
            )
        connection.commit()


def _calculate_oai_ids_to_reprocess():
    with get_connection() as connection:
        cursor = connection.cursor()
        # At this point all records have been processed once. Now ensure that records where
        # we can add an ORCID are marked for reprocessing.
        # - localid_without_orcid is a dict where each key is a local ID, and the value is
        #   a space-delimited list of OAI IDs where that local ID (but no ORCID) occurs.
        # - localid_to_orcid is a dict where each key is a local ID and the value is a dict
        #   containing ORCID and "source OAI ID".
        # Comparing these two we'll know which OAI IDs can be enriched with ORCID.
        oai_ids_to_reprocess = set()
        for cache_key, oai_ids in harvest_cache["localid_without_orcid"].items():
            if cache_key in harvest_cache["localid_to_orcid"]:
                oai_ids_to_reprocess.update(oai_ids.split())
        for oai_id in oai_ids_to_reprocess:
            cursor.execute("UPDATE converted SET should_be_reprocessed = 1 WHERE oai_id = ?", [oai_id])
        connection.commit()


def _add_link_between_source_and_enriched():
    # Save-to-db the fact that a certain record has been enriched with data from one or more other records,
    # so that when those "source" records are updated or deleted, the enriched record will be flagged
    # for reprocessing (through an SQL trigger).
    with get_connection() as connection:
        cursor = connection.cursor()
        for enriched_oai_id, source_oai_ids in harvest_cache["enriched_from_other_record"].items():
            for source_oai_id in source_oai_ids:
                cursor.execute("""
                INSERT INTO enriched_from_other_record(enriched_oai_id, source_oai_id)
                VALUES (?, ?)
                ON CONFLICT DO NOTHING
                """, [enriched_oai_id, source_oai_id])
        connection.commit()


def _reprocess_affected_records(sources_to_process):
    max_workers = max(psutil.cpu_count(logical=True) * 2, 8)
    with ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=init,
        initargs=(
            lock,
            harvest_cache,
            added_converted_rowids,
            log,
            incremental,
        ),
    ) as executor:
        for source in sources_to_process:
            executor.submit(_handle_reprocess_affected_records, source)
        executor.shutdown(wait=True)


def _handle_reprocess_affected_records(source):
    with get_connection() as connection, requests.Session() as session:
        cursor = connection.cursor()
        inner_cursor = connection.cursor()
        adapter = requests.adapters.HTTPAdapter(max_retries=2)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        cursor.row_factory = lambda cursor, row: row[0]
        oai_ids_to_reprocess = cursor.execute("SELECT oai_id FROM converted WHERE should_be_reprocessed = 1 AND source = ?", [source["code"]]).fetchall()
        cursor.row_factory = dict_factory

        log.info(f"Reprocessing {len(oai_ids_to_reprocess)} records for {source['code']}")
        for oai_id in oai_ids_to_reprocess:
            try:
                xml = cursor.execute("SELECT data FROM original WHERE oai_id = ?", [oai_id]).fetchone()["data"]
                original_converted = cursor.execute("SELECT original_id, source FROM converted WHERE oai_id = ?", [oai_id]).fetchone()
                converted = convert(xml)
                (field_events, record_info) = validate(converted, harvest_cache, session, original_converted["source"], cached_paths, inner_cursor)
                (audited, audit_events) = audit(converted, harvest_cache, session)

                lock.acquire()
                try:
                    with get_connection() as inner_connection:
                        store_converted(original_converted["original_id"], audited.body, audit_events.data, field_events, record_info, inner_connection)
                except Exception:
                        log.warning(traceback.format_exc())
                finally:
                    lock.release()
            except Exception:
                log.warning(traceback.format_exc())
                continue
        log.info(f"Finished reprocessing records for {source['code']}")


def init(l, c, a, lg, inc):
    global lock
    global harvest_cache
    global added_converted_rowids
    global log
    global incremental
    lock = l
    harvest_cache = c
    added_converted_rowids = a
    log = lg
    incremental = inc


def handle_args():
    parser = ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-f",
        "--force-new",
        action="store_false",
        help="Forcibly creates a new database, removing the existing one if one exists as the given path",
    )
    group.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Updates sources incrementally. Creates database and harvests from the beginning if the database doesn't already exist.",
    )
    group.add_argument(
        "--reset-harvest-time",
        action="store_true",
        help="Removes last_harvest entry for specified source(s) (or all sources), meaning next --update will trigger a full harvest.",
    )
    group.add_argument(
        "-p",
        "--purge",
        action="store_true",
        help="Delete records (from specified sources, if sources are specified, otherwise everything (but harvest history is kept)",
    )

    parser.add_argument(
        "-d",
        "--database",
        default="swepub.sqlite3",
        help="Path to sqlite3 database (to be created or updated; overrides SWEPUB_DB)",
    )
    parser.add_argument(
        "-e",
        "--env",
        default=None,
        help="One of DEV, QA, PROD (default DEV). Overrides SWEPUB_ENV.",
    )
    parser.add_argument("--skip-unpaywall", action="store_true", help="Skip Unpaywall check")
    parser.add_argument("--skip-autoclassifier", action="store_true", help="Skip autoclassify step")
    parser.add_argument("-s", "--source-file", default=None, help="Source file to use.")
    parser.add_argument(
        "source",
        nargs="*",
        default="",
        help="Source(s) to process (if not specified, everything in sources.json will be processed, e.g. uniarts ths mdh",
    )
    parser.add_argument(
        "--local-server",
        nargs="?",
        default=None,
        const="http://localhost:8383/oai",
        help="Replace source URLs with ones pointing to local OAI-PMH test server (see misc/oai_pmh_server.py), e.g. http://localhost:8383/oai"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = handle_args()

    # Make sure cache directory exists
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

    if args.database:
        environ["SWEPUB_DB"] = args.database
    elif not getenv("SWEPUB_DB", None):
        environ["SWEPUB_DB"] = DEFAULT_SWEPUB_DB

    if args.env:
        environ["SWEPUB_ENV"] = args.env
    elif not getenv("SWEPUB_ENV", None):
        environ["SWEPUB_ENV"] = DEFAULT_SWEPUB_ENV

    if args.source_file:
        environ["SWEPUB_SOURCE_FILE"] = args.source_file
    elif not getenv("SWEPUB_SOURCE_FILE", None):
        environ["SWEPUB_SOURCE_FILE"] = DEFAULT_SWEPUB_SOURCE_FILE

    log.info(f"SWEPUB_ENV is {environ['SWEPUB_ENV']}")

    if environ.get("SWEPUB_SKIP_REMOTE"):
        log.info(f"SWEPUB_SKIP_REMOTE set, not refreshing DOAB or using remote services for validation/enrichment")

    if not getenv("ANNIF_EN_URL"):
        environ["ANNIF_EN_URL"] = DEFAULT_ANNIF_EN_URL
    if not getenv("ANNIF_SV_URL"):
        environ["ANNIF_SV_URL"] = DEFAULT_ANNIF_SV_URL

    sources = load(open(environ["SWEPUB_SOURCE_FILE"]))

    # The Unpaywall mirror is not accessible from the public Internet, so for local testing one might want to avoid it
    if args.skip_unpaywall:
        environ["SWEPUB_SKIP_UNPAYWALL"] = "1"

    if args.skip_autoclassifier:
        environ["SWEPUB_SKIP_AUTOCLASSIFIER"] = "1"

    if args.local_server:
        environ["SWEPUB_LOCAL_SERVER"] = args.local_server

    # Annif health check
    if getenv("SWEPUB_SKIP_AUTOCLASSIFIER"):
        log.warning("Autoclassifier manually disabled")
    else:
        try:
            _annif_health_check()
            log.info("Annif is available")
        except Exception as e:
            if environ["SWEPUB_ENV"] in ["QA", "PROD"]:
                log.error(f"Annif misconfigured or not available: {e}")
                sys.exit(1)
            else:
                log.warning(f"Annif misconfigured or not available. Disabling autoclassifier: {e}")
                environ["SWEPUB_SKIP_AUTOCLASSIFIER"] = "1"

    incremental = False
    if args.update:
        incremental = True
        log.info("Doing incremental update")
        if not storage_exists():
            log.info(f"Database {get_sqlite_path()} doesn't exist; creating it")
            clean_and_init_storage()

    sources_to_process = []
    if args.source:
        for code in args.source:
            if code not in sources:
                log.error(f"Source {code} does not exist in {environ['SWEPUB_SOURCE_FILE']}")
                sys.exit(1)
            # Some sources should have different URIs/settings for different environments
            sources[code]["sets"][:] = [
                item
                for item in sources[code]["sets"]
                if getenv("SWEPUB_ENV") in item.get("envs", []) or "envs" not in item
            ]
            sources_to_process.append(sources[code])
    else:
        for source in sources.values():
            source["sets"][:] = [
                item
                for item in source["sets"]
                if getenv("SWEPUB_ENV") in item.get("envs", []) or "envs" not in item
            ]
            sources_to_process.append(source)

    harvest_cache = None
    t1 = None
    # If we're purging we skip the harvesting phase but do the rest.
    if args.purge:
        log.info("Purging " + " ".join([source["code"] for source in sources_to_process]))
        with get_connection() as connection:
            cursor = connection.cursor()
            for source in sources_to_process:
                cursor.execute("DELETE FROM original WHERE source = ?", [source["code"]])
                cursor.execute("DELETE FROM last_harvest WHERE source = ?", [source["code"]])
            for table in TABLES_DELETED_ON_INCREMENTAL_OR_PURGE:
                cursor.execute(f"DELETE FROM {table}")
    elif args.reset_harvest_time:
        log.info("Removing last_harvest time for " + " ".join([source["code"] for source in sources_to_process]))
        with get_connection() as connection:
            cursor = connection.cursor()
            for source in sources_to_process:
                cursor.execute("DELETE FROM last_harvest WHERE source = ?", [source["code"]])
        sys.exit(0)
    else:
        # All harvest jobs have access to the same Manager-managed dictionaries
        manager = Manager()
        harvest_cache = _get_harvest_cache_manager(manager)
        harvest_cache["meta"]["sources_to_go"] = manager.list(
            [source["code"] for source in sources_to_process]
        )
        harvest_cache["meta"]["sources_in_progress"] = manager.list()
        harvest_cache["meta"]["sources_succeeded"] = manager.list()
        harvest_cache["meta"]["sources_failed"] = manager.list()
        added_converted_rowids = manager.dict()

        log.info("Harvesting " + " ".join([source["code"] for source in sources_to_process]))

        t0 = time.time()
        if incremental:
            with get_connection() as connection:
                cursor = connection.cursor()
                for table in TABLES_DELETED_ON_INCREMENTAL_OR_PURGE:
                    cursor.execute(f"DELETE FROM {table}")
        else:
            clean_and_init_storage()

        # Initially synchronization was left up to sqlite3's file locking to handle,
        # which was fine, except that the try/sleep is somewhat inefficient and risks
        # starving some processes for a long time.
        # Instead, using an explicit lock should instead allow the kernel to fairly
        # distribute the database between the processes.
        lock = Lock()

        # We want a lot of parallelism. The point of this is not only to saturate _our_ cores
        # which may well be "overloaded" during parts of the process, but also to keep as many
        # as possible of the sources working all at once feeding us data. Ideally we want our
        # network buffers full at all times, with data ready to consume for any core available.
        # Having many processes going at once is not a liability in terms of overhead.
        # Context switching is a cost paid per core, not per thread/process.
        max_workers = max(psutil.cpu_count(logical=True) * 2, 8)
        with ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=init,
            initargs=(
                lock,
                harvest_cache,
                added_converted_rowids,
                log,
                incremental,
            ),
        ) as executor:
            for source in sources_to_process:
                executor.submit(harvest_wrapper, source)
            executor.shutdown(wait=True)

        t1 = time.time()
        diff = round(t1 - t0, 2)
        log.info(f"Phase 1 (harvesting) ran for {diff} seconds")

        t0 = t1
        _add_localid_orcid_to_db(harvest_cache)
        _calculate_oai_ids_to_reprocess()
        _reprocess_affected_records(sources_to_process)
        _add_link_between_source_and_enriched()
        t1 = time.time()
        diff = round(t1 - t0, 2)
        log.info(f"Phase 2 (reprocessing affected records) ran for {diff} seconds")

    t0 = t1 if t1 else time.time()
    deduplicate()
    t1 = time.time()
    diff = round(t1 - t0, 2)
    log.info(f"Phase 3 (deduplication) ran for {diff} seconds")

    t0 = t1
    merge()
    t1 = time.time()
    diff = round(t1 - t0, 2)
    log.info(f"Phase 4 (merging) ran for {diff} seconds")

    t0 = t1
    generate_search_tables()
    t1 = time.time()
    diff = round(t1 - t0, 2)
    log.info(f"Phase 5 (generate search tables) ran for {diff} seconds")

    t0 = t1
    generate_processing_stats()
    t1 = time.time()
    diff = round(t1 - t0, 2)
    log.info(f"Phase 6 (generate processing stats) ran for {diff} seconds")

    if harvest_cache and not args.purge:
        log.info(f'Sources harvested: {" ".join(harvest_cache["meta"]["sources_succeeded"])}')
        if harvest_cache["meta"]["sources_failed"]:
            log.warning(f'Sources failed: {" ".join(harvest_cache["meta"]["sources_failed"])}')
        # Save ISSN/DOI cache for use next time
        try:
            log.info(
                f'Saving {len(harvest_cache["issn_new"]) + len(harvest_cache["doi_new"])} cached IDs to {ID_CACHE_FILE}'
            )
            with open(ID_CACHE_FILE, "wb") as f:
                f.write(
                    json.dumps(
                        {
                            "doi": dict(harvest_cache["doi_new"]),
                            "issn": dict(harvest_cache["issn_new"]),
                        }
                    )
                )
        except Exception as e:
            log.warning(f"Failed saving harvest ID cache to {ID_CACHE_FILE}: {e}")

    if environ.get("SWEPUB_LEGACY_SEARCH_DATABASE"):
        t0 = t1
        legacy_sync()
        t1 = time.time()
        diff = round(t1 - t0, 2)
        log.info(f"Phase 7 (legacy search sync) ran for {diff} seconds")
