import lxml.etree as et
from lxml.etree import parse, XSLT, fromstring, LxmlError, XMLSyntaxError
from io import StringIO
from storage import commit_sqlite, get_cursor, store_converted
from multiprocessing import Pool, Lock
import time
from validate import validate

class ModsParser(object):

    IDENTIFIER = '{http://www.openarchives.org/OAI/2.0/}identifier'
    MODS = '{http://www.loc.gov/mods/v3}mods'
    PARSED_XSL = parse('./pipeline/mods_to_xjsonld.xsl')
    _convert = XSLT(PARSED_XSL)

    def _xjson(self, x):
        if x.tag == 'string':
            return ''.join([y for y in x.itertext()])
        elif x.tag == 'array':
            return [self._xjson(y) for y in x]
        elif x.tag == 'dict':
            return {y.attrib['key']: self._xjson(y) for y in x}

        return None

    def _components(self, xml):
        myid = None
        mods = None
        for elem in parse(StringIO(xml)).getroot():
            for c in elem:
                if c.tag == ModsParser.IDENTIFIER:
                    myid = c.text
                    break
                elif c.tag == ModsParser.MODS:
                    mods = c
                    break

            if None not in (myid, mods):
                break

        return myid, mods

    def parse_mods(self, xml):
        try:
            myid, elem = self._components(xml)

            if elem is not None and len(elem):
                doc = self._xjson(fromstring(str(self._convert(elem))))
            else:
                doc = {}

            doc['@id'] = myid
            doc = self.strip(doc)

            #return {'publication': doc, 'events': {'mods_converter_version': self.PARSED_XSL.getroot().get('version')}}
            return doc
        except (LxmlError, XMLSyntaxError) as e:
            #logger.exception(e)
            raise e

    def strip(self, node):
        if isinstance(node, dict):
            return {k: self.strip(v) for k, v in node.items()}
        elif isinstance(node, list):
            return [self.strip(v) for v in node]
        elif isinstance(node, str):
            return node.strip()
        return node


modsparser = ModsParser()
def _convert_publication(body):
    return modsparser.parse_mods(body)

def convert():
    
    # Set up batching
    batch = []
    tasks = []

    with Pool(processes=16) as pool:
        cursor = get_cursor()
        inner_cursor = get_cursor()
        for row in cursor.execute("""
        SELECT
            id, data
        FROM
            original
        """):
            original_id = row[0]
            original_data = row[1]

            batch.append( (original_id, original_data) )

            if (len(batch) >= 32):
                while (len(tasks) >= 32):
                    time.sleep(0)
                    n = len(tasks)
                    i = n-1
                    while i > -1:
                        if tasks[i].ready():
                            result = tasks[i].get()
                            resultlist = result[0]
                            write_conversion_result(resultlist)
                            del(tasks[i])
                        i -= 1
                tasks.append(pool.map_async(_convert_batch, (batch,)))
                batch = []

        if len(batch) > 0:
            tasks.append(pool.map_async(_convert_batch, (batch,)))
        for task in tasks:
            while not task.ready():
                time.sleep(0)
            result = task.get()
            resultlist = result[0]
            write_conversion_result(resultlist)
            
def write_conversion_result(resultlist):
    for publication in resultlist:
        converted_data = publication["converted"]
        accepted = publication["accepted"]
        log_events = publication["log_events"]
        original_id = publication["original_id"]
        if accepted: # TEMP
            store_converted(converted_data, original_id)
    commit_sqlite

def _convert_batch(batch):
    results = []
    for original_id, original_data in batch:
        converted_data = _convert_publication(original_data)
        accepted = validate(original_data, converted_data)
        results.append({"converted": converted_data, "log_events": None, "accepted": accepted, "original_id": original_id})
    return results