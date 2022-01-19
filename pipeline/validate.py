import lxml.etree as et
from io import StringIO
from enrichers.issn import recover_issn
from log import log_for_OAI_id
from jsonpath_rw_ext import parse
import itertools
import requests
from normalize import *

from util import update_at_path, unicode_translate

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
    if errors.getroot():
        for error in errors.getroot():
            error_list.append(error.text)
        min_level_errors = {'bibliographical_minimum_level_error': error_list}
        log_for_OAI_id(body["@id"], min_level_errors)
    return bool(error_list)


def validate(raw_xml, body):
    if _should_be_rejected(raw_xml, body):
        return False
    
    session = requests.Session()

    for idb in body.get("identifiedBy", []):
        if idb["@type"] == "ISI":
            validate_isi(idb["value"])
            recover_isi(idb)
        if idb["@type"] == "DOI":
            recover_doi(idb)
        if idb["@type"] == "ISSN":
            validate_issn(idb, session)
            recover_issn(idb)
        if idb["@type"] == "ISBN":
            validate_isbn(idb["value"])
            recover_isbn(idb)
    
    for series in body.get("hasSeries", []):
        for idb in series.get("identifiedBy", []):
            if idb["@type"] == "ISSN":
                validate_issn(idb, session)
                recover_issn(idb)
        for title in series.get("hasTitle", []):
            if "mainTitle" in title:
                normalize_free_text(title, "mainTitle")
            if "subtitle" in title:
                normalize_free_text(title, "subtitle")
    
    for partOf in body.get("partOf", []):
        for series in partOf.get("hasSeries", []):
            for idb in series.get("identifiedBy", []):
                if idb["@type"] == "ISSN":
                    recover_issn(idb)
            for title in series.get("hasTitle", []):
                if "mainTitle" in title:
                    normalize_free_text(title, "mainTitle")
                if "subtitle" in title:
                    normalize_free_text(title, "subtitle")
        for idb in partOf.get("identifiedBy", []):
                if idb["@type"] == "ISSN":
                    validate_issn(idb, session)
                    recover_issn(idb)
                if idb["@type"] == "ISBN":
                    validate_isbn(idb["value"])
                    recover_isbn(idb)

    for contribution in body["instanceOf"].get("contribution", []):
        for idb in contribution.get("agent", {}).get("identifiedBy", []):
            if idb["@type"] == "ORCID":
                validate_orcid(idb["value"])
                recover_orcid(idb)

    for publication in body.get("publication", []):
        if publication.get("@type") == "Publication":
            new_date = unicode_translate(publication.get("date", None))
            if new_date:
                publication["date"] = new_date

    for key in body["instanceOf"]:
        obj = body["instanceOf"].get(key, {})
        if isinstance(obj, dict):
            for hasNote in obj.get("hasNote", []):
                if hasNote.get("@type", "") == "CreatorCount":
                    new_label = unicode_translate(publication.get("date", None))
                    if new_label:
                        publication["label"] = new_label

    for subject in body["instanceOf"].get("subject", []):
        if subject.get("inScheme", {}).get("code", "") == "uka.se":
            pass # UKA STUFF HERE
        if subject.get("@type", "") == "Topic" and "prefLabel" in subject:
            normalize_free_text(subject, "prefLabel")
        if subject.get("@type", "") == "Note" and "label" in subject:
            normalize_free_text(subject, "label")

    for title in body["instanceOf"].get("hasTitle", []):
        if "mainTitle" in title:
            normalize_free_text(title, "mainTitle")
        if "subtitle" in title:
            normalize_free_text(title, "subtitle")
    
    for summary in body["instanceOf"].get("summary", []):
        if "label" in summary:
            normalize_free_text(summary, "label")


    # "Enrichment".. ?
    # for id_type, jpath in PRECOMPILED_PATHS.items():
    #     matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
    #     for match in matches:
    #         if match.value:

    #             if id_type == 'ISBN':
    #                 recover_isbn(match.value, body, str(match.full_path), body["@id"])
    #             if id_type == 'ISI':
    #                 recover_isi(match.value, body, str(match.full_path), body["@id"])
    #             if id_type == 'ORCID':
    #                 recover_orcid(match.value, body, str(match.full_path), body["@id"])
    #             if id_type == 'ISSN':
    #                 recover_issn(match.value, body, str(match.full_path), body["@id"])
    #             if id_type == 'DOI':
    #                 recover_doi(match.value, body, str(match.full_path), body["@id"])
    #             if id_type == 'publication_year' or id_type == 'creator_count':
    #                 translated = unicode_translate(match.value)
    #                 if translated != match.value:
    #                     update_at_path(body, str(match.full_path), translated)

    # # Validation
    # passesValidation = True
    # for id_type, jpath in PRECOMPILED_PATHS.items():
    #     matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
    #     for match in matches:
    #         if match.value:
    #             #print( id_type )
    #             #print( str(match.full_path) )
    #             #print( match.value )

    #             if id_type == 'ISBN':
    #                 passesValidation &= validate_isbn(match.value, body["@id"])
    #             if id_type == 'ISI':
    #                 passesValidation &= validate_isi(match.value, body["@id"])
    #             if id_type == 'ORCID':
    #                 passesValidation &= validate_orcid(match.value, body["@id"])
    #             if id_type == 'ISSN':
    #                 passesValidation &= validate_issn(match.value, body["@id"], session)
    #             if id_type == 'DOI':
    #                 passesValidation &= validate_doi(match.value, body["@id"], session)
    #             if id_type == 'URI':
    #                 result = validate_base_unicode(match.value)
    #                 if result == False:
    #                     log_for_OAI_id(body["@id"], 'URI validation failed: unicode')
    #                     passesValidation = False
    #             if id_type == 'publication_year':
    #                 passesValidation &= validate_date_time(match.value, body["@id"])
    #             if id_type == 'creator_count':
    #                 if not (match.value.isnumeric() and int(match.value) > 0):
    #                     log_for_OAI_id(body["@id"], 'creator_count validation failed: numeric')
    #                     passesValidation = False
    #             if id_type == 'UKA':
    #                 passesValidation &= validate_uka(match.value, body["@id"])

    # # Normalization
    # for id_type, jpath in PRECOMPILED_PATHS.items():
    #     matches = itertools.chain.from_iterable(jp.find(body) for jp in jpath)
    #     for match in matches:
    #         if match.value:

    #             if id_type == 'ISBN':
    #                 normalize_isbn(match.value, body, str(match.full_path), body["@id"])
                    
    #             if id_type == 'ISI':
    #                 normalize_isi(match.value, body, str(match.full_path), body["@id"])
                    
    #             if id_type == 'ORCID':
    #                 normalize_orcid(match.value, body, str(match.full_path), body["@id"])
                    
    #             if id_type == 'ISSN':
    #                 normalize_issn(match.value, body, str(match.full_path), body["@id"])
                    
    #             if id_type == 'DOI':
    #                 normalize_doi(match.value, body, str(match.full_path), body["@id"])
                    
    #             if id_type == 'free_text':
    #                 normalize_free_text(match.value, body, str(match.full_path), body["@id"])

    return True # LOL? It's backwards, but this is the way they want it, "validate, but trust".
