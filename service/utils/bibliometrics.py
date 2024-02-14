import orjson as json
import os
import sys

from pipeline.bibframesource import BibframeSource

CREATOR_FIELDS = [
    "familyName",
    "givenName",
    "localId",
    "localIdBy",
    "ORCID",
    "affiliation",
    "freetext_affiliations",
]
SUBJECT_FIELDS = ["oneDigitTopics", "threeDigitTopics", "fiveDigitTopics"]


def build_deduplicated_result(es_result):
    hits = es_result.get("hits", {}).get("hits", [])
    if not hits:
        return None
    return BibframeSource(hits[0].get("_source")).bibframe_master


def build_result(row, fields):
    errors = list()
    (result_hit, errors) = _build_hit(json.loads(row["data"]), fields)
    return result_hit, errors


def _build_hit(bibframe_record, fields):
    errors = list()
    bibframe_source = BibframeSource(bibframe_record, fields)

    # maps chosen fields to BibframeSource properties
    field_property_dict = {
        "archiveURI": "archive_URI",
        "autoclassified": "autoclassified",
        "classifications": "ssif_subjects",
        "contentMarking": "content_marking",
        "creatorCount": "creator_count",
        "creators": "creators",
        "DOAJ": "DOAJ",
        "DOI": "DOI",
        "duplicateIds": "duplicate_ids",
        "electronicLocator": "electronic_locator",
        "ISBN": "ISBN",
        "ISI": "ISI",
        "ISSN": "ISSN",
        "keywords": "keywords",
        "languages": "languages",
        "openAccess": "open_access",
        "openAccessVersion": "open_access_version",
        "outputTypes": "output_types",
        "PMID": "PMID",
        "publicationChannel": "publication_channel",
        "publicationCount": "publication_count",
        "publicationStatus": "publication_status",
        "publicationYear": "publication_year",
        "publisher": "publisher",
        "recordId": "record_id",
        "scopusId": "scopus_id",
        "series": "series",
        "seriesTitle": "series_title",
        "source": "source_org",
        "summary": "summary",
        "swedishList": "swedish_list",
        "title": "title",
    }

    result = dict()
    if bibframe_source.include_all:
        for field_label, prop_str in field_property_dict.items():
            result.update({field_label: getattr(bibframe_source, prop_str)})
    else:
        if fields is not None:
            for field in fields:
                if field in CREATOR_FIELDS:
                    if "creators" not in result.keys() and "creators" not in fields:
                        # add creators field if one of creator_fields has been chosen,
                        # if not already in fields or result
                        field = "creators"
                    else:
                        # do not add as these fields will be added to creator
                        continue
                elif field in SUBJECT_FIELDS:
                    if "classifications" not in result.keys() and "classifications" not in fields:
                        # add classifications field if one of subject_fields has been chosen,
                        # if not already in fields or result
                        field = "classifications"
                    else:
                        # do not add as these fields will be added to classifications
                        continue

                prop = field_property_dict.get(field)
                if prop is None:
                    # invalid field name
                    errors.append(f"Invalid field name: {field}")
                    break
                else:
                    result.update({field: getattr(bibframe_source, prop)})

    return result, errors
