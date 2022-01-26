from pathlib import Path
from autoclassify import auto_classify
from merge import merge
import sickle
from modsstylesheet import ModsStylesheet
import hashlib
import requests
from uuid import uuid1
from convert import convert
from deduplicate import deduplicate
import time
from multiprocessing import Process, Lock, Value
import sys
from storage import *

from sickle.oaiexceptions import (
    BadArgument, BadVerb, BadResumptionToken,
    CannotDisseminateFormat, IdDoesNotExist, NoSetHierarchy,
    NoMetadataFormat, NoRecordsMatch, OAIError
)
from modsstylesheet import ModsStylesheet
from validate import validate

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



def harvest(source, lock, harvested_count):

    start_time = time.time()

    for set in source["sets"]:
        harvest_info = f'{set["url"]} ({set["subset"]}, {set["metadata_prefix"]})'
        record_iterator = RecordIterator(source["code"], set, None, None)
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
                        p = Process(target=threaded_handle_harvested, args=(batch, source["code"], lock))
                        batch_count += 1
                        p.start()
                        processes.append( p )
                        batch = []
            p = Process(target=threaded_handle_harvested, args=(batch, source["code"], lock))
            p.start()
            processes.append( p )
            for p in processes:
                p.join()
            finish_time = time.time()
            print(f'Harvest of {source["code"]} took {finish_time-start_time} seconds.')
        except HarvestFailed as e:
            print (f'FAILED HARVEST: {source["code"]}')
            exit -1


def threaded_handle_harvested(batch, source, lock):
    for xml in batch:
        converted = convert(xml)
        (accepted, events) = validate(xml, converted)
        lock.acquire()
        try:
            store_original_and_converted(xml, converted, source, accepted, events)
        finally:
            lock.release()


sources = json.load(open(os.path.dirname(__file__) + '/sources.json'))

if __name__ == "__main__":
    args = sys.argv[1:]

    if "devdata" in args:
        sources_to_harvest = [sources["mdh"], sources["miun"], sources["mau"]]
    elif len(args) > 0:
        sources_to_harvest = []
        for arg in args:
            if arg not in sources:
                print(f"Source {arg} does not exist in sources.json")
                sys.exit(1)
            sources_to_harvest.append(sources[arg])
    else:
        sources_to_harvest = list(sources.values())

    print("Harvesting", " ".join([source['code'] for source in sources_to_harvest]))

    t0 = time.time()
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
        p = Process(target=harvest, args=(source,lock,harvested_count))
        p.start()
        processes.append( p )
    for p in processes:
        p.join()

    t1 = time.time()
    diff = t1-t0
    print(f"Phase 1 (harvesting) ran for {diff} seconds")
    t0 = t1
    auto_classify()
    t1 = time.time()
    diff = t1-t0
    print(f"Phase 2 (auto-classification) ran for {diff} seconds")
    t0 = t1
    deduplicate()
    t1 = time.time()
    diff = t1-t0
    print(f"Phase 3 (deduplication) ran for {diff} seconds")
    t0 = t1
    merge()
    t1 = time.time()
    diff = t1-t0
    print(f"Phase 4 (merging) ran for {diff} seconds")
    

