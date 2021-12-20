from pathlib import Path
import sickle
from modsstylesheet import ModsStylesheet
import hashlib
import requests
from uuid import uuid1
from convert import convert
from deduplicate import deduplicate
import time
from multiprocessing import Process
import shutil

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



def harvest(source):
    shutil.rmtree("./output")
    Path("./output/raw/").mkdir(parents=True, exist_ok=True)
    
    for set in source["sets"]:
        harvest_info = f'{set["url"]} ({set["subset"]}, {set["metadata_prefix"]})'
        record_iterator = RecordIterator(source["code"], set, None, None)
        try:
            batch_count = 0
            batch = []
            processes = []
            records_in_batch = 0
            total = 0
            t0 = time.time()
            
            for record in record_iterator:
                if record.is_successful():
                    batch.append(record.xml)
                    records_in_batch += 1
                    total += 1
                    if records_in_batch == 200:
                        records_in_batch = 0
                        t1 = time.time()
                        diff = t1 - t0
                        t0 = t1
                        print(f"{200/diff} per sec, for last 200 , {total} done in total.")
                    if (len(batch) >= 512):
                        while (len(processes) >= 16):
                            time.sleep(0)
                            n = len(processes)
                            i = n-1
                            while i > -1:
                                if not processes[i].is_alive():
                                    print("* CLEARING A PROCESS")
                                    del processes[i]
                                i -= 1
                        p = Process(target=threaded_handle_harvested, args=(batch,f'./output/raw/{batch_count}'))
                        batch_count += 1
                        p.start()
                        processes.append( p )
                        batch = []
            p = Process(target=threaded_handle_harvested, args=(batch,f'./output/raw/{batch_count}'))
            p.start()
            processes.append( p )
            for p in processes:
                p.join()
            deduplicate()
        except HarvestFailed as e:
            print ("FAILED HARVEST")
            exit -1

def threaded_handle_harvested(batch, batch_file):
    print(f"RUNNING WITH FILE: {batch_file}")
    with open(batch_file, "w") as f:
        for xml in batch:
            #print(f'Harvest harvest_item_id {record.harvest_item_id}')
            converted = convert(xml)
            if validate(xml, converted):
                #print(f"Validation passed for {converted['@id']}")
                f.write(f"{converted}\n")
            else:
                pass
                #print(f"Validation failed for {converted['@id']}")

sources = [

#
#   - name: Chalmers tekniska högskola
#    code: cth
#    sets:
#      - url: http://research.chalmers.se/oai-pmh/swepub
#        subset: CHALMERS_SWEPUB
#        metadata_prefix: mods
#
{
    "name" : "Chalmers tekniska högskola",
    "code": "cth",
    "sets": [
        {"url": "http://research.chalmers.se/oai-pmh/swepub", "subset": "CHALMERS_SWEPUB", "metadata_prefix": "mods"}
    ]
},

#
#   - name: Uppsala universitet
#    code: uu
#    sets:
#      - url: http://uu.diva-portal.org/dice/oai
#        subset: SwePub-uu
#        metadata_prefix: swepub_mods
#
{
    "name" : "Uppsala universitet",
    "code": "uu",
    "sets": [
        {"url": "http://uu.diva-portal.org/dice/oai", "subset": "SwePub-uu", "metadata_prefix": "swepub_mods"}
    ]
},
#  - name: Enskilda Högskolan Stockholm
#    code: ths
#    sets:
#      - url: http://ths.diva-portal.org/dice/oai
#        subset: SwePub-ths
#        metadata_prefix: swepub_mods
{
    "name" : "Enskilda Högskolan Stockholm",
    "code": "ths",
    "sets": [
        {"url": "http://ths.diva-portal.org/dice/oai", "subset": "SwePub-ths", "metadata_prefix": "swepub_mods"}
    ]
}

]

harvest(sources[2])
