import lxml.etree as et
from lxml.etree import parse, XSLT, fromstring, LxmlError, XMLSyntaxError
from io import StringIO
from storage import commit_sqlite, get_cursor, store_converted
from multiprocessing import Process, Lock
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

    lock = Lock()

    processes = []
    cursor = get_cursor()
    inner_cursor = get_cursor()
    for row in cursor.execute("""
    SELECT
        id, data
    FROM
        original
    """):
        original_rowid = row[0]
        original_data = row[1]

        batch.append( (original_rowid, original_data) )

        if (len(batch) >= 32):
            while (len(processes) >= 32):
                time.sleep(0)
                n = len(processes)
                i = n-1
                while i > -1:
                    if not processes[i].is_alive():
                        processes[i].join()
                        del processes[i]
                    i -= 1
            
            p = Process(target=_convert_and_write_batch, args=(batch, lock))
            p.start()
            processes.append( p )
            batch = []
    
    p = Process(target=_convert_and_write_batch, args=(batch, lock))
    p.start()
    processes.append( p )
    for p in processes:
        p.join()
            
def _convert_and_write_batch(batch, lock):
    lock.acquire()
    try:
        for (original_rowid, original_data) in batch:
            #print(f"In pool: {original_data}\n\n")
            converted_data = _convert_publication(original_data)
            if validate(original_data, converted_data):
                #print(f"Valid: {converted_data['@id']}")
                store_converted(converted_data, original_rowid)
    finally:
        commit_sqlite
        lock.release()
    
    