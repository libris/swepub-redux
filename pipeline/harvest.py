import sickle
from modsstylesheet import ModsStylesheet
import hashlib
import requests
from uuid import uuid1
from convert import convert

from sickle.oaiexceptions import (
    BadArgument, BadVerb, BadResumptionToken,
    CannotDisseminateFormat, IdDoesNotExist, NoSetHierarchy,
    NoMetadataFormat, NoRecordsMatch, OAIError
)
from modsstylesheet import ModsStylesheet

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
        #self.stylesheet = ModsStylesheet(code, self.set.url)
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
        #self._clear_count()
        harvest_info = f'{set["url"]} ({set["subset"]}, {set["metadata_prefix"]})'
        record_iterator = RecordIterator(source["code"], set, None, None)
        try:
            #self.published_records = PublishedRecords(
            #    set.url, PREVENT_DUPLICATE_HARVESTS and not source.forced)
            for record in record_iterator:
                status = check_record(record)
                print(f'Harvest item {status}, harvest_item_id {record.harvest_item_id}')
                if status == 'OK':
                    converted = convert(record.xml)
                    print(f"converted someting, now with @id = {converted['@id']}")
            logger.info(
                f"Harvest of {harvest_info} completed with {self._get_stats()}.",
                extra=source.dict)
        except HarvestFailed as e:
            print ("FAILED HARVEST")
            exit -1

def check_record(record):
    if not record.is_successful():
        #self.harvest_stats.incr_failed()
        #self.failures += 1
        return 'fail'
    # This seems irrelevant for full harvests (only useful for the increment-and-already-done case)
    #elif self.published_records.has_been_published(record):
        #self.harvest_stats.incr_prevented()
        #self.prevented += 1
    #    return 'prevented'
    else:
        #self.harvest_stats.incr_successful()
        #self.successes += 1
        return 'OK'

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
