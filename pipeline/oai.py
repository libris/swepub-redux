import requests
import xml.etree.ElementTree as ET

import pipeline.sickle as sickle
from pipeline.sickle.oaiexceptions import (
    BadArgument, BadVerb, BadResumptionToken,
    CannotDisseminateFormat, IdDoesNotExist, NoSetHierarchy,
    NoMetadataFormat, NoRecordsMatch, OAIError
)
from pipeline.modsstylesheet import ModsStylesheet

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
        sickle_client = sickle.Sickle(self.set["url"], max_retries=8, timeout=90)
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
        record = next(self.records)
        #print(f"next record: {record.header.identifier}") # status="deleted"
        root = ET.fromstring(record.header.raw)
        deleted = "status" in root.attrib and root.attrib["status"] == "deleted"
        transformed_record = self.stylesheet.apply(record.raw)
        return Record(record.header.identifier, deleted, transformed_record)


class Record:
    def __init__(self, oai_id=None, deleted=None, xml=''):
        self.xml = xml
        self.deleted = deleted
        self.oai_id = oai_id

    def is_successful(self):
        return bool(self.xml)


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
