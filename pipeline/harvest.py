from autoclassify import auto_classify
from merge import merge
from convert import convert
from deduplicate import deduplicate
from storage import *
from index import generate_search_tables
from stats import generate_processing_stats
from oai import *
from validate import validate, should_be_rejected
from audit import audit
import swepublog

import re
import time
from multiprocessing import Process, Lock, Value, Manager
import sys
from datetime import datetime, timezone
import uuid


ID_CACHE_PATH = "./id_cache.json"
KNOWN_ISSN_PATH = "./known_valid_issn.txt"
KNOWN_DOI_PATH = "./known_valid_doi.txt"


def harvest(source, lock, harvested_count, harvest_cache, incremental, added_converted_rowids):
    fromtime = None
    if incremental:
        lock.acquire()
        try:
            with get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("""
                SELECT strftime('%Y-%m-%dT%H:%M:%SZ', last_successful_harvest) from last_harvest WHERE source = ?""",
                (source["code"],))
                rows = cursor.fetchall()
                if rows:
                    fromtime = rows[0][0]
        finally:
            lock.release()

    start_time = time.time()
    harvest_id = str(uuid.uuid4())
    harvest_cache['meta'][harvest_id] = [0, 0]

    with get_connection() as connection:
        cursor = connection.cursor()
        lock.acquire()
        try:
            cursor.execute("""
            INSERT INTO harvest_history(id, source, harvest_start) VALUES (?, ?, ?)
            """, (harvest_id, source["code"], datetime.now(timezone.utc).isoformat()))
            connection.commit()
        finally:
            lock.release()

    for set in source["sets"]:
        harvest_info = f'{set["url"]} ({set["subset"]}, {set["metadata_prefix"]})'
        harvest_start = datetime.now(timezone.utc)

        #fromtime = "2020-05-05T00:00:00Z" # Only while debugging, use to force FROM date to get some incremental test data.
        record_iterator = RecordIterator(source["code"], set, fromtime, None)
        try:
            batch_count = 0
            batch = []
            processes = []
            record_count_since_report = 0
            t0 = time.time()
            
            for record in record_iterator:
                if record.is_successful():
                    batch.append(record)
                    record_count_since_report += 1
                    # if record_count_since_report == 200:
                    #     record_count_since_report = 0
                    #     diff = time.time() - start_time
                    #     harvested_count.value += 200
                    #     print(f"{harvested_count.value/diff} per sec, running average, {harvested_count.value} done in total.")
                    if (len(batch) >= 128):
                        while (len(processes) >= 4):
                            time.sleep(0)
                            n = len(processes)
                            i = n-1
                            while i > -1:
                                if not processes[i].is_alive():
                                    processes[i].join()
                                    del processes[i]
                                i -= 1
                        p = Process(target=threaded_handle_harvested, args=(batch, source["code"], lock, harvest_cache, incremental, added_converted_rowids, harvest_id))
                        batch_count += 1
                        p.start()
                        processes.append( p )
                        batch = []
            p = Process(target=threaded_handle_harvested, args=(batch, source["code"], lock, harvest_cache, incremental, added_converted_rowids, harvest_id))
            p.start()
            processes.append( p )
            for p in processes:
                p.join()
            finish_time = time.time()
            log.info(f'Harvest of {source["code"]} took {finish_time-start_time} seconds.')


            with get_connection() as connection:
                cursor = connection.cursor()
                lock.acquire()
                try:
                    cursor.execute("""
                    INSERT INTO last_harvest(source, last_successful_harvest) VALUES (?, ?)
                    ON CONFLICT(source) DO UPDATE SET last_successful_harvest = ?;""", (source["code"], harvest_start, harvest_start))
                    connection.commit()
                finally:
                    lock.release()
            #print(f"harvested: {record_count_since_report}")

            # If we're doing incremental updating: Check if the source uses <deletedRecord>persistent</deletedRecord>.
            # If it does not, we need to "ListIdentifiers" all of their records to figure out if any were deleted.
            if incremental:
                if not _get_has_persistent_deletes(set):
                    all_source_ids = _get_source_ids(set)
                    obsolete_ids = []
                    with get_connection() as connection:
                        cursor = connection.cursor()
                        for original_id_row in cursor.execute("""
                        SELECT
                            oai_id
                        FROM
                            original
                        WHERE
                            source = ?;
                        """, (source["code"],)):
                            existing_oai_id = original_id_row[0]
                            if existing_oai_id not in all_source_ids:
                                obsolete_ids.append(existing_oai_id)

                        cursor.execute(f"""
                        DELETE FROM
                            original
                        WHERE oai_id IN ({','.join('?'*len(obsolete_ids))});
                        """, (obsolete_ids,))
                        log.info(f"Deleted {len(obsolete_ids)} obsolete records from {source['code']}, after checking their ID-list.")

        except HarvestFailed as e:
            log.warning(f'FAILED HARVEST: {source["code"]}. Error: {e}')
            continue
    num_accepted, num_rejected = harvest_cache['meta'][harvest_id]
    with get_connection() as connection:
        cursor = connection.cursor()
        lock.acquire()
        try:
            cursor.execute("""
            UPDATE
                harvest_history
            SET
                harvest_completed = ?, successes = ?, rejected = ?
            WHERE
                id = ?""",
            (datetime.now(timezone.utc).isoformat(), num_accepted, num_rejected, harvest_id))
            connection.commit()
        finally:
            lock.release()


def threaded_handle_harvested(batch, source, lock, harvest_cache, incremental, added_converted_rowids, harvest_id):
    converted_rowids = []
    num_accepted = 0
    num_rejected = 0
    for record in batch:
        xml = record.xml
        rejected, min_level_errors = should_be_rejected(xml)
        accepted = not rejected

        if accepted:
            num_accepted += 1
            converted = convert(xml)
            (field_events, record_info) = validate(converted, harvest_cache)
            (audited, audit_events) = audit(converted)
        elif not record.deleted:
            num_rejected += 1

        lock.acquire()
        try:
            with get_connection() as connection:
                original_rowid = store_original(record.oai_id, record.deleted, xml, source, accepted, connection, incremental, min_level_errors, harvest_id)
                if accepted:
                    converted_rowid = store_converted(original_rowid, audited.data, audit_events.data, field_events, record_info, connection)
                    converted_rowids.append(converted_rowid)
        finally:
            lock.release()

    if incremental:
        for rowid in converted_rowids:
            added_converted_rowids[rowid] = None

    harvest_cache['meta'][harvest_id] = [harvest_cache['meta'][harvest_id][0] + num_accepted, harvest_cache['meta'][harvest_id][1] + num_rejected]

def _get_source_ids(source_set):
    source_ids = set()
    sickle_client = sickle.Sickle(source_set["url"])
    list_ids_params = {
        "metadataPrefix": source_set["metadata_prefix"],
        "ignore_deleted": False,
    }
    if source_set["subset"]:
        list_ids_params["set"] = source_set["subset"]
    headers = sickle_client.ListIdentifiers(** list_ids_params)
    for header in headers:
        source_ids.add(header.identifier)
    return source_ids

def _get_has_persistent_deletes(source_set):
    sickle_client = sickle.Sickle(source_set["url"])
    identify = sickle_client.Identify()
    return identify.deletedRecord == "persistent"


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
        with open(ID_CACHE_PATH, 'r') as f:
            previously_validated_ids = json.load(f)
        log.info(f"Cache populated with {len(previously_validated_ids)} previously validated IDs from {ID_CACHE_PATH}")
    except FileNotFoundError:
        log.warning("ID cache file not found, starting fresh")
    except Exception as e:
        log.warning(f"Failed loading ID cache file, starting fresh (error: {e})")

    # If we have files with known ISSN/DOI numbers, use them to populate the cache
    known_issn = {}
    known_doi = {}
    try:
        with open(KNOWN_ISSN_PATH, 'r') as issn, open(KNOWN_DOI_PATH, 'r') as doi:
            issn_count = 0
            doi_count = 0
            for line in issn:
                known_issn[line.strip()] = 1
                issn_count += 1
            for line in doi:
                known_doi[line.strip()] = 1
                doi_count += 1
            log.info(f"Cache populated with {issn_count} ISSNs from {KNOWN_ISSN_PATH}, {doi_count} DOIs from {KNOWN_DOI_PATH}")
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

    return manager.dict({'doi_new': doi_new, 'doi_static': doi_static, 'issn_new': issn_new, 'issn_static': issn_static, 'meta': harvest_meta})

SOURCES = json.load(open(os.path.dirname(__file__) + '/sources.json'))
TABLES_DELETED_ON_INCREMENTAL_OR_PURGE = ["cluster", "finalized", "search_single", "search_doi", "search_genre_form", "search_subject", "search_creator", "search_org", "search_fulltext", "stats_field_events", "stats_audit_events"]

if __name__ == "__main__":
    # To change log level, set SWEPUB_LOG_LEVEL environment variable to DEBUG, INFO, ..
    log = swepublog.get_default_logger()
    args = sys.argv[1:]

    if "purge" in args and "update" in args:
        log.error("Can't purge and update at the same time!")
        sys.exit(1)

    purge = False
    if "purge" in args:
        args.remove("purge")
        purge = True

    incremental = False
    if "update" in args:
        args.remove("update")
        incremental = True
        log.info("Doing incremental update")

    if "devdata" in args:
        sources_to_process = [SOURCES["mdh"], SOURCES["miun"], SOURCES["mau"]]
    elif len(args) > 0:
        sources_to_process = []
        for arg in args:
            if arg not in SOURCES:
                log.error(f"Source {arg} does not exist in sources.json")
                sys.exit(1)
            sources_to_process.append(SOURCES[arg])
    else:
        sources_to_process = list(SOURCES.values())

    t1 = None
    if purge:
        log.info("Purging " + " ".join([source['code'] for source in sources_to_process]))
        with get_connection() as connection:
            cursor = connection.cursor()
            for source in sources_to_process:
                cursor.execute("DELETE FROM original WHERE source = ?", [source['code']])
                cursor.execute("DELETE FROM last_harvest WHERE source = ?", [source['code']])
            for table in TABLES_DELETED_ON_INCREMENTAL_OR_PURGE:
                cursor.execute(f"DELETE FROM {table}")
    else:
        # All harvest jobs have access to the same Manager-managed dictionaries
        manager = Manager()
        harvest_cache = _get_harvest_cache_manager(manager)
        added_converted_rowids = manager.dict()

        log.info("Harvesting " + " ".join([source['code'] for source in sources_to_process]))

        t0 = time.time()
        if incremental:
            with get_connection() as connection:
                cursor = connection.cursor()
                for table in TABLES_DELETED_ON_INCREMENTAL_OR_PURGE:
                    cursor.execute(f"DELETE FROM {table}")
        else:
            clean_and_init_storage()
        processes = []

        # Initially synchronization was left up to sqlite3's file locking to handle,
        # which was fine, except that the try/sleep is somewhat inefficient and risks
        # starving some processes for a long time.
        # Instead, using an explicit lock should instead allow the kernel to fairly
        # distribute the database between the processes.
        lock = Lock()

        harvested_count = Value("I", 0)

        for source in sources_to_process:
            p = Process(target=harvest, args=(source, lock, harvested_count, harvest_cache, incremental, added_converted_rowids))
            p.start()
            processes.append( p )
        for p in processes:
            p.join()

        t1 = time.time()
        diff = t1-t0
        log.info(f"Phase 1 (harvesting) ran for {diff} seconds")

        t0 = t1
        auto_classify(incremental, added_converted_rowids.keys())
        t1 = time.time()
        diff = t1-t0
        log.info(f"Phase 2 (auto-classification) ran for {diff} seconds")

    t0 = t1 if t1 else time.time()
    deduplicate()
    t1 = time.time()
    diff = t1-t0
    log.info(f"Phase 3 (deduplication) ran for {diff} seconds")

    t0 = t1
    merge()
    t1 = time.time()
    diff = t1-t0
    log.info(f"Phase 4 (merging) ran for {diff} seconds")

    t0 = t1
    generate_search_tables()
    t1 = time.time()
    diff = t1-t0
    log.info(f"Phase 5 (generate search tables) ran for {diff} seconds")

    t0 = t1
    generate_processing_stats()
    t1 = time.time()
    diff = t1-t0
    log.info(f"Phase 6 (generate processing stats) ran for {diff} seconds")

    if not purge:
        # Save ISSN/DOI cache for use next time
        try:
            log.info(f'Saving {len(harvest_cache["issn_new"]) + len(harvest_cache["doi_new"])} cached IDs to {ID_CACHE_PATH}')
            with open(ID_CACHE_PATH, 'w') as f:
                json.dump({"doi": dict(harvest_cache['doi_new']), "issn": dict(harvest_cache["issn_new"])}, f)
        except Exception as e:
            log.warning(f"Failed saving harvest ID cache to {ID_CACHE_PATH}: {e}")
