import lxml.etree as et
from io import StringIO
from log import log_for_OAI_id
from jsonpath_rw_ext import parse
import itertools

MINIMUM_LEVEL_FILTER = et.XSLT(et.parse('./pipeline/minimumlevelfilter.xsl'))

PATHS = {
    'URI': ('identifiedBy[?(@.@type=="URI")].value', ),
    'DOI': ('identifiedBy[?(@.@type=="DOI")].value', ),
    'ISI': ('identifiedBy[?(@.@type=="ISI")].value', ),
    'ORCID': ('instanceOf.contribution.[*].agent.identifiedBy[?(@.@type=="ORCID")].value', ),
    'publication_year': ('publication[?(@.@type=="Publication")].date', ),
    'creator_count': ('instanceOf.[*].hasNote[?(@.@type=="CreatorCount")].label', ),
    'ISBN': (
        'identifiedBy[?(@.@type=="ISBN")].value',
        'partOf.[*].identifiedBy[?(@.@type=="ISBN")].value'),
    'ISSN': (
        'identifiedBy[?(@.@type=="ISSN")].value',
        'hasSeries.[*].identifiedBy[?(@.@type=="ISSN")].value',
        'partOf.[*].hasSeries.[*].identifiedBy[?(@.@type=="ISSN")].value',
        'partOf.[*].identifiedBy[?(@.@type=="ISSN")].value',),
    'free_text': (
        'hasSeries.[*].hasTitle.[*].mainTitle',
        'partOf.[*].hasSeries.[*].hasTitle.[*].mainTitle',
        'hasSeries.[*].hasTitle.[*].subtitle',
        'partOf.[*].hasSeries.[*].hasTitle.[*].subtitle',
        'instanceOf.hasTitle[*].mainTitle',
        'instanceOf.hasTitle[*].subtitle',
        'instanceOf.summary[*].label',
        'instanceOf.subject[?(@.@type=="Topic")].prefLabel',
        'instanceOf.hasNote[?(@.@type=="Note")].label'),
    'UKA': ('instanceOf.subject[?(@.inScheme.code=="uka.se")].code',),
}

PRECOMPILED_PATHS = {k: [parse(p) for p in v] for k, v in PATHS.items()}


def _should_be_rejected(raw_xml, body):
    error_list = []
    parsed_xml = et.parse(StringIO(raw_xml))
    errors = MINIMUM_LEVEL_FILTER(parsed_xml)
    if errors.getroot():
        for error in errors.getroot():
            error_list.append(error.text)
        min_level_errors = {'bibliographical_minimum_level_error': error_list}
        log_for_OAI_id(body["@id"], min_level_errors)
    return bool(error_list)


def validate(raw_xml, body):
    if _should_be_rejected(raw_xml, body):
        return False
    else:
        log_for_OAI_id(body["@id"], "Converted OK!")
    
    for id_type, jpath in PRECOMPILED_PATHS.items():
        matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
        for match in matches:
            if match.value:
                print( id_type )
                print( str(match.full_path) )
                print( match.value )
    
    # NOTE: More than 10 "validations" should short cut to normalizer
