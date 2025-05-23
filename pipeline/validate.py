import lxml.etree as et
from io import StringIO
from jsonpath_rw_ext import parse
import itertools
from os import path

from pipeline.normalize import *

from pipeline.util import get_at_path, remove_at_path, FieldMeta, Enrichment, Validation, Normalization, SSIF_SCHEME

from pipeline.validators.datetime import validate_date_time
from pipeline.validators.doi import validate_doi
from pipeline.validators.issn import validate_issn
from pipeline.validators.isbn import validate_isbn
from pipeline.validators.isi import validate_isi
from pipeline.validators.orcid import validate_orcid
from pipeline.validators.ssif import validate_ssif
from pipeline.validators.uri import validate_uri
from pipeline.validators.creator import validate_creator_count

from pipeline.enrichers.issn import recover_issn
from pipeline.enrichers.isbn import recover_isbn
from pipeline.enrichers.isi import recover_isi
from pipeline.enrichers.orcid import recover_orcid
from pipeline.enrichers.doi import recover_doi
from pipeline.enrichers.unicode import recover_unicode
from pipeline.enrichers.localid import recover_orcid_from_localid

MINIMUM_LEVEL_FILTER = et.XSLT(
    et.parse(path.join(path.dirname(path.abspath(__file__)), "../resources/minimumlevelfilter.xsl"))
)

PATHS = {
    "URI": ('identifiedBy[?(@.@type=="URI")].value',),
    "DOI": ('identifiedBy[?(@.@type=="DOI")].value',),
    "ISI": ('identifiedBy[?(@.@type=="ISI")].value',),
    "ORCID": ('instanceOf.contribution.[*].agent.identifiedBy[?(@.@type=="ORCID")].value',),
    "PersonID": ('instanceOf.contribution.[*].agent.identifiedBy[?(@.@type=="Local")]',),
    "publication_year": ('publication[?(@.@type=="Publication")].date',),
    "creator_count": ('instanceOf.[*].hasNote[?(@.@type=="CreatorCount")].label',),
    "ISBN": (
        'identifiedBy[?(@.@type=="ISBN")].value',
        'isPartOf.[*].identifiedBy[?(@.@type=="ISBN")].value',
    ),
    "ISSN": (
        'identifiedBy[?(@.@type=="ISSN")].value',
        'hasSeries.[*].identifiedBy[?(@.@type=="ISSN")].value',
        'isPartOf.[*].hasSeries.[*].identifiedBy[?(@.@type=="ISSN")].value',
        'isPartOf.[*].identifiedBy[?(@.@type=="ISSN")].value',
    ),
    "free_text": (
        "hasSeries.[*].hasTitle.[*].mainTitle",
        "isPartOf.[*].hasSeries.[*].hasTitle.[*].mainTitle",
        "hasSeries.[*].hasTitle.[*].subtitle",
        "isPartOf.[*].hasSeries.[*].hasTitle.[*].subtitle",
        "instanceOf.hasTitle[*].mainTitle",
        "instanceOf.hasTitle[*].subtitle",
        "instanceOf.summary[*].label",
        'instanceOf.subject[?(@.@type=="Topic")].prefLabel',
        'instanceOf.hasNote[?(@.@type=="Note")].label',
    ),
    "SSIF": (f"instanceOf.classification[*].@id",),
}

PRECOMPILED_PATHS = {k: [parse(p) for p in v] for k, v in PATHS.items()}


def _minimum_level_checker(raw_xml):
    parsed_xml = et.parse(StringIO(raw_xml))
    return MINIMUM_LEVEL_FILTER(parsed_xml)


def should_be_rejected(raw_xml):
    error_list = []
    errors = _minimum_level_checker(raw_xml)
    if errors.getroot() is not None:
        for error in errors.getroot():
            error_list.append(error.text)
    return bool(error_list), error_list


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
                stats[field.id_type] = {"events": []}

            if stats[field.id_type].get("validation_status", "") != Validation.INVALID:
                stats[field.id_type]["validation_status"] = field.validation_status

            current_enrichment_status = stats[field.id_type].get("enrichment_status", "")
            if current_enrichment_status != Enrichment.UNSUCCESSFUL:
                if not (
                    current_enrichment_status == Enrichment.ENRICHED
                    and field.enrichment_status == Enrichment.UNCHANGED
                ):
                    stats[field.id_type]["enrichment_status"] = field.enrichment_status

            if stats[field.id_type].get("normalization_status", "") != Normalization.NORMALIZED:
                stats[field.id_type]["normalization_status"] = field.normalization_status

            stats[field.id_type]["events"].extend(field.events)
    return stats


def validate_stuff(field_events, session, harvest_cache, body, source, cached_paths):
    for id_type in field_events.values():
        for field in id_type.values():
            if field.validation_status != Validation.VALID:
                if field.id_type == "ISBN":
                    validate_isbn(field)
                if field.id_type == "ISI":
                    validate_isi(field)
                if field.id_type == "ORCID":
                    validate_orcid(field, body, harvest_cache, source, cached_paths)
                if field.id_type == "ISSN":
                    validate_issn(field, session, harvest_cache)
                if field.id_type == "DOI":
                    validate_doi(field, session, harvest_cache)
                if field.id_type == "URI":
                    validate_uri(field)
                if field.id_type == "publication_year":
                    validate_date_time(field)
                if field.id_type == "creator_count":
                    validate_creator_count(field)
                # SSIF is not enriched, so don't validate it twice.
                if field.validation_status == Validation.PENDING:
                    if field.id_type == "SSIF":
                        validate_ssif(field)
                if field.id_type == "free_text":
                    field.validation_status = Validation.VALID  # formerly "AcceptingValidator"


def enrich_stuff(body, field_events, cached_paths):
    created_fields = {}
    for id_type in field_events.values():
        for field in id_type.values():
            added_stuff = []
            if field.validation_status != Validation.VALID:
                if field.id_type == "ISBN":
                    added_stuff = recover_isbn(body, field, cached_paths)
                if field.id_type == "ISI":
                    recover_isi(body, field, cached_paths)
                if field.id_type == "ORCID":
                    recover_orcid(body, field, cached_paths)
                if field.id_type == "ISSN":
                    added_stuff = recover_issn(body, field, cached_paths)
                if field.id_type == "DOI":
                    recover_doi(body, field, cached_paths)
                if field.id_type == "publication_year":
                    recover_unicode(body, field, cached_paths)
                if field.id_type == "creator_count":
                    recover_unicode(body, field, cached_paths)

                if added_stuff:
                    if field.id_type not in created_fields:
                        created_fields[field.id_type] = []
                    created_fields[field.id_type].extend(added_stuff)
    for id_type, fields in created_fields.items():
        for field in fields:
            field_events[id_type][field.path] = field


def enrich_stuff_a_little_more(body, field_events, harvest_cache, source, cached_paths, read_only_cursor):
    created_fields = {}
    for id_type in field_events.values():
        for field in id_type.values():
            added_stuff = []
            if field.id_type == "PersonID":
                added_stuff = recover_orcid_from_localid(body, field, harvest_cache, source, cached_paths, read_only_cursor)

            if added_stuff:
                if field.id_type not in created_fields:
                    created_fields[field.id_type] = []
                created_fields[field.id_type].extend(added_stuff)
    for id_type, fields in created_fields.items():
        for field in fields:
            field_events[id_type][field.path] = field


def normalize_stuff(body, field_events, cached_paths):
    for id_type in field_events.values():
        for field in id_type.values():
            # Unlike with validations/enrichments we now only look at *valid* fields
            if field.validation_status == Validation.VALID:
                if field.id_type == "ISBN":
                    normalize_isbn(body, field, cached_paths)
                if field.id_type == "ISI":
                    normalize_isi(body, field, cached_paths)
                if field.id_type == "ORCID" or field.id_type == "PersonID":
                    normalize_orcid(body, field, cached_paths)
                if field.id_type == "ISSN":
                    normalize_issn(body, field, cached_paths)
                if field.id_type == "DOI":
                    normalize_doi(body, field, cached_paths)
                if field.id_type == "free_text":
                    normalize_free_text(body, field, cached_paths)


def move_incorrectlyIdentifiedBy(body, field_events, cached_paths):
    pathsToRemove = []
    for id_type in field_events.values():
        for field in id_type.values():
            # For the _invalid_ fields, we (sometimes) want to add them under incorrectlyIdentifiedBy
            if field.validation_status != Validation.VALID and field.id_type in ["DOI", "ISBN", "ISI", "ISSN"]:

                # Schedule the path of the bad value for removal
                pathsToRemove.append(field.path)

                # Add it back, as incorrectlyIdentifiedBy
                parentPath = ".".join(field.path.split(".")[:-3]) # strip away ".identifiedBy.[0].value" (3 items)
                entityPath = ".".join(field.path.split(".")[:-1]) # strip away ".value" (1 item)

                parent = get_at_path(body, parentPath)
                incorrectlyIdentifiedByEntity = dict(get_at_path(body, entityPath))

                if "incorrectlyIdentifiedBy" not in parent:
                    parent["incorrectlyIdentifiedBy"] = [incorrectlyIdentifiedByEntity]
                else:
                    parent["incorrectlyIdentifiedBy"].append(incorrectlyIdentifiedByEntity)
                
                field.enrichment_status = Enrichment.ENRICHED

                field.events.append(
                    make_event(
                        event_type="enrichment",
                        code="incorrectlyIdentifiedBy",
                        value=None,
                        initial_value=incorrectlyIdentifiedByEntity.get("value", ""),
                        result=None,
                    )
                )

    if pathsToRemove:

        # The point of this is that for example ..identifiedBy.[1].. be
        # removed _before_ ..identifiedBy.[0].. , becuase removing a lower index first,
        # would displace the higher index and the wrong thing would be deleted.
        pathsToRemove.sort(reverse=True)
        for path in pathsToRemove:
            remove_at_path(body, path, 1)


# The point of this is that invalid ORCIDs often contain other sorts of personal information
# Which we _do not_ want to have on file, or in the worst case even publicly displayed.
def censor_invalid_orcids(body, field_events, cached_paths):
    for id_type in field_events.values():
        for field in id_type.values():
            if field.validation_status != Validation.VALID and field.id_type == "ORCID":
                field.enrichment_status = Enrichment.ENRICHED
                field.events.append(
                    make_event(
                        event_type="enrichment",
                        code="removed",
                        value="[redacted]",
                        initial_value=field.value,
                        result=None,
                    )
                )
                update_at_path(body, field.path, "[redacted]", cached_paths)


def get_clean_events(field_events):
    events_only = {}
    for id_type, paths in field_events.items():
        if not events_only.get(id_type):
            events_only[id_type] = {}
        for path, values in paths.items():
            if values.events:
                events_only[id_type][path] = {
                    "events": values.events,
                    "normalization_status": values.normalization_status,
                    "validation_status": values.validation_status,
                    "enrichment_status": values.enrichment_status,
                }
    return events_only


def validate(body, harvest_cache, session, source, cached_paths, read_only_cursor):
    field_events = {}
    # For each path, create a FieldMeta object that we'll use during all
    # enrichments/validations/normalizations to keep some necessary state
    for id_type, jpath in PRECOMPILED_PATHS.items():
        matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
        for match in matches:
            if match.value:
                if not field_events.get(id_type):
                    field_events[id_type] = {}
                field_events[id_type][str(match.full_path)] = FieldMeta(
                    str(match.full_path), id_type, match.value
                )

    validate_stuff(field_events, session, harvest_cache, body, source, cached_paths)
    enrich_stuff(body, field_events, cached_paths)
    # Second validation pass to see if enrichments made some values valid
    validate_stuff(field_events, session, harvest_cache, body, source, cached_paths)
    enrich_stuff_a_little_more(body, field_events, harvest_cache, source, cached_paths, read_only_cursor)
    normalize_stuff(body, field_events, cached_paths)
    # Beware, after this point all field_event paths must be considered potentially corrupt,
    # as moving things around places them at new paths!
    move_incorrectlyIdentifiedBy(body, field_events, cached_paths)
    censor_invalid_orcids(body, field_events, cached_paths)

    record_info = get_record_info(field_events)
    events_only = get_clean_events(field_events)

    return events_only, record_info
