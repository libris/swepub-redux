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
import json
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



def harvest(source):

    start_time = time.time()
    
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
                        #print(f"{200/diff} per sec, for last 200 , {total} done in total.")
                    if (len(batch) >= 512):
                        while (len(processes) >= 16):
                            time.sleep(0)
                            n = len(processes)
                            i = n-1
                            while i > -1:
                                if not processes[i].is_alive():
                                    #print("* CLEARING A PROCESS")
                                    del processes[i]
                                i -= 1
                        p = Process(target=threaded_handle_harvested, args=(batch,))
                        batch_count += 1
                        p.start()
                        processes.append( p )
                        batch = []
            p = Process(target=threaded_handle_harvested, args=(batch,))
            p.start()
            processes.append( p )
            for p in processes:
                p.join()
            finish_time = time.time()
            print(f'Harvest of {source["code"]} took {finish_time-start_time} seconds.')
        except HarvestFailed as e:
            print (f'FAILED HARVEST: {source["code"]}')
            exit -1

def threaded_handle_harvested(batch):
    for xml in batch:
        #print(f'Harvest harvest_item_id {record.harvest_item_id}')
        converted = convert(xml)
        if validate(xml, converted):
            #print(f"Validation passed for {converted['@id']}")
            store_converted(xml, converted)
        else:
            pass
            #print(f"Validation failed for {converted['@id']}")

sources = [
    {
        "name" : "Örebro universitet",
        "code": "oru",
        "sets": [
            {"url": "http://oru.diva-portal.org/dice/oai", "subset": "SwePub-oru", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Umeå universitet",
        "code": "umu",
        "sets": [
            {"url": "http://umu.diva-portal.org/dice/oai", "subset": "SwePub-umu", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Södertörns högskola",
        "code": "sh",
        "sets": [
            {"url": "http://sh.diva-portal.org/dice/oai", "subset": "SwePub-sh", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Sveriges lantbruksuniversitet",
        "code": "slu",
        "sets": [
            {"url": "http://slubar.slu.se/sps/cgi/oai2", "subset": "swepub", "metadata_prefix": "mods_sp30_sp3"}
        ]
    },
    {
        "name" : "Stockholms universitet",
        "code": "su",
        "sets": [
            {"url": "http://su.diva-portal.org/dice/oai", "subset": "SwePub-su", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Stockholms konstnärliga högskola",
        "code": "uniarts",
        "sets": [
            {"url": "http://uniarts.diva-portal.org/dice/oai", "subset": "SwePub-uniarts", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Statens väg- och transportforskningsinstitut",
        "code": "vti",
        "sets": [
            {"url": "http://vti.diva-portal.org/dice/oai", "subset": "SwePub-vti", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Sophiahemmet Högskola",
        "code": "shh",
        "sets": [
            {"url": "http://shh.diva-portal.org/dice/oai", "subset": "SwePub-shh", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Röda Korsets Högskola",
        "code": "rkh",
        "sets": [
            {"url": "http://rkh.diva-portal.org/dice/oai", "subset": "SwePub-rkh", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "RISE Research Institutes of Sweden",
        "code": "ri",
        "sets": [
            {"url": "http://ri.diva-portal.org/dice/oai", "subset": "SwePub-ri", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Riksantikvarieämbetet",
        "code": "raa",
        "sets": [
            {"url": "http://raa.diva-portal.org/dice/oai", "subset": "SwePub-raa", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Nordiska Afrikainstitutet",
        "code": "nai",
        "sets": [
            {"url": "http://nai.diva-portal.org/dice/oai", "subset": "SwePub-nai", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Naturvårdsverket",
        "code": "naturvardsverket",
        "sets": [
            {"url": "http://naturvardsverket.diva-portal.org/dice/oai", "subset": "SwePub-naturvardsverket", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Naturhistoriska riksmuseet",
        "code": "nrm",
        "sets": [
            {"url": "http://nrm.diva-portal.org/dice/oai", "subset": "SwePub-nrm", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Nationalmuseum",
        "code": "nationalmuseum",
        "sets": [
            {"url": "http://nationalmuseum.diva-portal.org/dice/oai", "subset": "SwePub-nationalmuseum", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Mälardalens högskola",
        "code": "mdh",
        "sets": [
            {"url": "http://mdh.diva-portal.org/dice/oai", "subset": "SwePub-mdh", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Mittuniversitetet",
        "code": "miun",
        "sets": [
            {"url": "http://miun.diva-portal.org/dice/oai", "subset": "SwePub-miun", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Malmö universitet",
        "code": "mau",
        "sets": [
            {"url": "http://mau.diva-portal.org/dice/oai", "subset": "SwePub-mau", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Lunds universitet",
        "code": "lu",
        "sets": [
            {"url": "http://lup.lub.lu.se/oai", "subset": "LU_SWEPUB", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Luleå tekniska universitet",
        "code": "ltu",
        "sets": [
            {"url": "http://ltu.diva-portal.org/dice/oai", "subset": "SwePub-ltu", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Linnéuniversitetet",
        "code": "lnu",
        "sets": [
            {"url": "http://lnu.diva-portal.org/dice/oai", "subset": "SwePub-lnu", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Linköpings universitet",
        "code": "liu",
        "sets": [
            {"url": "http://liu.diva-portal.org/dice/oai", "subset": "SwePub-liu", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Kungl. Musikhögskolan",
        "code": "kmh",
        "sets": [
            {"url": "http://kmh.diva-portal.org/dice/oai", "subset": "SwePub-kmh", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Kungl. Konsthögskolan",
        "code": "kkh",
        "sets": [
            {"url": "http://kkh.diva-portal.org/dice/oai", "subset": "SwePub-kkh", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Kungliga Tekniska högskolan",
        "code": "kth",
        "sets": [
            {"url": "http://kth.diva-portal.org/dice/oai", "subset": "SwePub-kth", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Konstfack",
        "code": "konstfack",
        "sets": [
            {"url": "http://konstfack.diva-portal.org/dice/oai", "subset": "SwePub-konstfack", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Karolinska Institutet",
        "code": "ki",
        "sets": [
            {"url": "http://openarchive.ki.se/oai/request", "subset": "com_10616_46998", "metadata_prefix": "swepub"},
            {"url": "http://prod.swepub.kib.ki.se", "subset": None, "metadata_prefix": "mods"}
        ]
    },
    {
        "name" : "Karlstads universitet",
        "code": "kau",
        "sets": [
            {"url": "http://kau.diva-portal.org/dice/oai", "subset": "SwePub-kau", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Jönköping University",
        "code": "hj",
        "sets": [
            {"url": "http://hj.diva-portal.org/dice/oai", "subset": "SwePub-hj", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Institutet för språk och folkminnen",
        "code": "sprakochfolkminnen",
        "sets": [
            {"url": "http://sprakochfolkminnen.diva-portal.org/dice/oai", "subset": "SwePub-sprakochfolkminnen", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Högskolan Väst",
        "code": "hv",
        "sets": [
            {"url": "http://hv.diva-portal.org/dice/oai", "subset": "SwePub-hv", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Högskolan Kristianstad",
        "code": "hkr",
        "sets": [
            {"url": "http://hkr.diva-portal.org/dice/oai", "subset": "SwePub-hkr", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Högskolan i Skövde",
        "code": "his",
        "sets": [
            {"url": "http://his.diva-portal.org/dice/oai", "subset": "SwePub-his", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Högskolan i Halmstad",
        "code": "hh",
        "sets": [
            {"url": "http://hh.diva-portal.org/dice/oai", "subset": "SwePub-hh", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Högskolan i Gävle",
        "code": "hig",
        "sets": [
            {"url": "http://hig.diva-portal.org/dice/oai", "subset": "SwePub-hig", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Högskolan i Borås",
        "code": "hb",
        "sets": [
            {"url": "http://hb.diva-portal.org/dice/oai", "subset": "SwePub-hb", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Högskolan Dalarna",
        "code": "du",
        "sets": [
            {"url": "http://du.diva-portal.org/dice/oai", "subset": "SwePub-du", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Göteborgs universitet",
        "code": "gu",
        "sets": [
            {"url": "https://gup.ub.gu.se/oai", "subset": None, "metadata_prefix": "mods"}
        ]
    },
    {
        "name" : "Gymnastik- och idrottshögskolan",
        "code": "gih",
        "sets": [
            {"url": "http://gih.diva-portal.org/dice/oai", "subset": "SwePub-gih", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Försvarshögskolan",
        "code": "fhs",
        "sets": [
            {"url": "http://fhs.diva-portal.org/dice/oai", "subset": "SwePub-fhs", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Ersta Sköndal Bräcke högskola",
        "code": "esh",
        "sets": [
            {"url": "http://ths.diva-portal.org/dice/oai", "subset": "SwePub-ths", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Blekinge Tekniska Högskola",
        "code": "bth",
        "sets": [
            {"url": "http://bth.diva-portal.org/dice/oai", "subset": "SwePub-bth", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Chalmers tekniska högskola",
        "code": "cth",
        "sets": [
            {"url": "http://research.chalmers.se/oai-pmh/swepub", "subset": "CHALMERS_SWEPUB", "metadata_prefix": "mods"}
        ]
    },
    {
        "name" : "Uppsala universitet",
        "code": "uu",
        "sets": [
            {"url": "http://uu.diva-portal.org/dice/oai", "subset": "SwePub-uu", "metadata_prefix": "swepub_mods"}
        ]
    },
    {
        "name" : "Enskilda Högskolan Stockholm",
        "code": "ths",
        "sets": [
            {"url": "http://ths.diva-portal.org/dice/oai", "subset": "SwePub-ths", "metadata_prefix": "swepub_mods"}
        ]
    }
]

if __name__ == "__main__":    
    clean_and_init_storage()
    processes = []
    #for source in sources:
    for source in sources[15:18]: # TEMP!
        p = Process(target=harvest, args=(source,))
        p.start()
        processes.append( p )
    for p in processes:
        p.join()
    deduplicate()
    #harvest(sources[2])
