import sickle
from modsstylesheet import ModsStylesheet
import hashlib
import requests
from uuid import uuid1
from convert import convert
import threading
import time

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
            logger.info("OAI-PMH query returned no matches.")
            raise StopIteration
        except OAIExceptions + RequestExceptions + (AttributeError,) as e:
            logger.exception(e, extra={
                'metadata_prefix': self.set.metadata_prefix,
                'subset': self.set.subset,
            })
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
    """Harvest a source and publish event when complete"""
    
    for set in source["sets"]:
        harvest_info = f'{set["url"]} ({set["subset"]}, {set["metadata_prefix"]})'
        record_iterator = RecordIterator(source["code"], set, None, None)
        try:
            # The point of using threads here is not CPU parallellism (as that doesn't
            # work in python anyway). The point is concurrency, which lets any number
            # of HTTP requests be in flight at once without blocking.
            batch = []
            threads = []
            for record in record_iterator:
                if record.is_successful():
                    batch.append(record.xml)
                    if (len(batch) >= 128):
                        while (len(threads) >= 128):
                            n = len(threads)
                            i = n
                            while i > 0:
                                if not threads[i].is_alive:
                                    del threads[i]
                                i -= 1
                            time.sleep(0)
                        t = threading.Thread(target=threaded_handle_harvested, args=(batch,))
                        t.start()
                        threads.append( t )
                        batch = []
            t = threading.Thread(target=threaded_handle_harvested, args=(batch,))
            t.start()
            threads.append( t )
            for t in threads:
                t.join()
        except HarvestFailed as e:
            print ("FAILED HARVEST")
            exit -1

def threaded_handle_harvested(batch):
    for xml in batch:
        #print(f'Harvest harvest_item_id {record.harvest_item_id}')
        converted = convert(xml)
        if validate(xml, converted):
            print(f"Validation passed for {converted['@id']}")
        else:
            print(f"Validation failed for {converted['@id']}")

#
#   - name: Chalmers tekniska högskola
#    code: cth
#    sets:
#      - url: http://research.chalmers.se/oai-pmh/swepub
#        subset: CHALMERS_SWEPUB
#        metadata_prefix: mods
#
source = {
    "name" : "Chalmers tekniska högskola",
    "code": "cth",
    "sets": [
        {"url": "http://research.chalmers.se/oai-pmh/swepub", "subset": "CHALMERS_SWEPUB", "metadata_prefix": "mods"}
    ]
}

harvest(source)
