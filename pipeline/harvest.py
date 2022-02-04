from pathlib import Path
from autoclassify import auto_classify
from merge import merge
import re
import sickle
from modsstylesheet import ModsStylesheet
import hashlib
import requests
from uuid import uuid1
from convert import convert
from deduplicate import deduplicate
import time
from multiprocessing import Process, Lock, Value, Manager
import sys
from storage import *
from index import generate_search_tables
import logging
import swepublog
from datetime import datetime, timezone

from sickle.oaiexceptions import (
    BadArgument, BadVerb, BadResumptionToken,
    CannotDisseminateFormat, IdDoesNotExist, NoSetHierarchy,
    NoMetadataFormat, NoRecordsMatch, OAIError
)
from modsstylesheet import ModsStylesheet
from validate import validate
from audit import audit

OAIExceptions = (
    BadArgument, BadVerb, BadResumptionToken,
    CannotDisseminateFormat, IdDoesNotExist, NoSetHierarchy,
    NoMetadataFormat, OAIError
)

RequestExceptions = (
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.HTTPError
)

ID_CACHE_PATH = "./id_cache.json"
ISSN_PATH = "./issn.txt"  # one ISSN per line

class RecordIterator:

    def __init__(self, code, source_set, harvest_from, harvest_to):
        self.set = source_set
        self.stylesheet = ModsStylesheet(code, self.set["url"])
        self.records = None
        self.publication_ids = set()
        self.harvest_from = harvest_from
        self.harvest_to = harvest_to

    def __iter__(self):
        return self

    def __next__(self):
        try:
            if not self._has_records():
                self._get_records()
            return self._get_next_record()
        except NoRecordsMatch:
            #logger.info("OAI-PMH query returned no matches.")
            raise StopIteration
        except OAIExceptions + RequestExceptions + (AttributeError,) as e:
            #logger.exception(e, extra={
            #    'metadata_prefix': self.set.metadata_prefix,
            #    'subset': self.set.subset,
            #})
            if isinstance(e, AttributeError):
                return Record()
            else:
                raise HarvestFailed(str(e))

    def _has_records(self):
        return self.records is not None

    def _get_records(self):
        sickle_client = sickle.Sickle(self.set["url"])
        list_record_params = {
            "metadataPrefix": self.set["metadata_prefix"],
            "ignore_deleted": False
        }
        if self.set["subset"]:
            list_record_params["set"] = self.set["subset"]
        if self.harvest_from:
            list_record_params["from"] = self.harvest_from
        if self.harvest_to:
            list_record_params["until"] = self.harvest_to
        self.records = sickle_client.ListRecords(**list_record_params)

    def _get_next_record(self):
        transformed_record = self.stylesheet.apply(next(self.records).raw)
        return Record(transformed_record)


class Record:

    def __init__(self, xml=''):
        self.xml = xml
        self.harvest_item_id = str(uuid1())
        self.hash = self._get_hash()

    def is_successful(self):
        return bool(self.xml)

    def _get_hash(self):
        return str(hashlib.md5(self.xml.encode()).hexdigest())


class Source:

    def __init__(self, source_dict):
        self.sets = [Set(**s) for s in source_dict['sets']]
        self.forced = source_dict['forced']
        self.code = source_dict['code']
        self.harvest_from = source_dict['harvest_from']
        self.harvest_to = source_dict['harvest_to']

    @property
    def dict(self):
        return {
            "sets": [s.dict for s in self.sets],
            "forced": self.forced,
            "code": self.code,
            "harvest_from": self.harvest_from,
            "harvest_to": self.harvest_to
        }


class Set:
    def __init__(self, *, url=None, metadata_prefix=None, subset=None):
        self.url = url
        self.metadata_prefix = metadata_prefix
        self.subset = subset

    @property
    def dict(self):
        return {
            "url": self.url,
            "metadata_prefix": self.metadata_prefix,
            "subset": self.subset
        }


class HarvestFailed(Exception):
    pass



def harvest(source, lock, harvested_count, harvest_cache, incremental):

    
    fromtime = None
    if incremental:
        lock.acquire()
        try:
            #cursor = get_cursor()
            #cursor.execute("SELECT last_successful_harvest from last_harvest WHERE source = ?", (source["code"],))
            #rows = cursor.fetchall()
            #print(f"** rows0:{rows[0][0]}, type: {type(rows[0][0])}")
            #fromtime = rows[0][0]
            #
            #
            #
            #HMM
            fromtime = "2022-05-05T00:00:00Z"
        finally:
            lock.release()

    start_time = time.time()

    for set in source["sets"]:
        harvest_info = f'{set["url"]} ({set["subset"]}, {set["metadata_prefix"]})'
        harvest_start = datetime.now(timezone.utc)

        record_iterator = RecordIterator(source["code"], set, fromtime, None)
        try:
            batch_count = 0
            batch = []
            processes = []
            record_count_since_report = 0
            t0 = time.time()
            
            for record in record_iterator:
                if record.is_successful():
                    batch.append(record.xml)
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
                        p = Process(target=threaded_handle_harvested, args=(batch, source["code"], lock, harvest_cache))
                        batch_count += 1
                        p.start()
                        processes.append( p )
                        batch = []
            p = Process(target=threaded_handle_harvested, args=(batch, source["code"], lock, harvest_cache))
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
                    ON CONFLICT DO UPDATE SET last_successful_harvest = ?;""", (source["code"], harvest_start, harvest_start))
                    connection.commit()
                finally:
                    lock.release()
            print(f"harvested: {record_count_since_report}")


        except HarvestFailed as e:
            log.warn(f'FAILED HARVEST: {source["code"]}')
            continue

def threaded_handle_harvested(batch, source, lock, harvest_cache):
    for xml in batch:
        converted = convert(xml)
        (accepted, events) = validate(xml, converted, harvest_cache)
        (audited, audit_events) = audit(converted)
        events.extend(audit_events.data)
        lock.acquire()
        try:
            with get_connection() as connection:
                store_original_and_converted(xml, audited.data, source, accepted, events, connection)
        finally:
            lock.release()


sources = json.load(open(os.path.dirname(__file__) + '/sources.json'))

if __name__ == "__main__":
    # To change log level, set SWEPUB_LOG_LEVEL environment variable to DEBUG, INFO, ..
    log = swepublog.get_default_logger()
    args = sys.argv[1:]

    incremental = False
    if "update" in args:
        args.remove("update")
        incremental = True

    if "devdata" in args:
        sources_to_harvest = [sources["mdh"], sources["miun"], sources["mau"]]
    elif len(args) > 0:
        sources_to_harvest = []
        for arg in args:
            if arg not in sources:
                log.error(f"Source {arg} does not exist in sources.json")
                sys.exit(1)
            sources_to_harvest.append(sources[arg])
    else:
        sources_to_harvest = list(sources.values())

    # We check if ISSN and DOI numbers really exist through HTTP requests to external servers,
    # so we cache the results to avoid unnecessary requests. Such requests were previously
    # cached in Redis. We don't care about the whole response, just whether the ISSN/DOI
    # was found or not, so all we need to store is the ISSN/DOI itself.
    # (This can't be a set because that's not supported by multiprocessing.Manager, and anyway
    # both set and dict lookups are O(1).)
    # After harvesting we save the cache to disk so that we can use it again next time, greatly
    # improving harvesting speed. This is all optional: harvesting will work fine even if the
    # cache file is missing/corrupt/whatever.
    previously_validated_ids = {}
    try:
        with open(ID_CACHE_PATH, 'r') as f:
            previously_validated_ids = json.load(f)
        log.info(f"Cache populated with {len(previously_validated_ids)} previously validated IDs from {ID_CACHE_PATH}")
    except FileNotFoundError:
        log.warn("ID cache file not found, starting fresh")
    except Exception as e:
        log.warn(f"Failed loading ID cache file, starting fresh (error: {e})")

    # If we have a file with known ISSN numbers, use it to populate the cache
    known_issns = {}
    try:
        with open(ISSN_PATH, 'r') as f:
            for line in f:
                known_issns[re.split(r'\s|\t', line)[0].strip()] = 1
            log.info(f"Cache populated with {len(known_issns)} ISSNs from {ISSN_PATH}")
    except Exception as e:
        log.warning(f"Failed loading ISSN file: {e}")
    # All harvest jobs have access to the same Manager-managed dictionaries
    manager = Manager()
    # id_cache (stuff seen during requests to external sources) should be saved,
    # but we don't want to waste time saving ISSNs already known from issn.txt,
    # hence separating "stuff learned during harvest" from "stuff learned from static file"
    ids_not_in_issn = set(previously_validated_ids.keys()) - set(known_issns.keys())
    id_cache = manager.dict(dict.fromkeys(ids_not_in_issn, 1))
    issn_cache = manager.dict(known_issns)
    harvest_cache = manager.dict({'id': id_cache, 'issn': issn_cache})

    log.info("Harvesting " + " ".join([source['code'] for source in sources_to_harvest]))

    t0 = time.time()
    if incremental:
        open_existing_storage()
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM cluster")
            cursor.execute("DELETE FROM finalized")
            cursor.execute("DELETE FROM search_single")
            cursor.execute("DELETE FROM search_doi")
            cursor.execute("DELETE FROM search_genre_form")
            cursor.execute("DELETE FROM search_subject")
            cursor.execute("DELETE FROM search_creator")
            cursor.execute("DELETE FROM search_org")
            cursor.execute("DELETE FROM search_fulltext")
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

    for source in sources_to_harvest:
        p = Process(target=harvest, args=(source, lock, harvested_count, harvest_cache, incremental))
        p.start()
        processes.append( p )
    for p in processes:
        p.join()
    
    t1 = time.time()
    diff = t1-t0
    log.info(f"Phase 1 (harvesting) ran for {diff} seconds")

    t0 = t1
    auto_classify()
    t1 = time.time()
    diff = t1-t0
    log.info(f"Phase 2 (auto-classification) ran for {diff} seconds")

    t0 = t1
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

    # Save ISSN/DOI cache for use next time
    try:
        log.info(f"Saving {len(harvest_cache['id'])} cached IDs to {ID_CACHE_PATH}")
        with open(ID_CACHE_PATH, 'w') as f:
            json.dump(dict(harvest_cache['id']), f)
    except Exception as e:
        log.warn(f"Failed saving harvest ID cache to {ID_CACHE_PATH}: {e}")
