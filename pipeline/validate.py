import lxml.etree as et
from io import StringIO
from enrichers.issn import recover_issn
from jsonpath_rw_ext import parse
import itertools
import requests
from normalize import *

from util import update_at_path, unicode_translate, make_event

from validators.datetime import validate_date_time
from validators.doi import validate_doi
from validators.issn import validate_issn
from validators.shared import validate_base_unicode
from validators.isbn import validate_isbn
from validators.isi import validate_isi
from validators.orcid import validate_orcid
from validators.uka import validate_uka

from enrichers.isbn import recover_isbn
from enrichers.isi import recover_isi
from enrichers.orcid import recover_orcid
from enrichers.doi import recover_doi

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
    if errors.getroot() is not None:
        for error in errors.getroot():
            error_list.append(error.text)
        min_level_errors = {'bibliographical_minimum_level_error': error_list}
    return bool(error_list)

def validate(raw_xml, body, id_cache, issn_cache):
    if _should_be_rejected(raw_xml, body):
        return (False, [])
    
    events = []
    session = requests.Session()

    # "Enrichment".. ?
    for id_type, jpath in PRECOMPILED_PATHS.items():
        matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
        for match in matches:
            if match.value:

                if id_type == 'ISBN':
                    recover_isbn(match.value, body, str(match.full_path), body["@id"], events)
                if id_type == 'ISI':
                    recover_isi(match.value, body, str(match.full_path), body["@id"], events)
                if id_type == 'ORCID':
                    recover_orcid(match.value, body, str(match.full_path), body["@id"], events)
                if id_type == 'ISSN':
                    recover_issn(match.value, body, str(match.full_path), body["@id"], events)
                if id_type == 'DOI':
                    recover_doi(match.value, body, str(match.full_path), body["@id"], events)
                if id_type == 'publication_year' or id_type == 'creator_count':
                    translated = unicode_translate(match.value)
                    if translated != match.value:
                        events.append(make_event("enrichment", "publication_year", str(match.full_path), "unicode", translated))
                        update_at_path(body, str(match.full_path), translated)

    # Validation
    for id_type, jpath in PRECOMPILED_PATHS.items():
        matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
        for match in matches:
            if match.value:
                #print( id_type )
                #print( str(match.full_path) )
                #print( match.value )

                if id_type == 'ISBN':
                    validate_isbn(match.value, str(match.full_path), events)
                if id_type == 'ISI':
                    validate_isi(match.value, str(match.full_path), events)
                if id_type == 'ORCID':
                    validate_orcid(match.value, str(match.full_path), events)
                if id_type == 'ISSN':
                    validate_issn(match.value, str(match.full_path), session, events, id_cache, issn_cache)
                if id_type == 'DOI':
                    validate_doi(match.value, str(match.full_path), session, events, id_cache)
                if id_type == 'URI':
                    result = validate_base_unicode(match.value)
                    if result == False:
                        events.append(make_event("validation", "URI", str(match.full_path), "unicode", "invalid"))
                if id_type == 'publication_year':
                    validate_date_time(match.value, str(match.full_path), events)
                if id_type == 'creator_count':
                    if not (match.value.isnumeric() and int(match.value) > 0):
                        events.append(make_event("validation", "URI", str(match.full_path), "numeric", "invalid"))
                if id_type == 'UKA':
                    validate_uka(match.value, str(match.full_path), events)

    # Normalization
    for id_type, jpath in PRECOMPILED_PATHS.items():
        matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
        for match in matches:
            if match.value:

                if id_type == 'ISBN':
                    normalize_isbn(match.value, body, str(match.full_path), events)
                    
                if id_type == 'ISI':
                    normalize_isi(match.value, body, str(match.full_path), events)
                    
                if id_type == 'ORCID':
                    normalize_orcid(match.value, body, str(match.full_path), events)
                    
                if id_type == 'ISSN':
                    normalize_issn(match.value, body, str(match.full_path), events)
                    
                if id_type == 'DOI':
                    normalize_doi(match.value, body, str(match.full_path), events)
                    
                if id_type == 'free_text':
                    normalize_free_text(match.value, body, str(match.full_path), events)

    return (True, events)
