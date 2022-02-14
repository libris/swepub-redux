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
from validators.uri import validate_uri
from validators.creator import validate_creator_count

from enrichers.isbn import recover_isbn
from enrichers.isi import recover_isi
from enrichers.orcid import recover_orcid
from enrichers.doi import recover_doi
from enrichers.unicode import recover_unicode

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


def should_be_rejected(raw_xml):
    error_list = []
    parsed_xml = et.parse(StringIO(raw_xml))
    errors = MINIMUM_LEVEL_FILTER(parsed_xml)
    min_level_errors = None
    if errors.getroot() is not None:
        for error in errors.getroot():
            error_list.append(error.text)
    return bool(error_list), error_list


class FieldMeta:
    def __init__(self, path, id_type, value=None):
        self.id_type = id_type
        self.path = path
        self.initial_value = value
        self.value = value
        self.validation_status = 'pending'  # 'valid', 'invalid', 'error', 'pending'
        self.enrichment_status = 'pending'  # 'enriched', 'unchanged', 'unsuccessful', 'pending', 'error',
        self.normalization_status = 'unchanged'  # 'unchanged', 'normalized'
        self.events = []

    def is_enriched(self):
        return self.enrichment_status == 'enriched'


def get_record_info(field_events):
    stats = {}
    # While a record can have multiple, say, ISBN fields with different validation/enrichment/normalization
    # results, for process-api purposes we need to be able to state something about the status of the
    # whole document. So, for a given field, e.g. ISBN:
    # - if *all* ISBNs are valid, the record's ISBN validation_status will be 'valid'
    # - if *any* ISBN is invalid, the record's ISBN validation_status will be 'invalid'
    # - etc.

    for id_type in field_events.values():
        for field in id_type.values():
            if not stats.get(field.id_type):
                stats[field.id_type] = {'events': []}

            if stats[field.id_type].get('validation_status', '') != 'invalid':
                stats[field.id_type]['validation_status'] = field.validation_status

            current_enrichment_status = stats[field.id_type].get('enrichment_status', '')
            if current_enrichment_status != 'unsuccessful':
                if not (current_enrichment_status == 'enriched' and field.enrichment_status == 'unchanged'):
                    stats[field.id_type]['enrichment_status'] = field.enrichment_status

            if stats[field.id_type].get('normalization_status', '') != 'normalized':
                stats[field.id_type]['normalization_status'] = field.normalization_status

            stats[field.id_type]['events'].extend(field.events)
    return stats


def validate_stuff(field_events, session, harvest_cache):
    for id_type in field_events.values():
        for field in id_type.values():
            if field.validation_status != 'valid':
                if field.id_type == 'ISBN':
                    validate_isbn(field)
                if field.id_type == 'ISI':
                    validate_isi(field)
                if field.id_type == 'ORCID':
                    validate_orcid(field)
                if field.id_type == 'ISSN':
                    validate_issn(field, session, harvest_cache)
                if field.id_type == 'DOI':
                    validate_doi(field, session, harvest_cache)
                if field.id_type == 'URI':
                    validate_uri(field)
                if field.id_type == 'publication_year':
                    validate_date_time(field)
                if field.id_type == 'creator_count':
                    validate_creator_count(field)
                if field.id_type == 'UKA':
                    validate_uka(field)
                if field.id_type == 'free_text':
                    field.validation_status = 'valid'  # formerly "AcceptingValidator"


def enrich_stuff(body, field_events):
    for id_type in field_events.values():
        for field in id_type.values():
            if field.validation_status != 'valid':
                if field.id_type == 'ISBN':
                    recover_isbn(body, field)
                if field.id_type == 'ISI':
                    recover_isi(body, field)
                if field.id_type == 'ORCID':
                    recover_orcid(body, field)
                if field.id_type == 'ISSN':
                    recover_issn(body, field)
                if field.id_type == 'DOI':
                    recover_doi(body, field)
                if field.id_type == 'publication_year':
                    recover_unicode(body, field)
                if field.id_type == 'creator_count':
                    recover_unicode(body, field)


def normalize_stuff(body, field_events):
    for id_type in field_events.values():
        for field in id_type.values():
            # Unlike with validations/enrichments we now only look at *valid* fields
            if field.validation_status == 'valid':
                if field.id_type == 'ISBN':
                    normalize_isbn(body, field)
                if field.id_type == 'ISI':
                    normalize_isi(body, field)
                if field.id_type == 'ORCID':
                    normalize_orcid(body, field)
                if field.id_type == 'ISSN':
                    normalize_issn(body, field)
                if field.id_type == 'DOI':
                    normalize_doi(body, field)
                if field.id_type == 'free_text':
                    normalize_free_text(body, field)


def get_clean_events(field_events):
    events_only = {}
    for id_type, paths in field_events.items():
        if not events_only.get(id_type):
            events_only[id_type] = {}
        for path, values in paths.items():
            if values.events:
                events_only[id_type][path] = {
                    'events': values.events,
                    'normalization_status': values.normalization_status,
                    'validation_status': values.validation_status,
                    'enrichment_status': values.enrichment_status
                }
    return events_only

def validate(body, harvest_cache):
    session = requests.Session()
    field_events = {}
    # For each path, create a FieldMeta object that we'll use during all
    # enrichments/validations/normalizations to keep some necessary state
    for id_type, jpath in PRECOMPILED_PATHS.items():
        matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
        for match in matches:
            if match.value:
                if not field_events.get(id_type):
                    field_events[id_type] = {}
                field_events[id_type][str(match.full_path)] = FieldMeta(str(match.full_path), id_type, match.value)

    validate_stuff(field_events, session, harvest_cache)
    enrich_stuff(body, field_events)
    # Second validation pass to see if enrichments made some values valid
    validate_stuff(field_events, session, harvest_cache)
    normalize_stuff(body, field_events)

    record_info = get_record_info(field_events)
    events_only = get_clean_events(field_events)

    return events_only, record_info
