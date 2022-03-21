import re
from io import StringIO
from os import path

from lxml.etree import parse, XSLT, fromstring, LxmlError, XMLSyntaxError


class ModsParser(object):
    IDENTIFIER = "{http://www.openarchives.org/OAI/2.0/}identifier"
    MODS = "{http://www.loc.gov/mods/v3}mods"
    PARSED_XSL = parse(
        path.join(path.dirname(path.abspath(__file__)), "../resources/mods_to_xjsonld.xsl")
    )
    _convert = XSLT(PARSED_XSL)
    match = re.compile("&(?!(#\\d+|\\w+);)")

    def _xjson(self, x):
        if x.tag == "string":
            return "".join([y for y in x.itertext()])
        elif x.tag == "array":
            return [self._xjson(y) for y in x]
        elif x.tag == "dict":
            return {y.attrib["key"]: self._xjson(y) for y in x}

        return None

    def _components(self, xml, encode_ampsersand=False):
        myid = None
        mods = None
        if encode_ampsersand:
            elems = parse(StringIO(self.match.sub("&amp;", xml))).getroot()
        else:
            elems = parse(StringIO(xml)).getroot()
        for elem in elems:
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

    def parse_mods(self, xml, encode_ampersand=False):
        try:
            myid, elem = self._components(xml, encode_ampersand)

            if elem is not None and len(elem):
                doc = self._xjson(fromstring(str(self._convert(elem))))
            else:
                doc = {}

            doc["@id"] = myid
            doc = self.strip(doc)

            # return {'publication': doc, 'events': {'mods_converter_version': self.PARSED_XSL.getroot().get('version')}}
            return doc
        except (LxmlError, XMLSyntaxError) as e:
            # logger.exception(e)
            raise e

    def strip(self, node):
        if isinstance(node, dict):
            return {k: self.strip(v) for k, v in node.items()}
        elif isinstance(node, list):
            return [self.strip(v) for v in node]
        elif isinstance(node, str):
            return node.strip()
        return node


def convert(body):
    return ModsParser().parse_mods(body)
