from lxml.etree import fromstring
from lxml.etree import parse, XSLT, LxmlError
from io import StringIO
import re


class Parser(object):
    IDENTIFIER = '{http://www.openarchives.org/OAI/2.0/}identifier'
    MODS = '{http://www.loc.gov/mods/v3}mods'
    _convert = None
    match = re.compile("&(?!(#\\d+|\\w+);)")

    def __init__(self, f):
        self._convert = XSLT(parse(f.name))

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
        for elem in parse(StringIO(self.match.sub('&amp;', xml))).getroot():
            for c in elem:
                if c.tag == Parser.IDENTIFIER:
                    myid = c.text
                    break
                elif c.tag == Parser.MODS:
                    mods = c
                    break

            if None not in (myid, mods):
                break

        return myid, mods

    def parse(self, xml):
        try:
            myid, elem = self._components(xml)

            if elem is not None and len(elem):
                doc = self._xjson(fromstring(str(self._convert(elem))))
            else:
                doc = {}

            doc['@id'] = myid
            doc = self.strip(doc)

            return {'publication': doc, 'errors': []}
        except LxmlError as e:
            return {'publication': {}, 'errors': [{'message': str(e)}]}

    def strip(self, node):
        if isinstance(node, dict):
            return {k: self.strip(v) for k, v in node.items()}
        elif isinstance(node, list):
            return [self.strip(v) for v in node]
        elif isinstance(node, str):
            return node.strip()
        return node


def unescapematch(matchobj):
    escapesequence = matchobj.group(0)
    digits = escapesequence[2:]
    ordinal = int(digits, 16)
    char = chr(ordinal)
    return char
