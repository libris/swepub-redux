import re
from urllib.parse import urlunparse

from service.utils.common import get_base_url
from pipeline.util import ENRICHING_AUDITORS

DEFAULT_FIELDS = [
    "DOI",
    "ISBN",
    "ISI",
    "ISSN",
    "ORCID",
    "UKA",
    "URI",
    "creator_count",
    "free_text",
    "publication_year",
    "PersonID",
]

DEFAULT_AUDITORS = [
    "ContributorAuditor",
    "ISSNAuditor",
    "CreatorCountAuditor",
    "UKAAuditor",
    "AutoclassifierAuditor",
    "OAAuditor",
    "CrossrefAuditorPublisher",
    "CrossrefAuditorPublisherLocation",
    "CrossrefAuditorPublishedPrint",
    "CrossrefAuditorProvisionActivity",
    "CrossrefAuditorISSN",
    "CrossrefAuditorSummary",
    "CrossrefAuditorLicense",
]

AUDIT_LABEL_MAP = {
    "ContributorAuditor": "contributor_duplicate_check",
    "ISSNAuditor": "ISSN_missing_check",
    "CreatorCountAuditor": "creator_count_check",
    "UKAAuditor": "UKA_comprehensive_check",
    "AutoclassifierAuditor": "auto_classify",
    "SwedishListAuditor": "swedish_list_check",
    "OAAuditor": "add_oa",
    "CrossrefAuditorPublisher": "add_crossref_publisher",
    "CrossrefAuditorPublisherLocation": "add_crossref_publisher_location",
    "CrossrefAuditorPublishedPrint": "add_crossref_published_print",
    "CrossrefAuditorProvisionActivity": "add_crossref_published_online",
    "CrossrefAuditorISSN": "add_crossref_issn_type",
    "CrossrefAuditorSummary": "add_crossref_summary",
    "CrossrefAuditorLicense": "add_crossref_license",
}

LABEL_AUDIT_MAP = dict()
for k, v in AUDIT_LABEL_MAP.items():
    LABEL_AUDIT_MAP.update({v: k})

DELIVERY_STATUS_ERROR_DESCRIPTIONS = {
    "recordContentSourceViolation": {
        "swe": "Organisationskod saknas",
        "eng": "Missing organization code",
    },
    "nameViolation": {"swe": "Upphov felaktigt", "eng": "Invalid contribution"},
    "titleViolation": {"swe": "Titel saknas", "eng": "Missing title"},
    "publicationOrOutputTypeViolation": {
        "swe": "Outputtyp/publikationstyp felaktig",
        "eng": "Invalid output/publication type",
    },
    "contentTypeViolation": {
        "swe": "Innehållstyp felaktig",
        "eng": "Invalid content type",
    },
    "publicationDateViolation": {
        "swe": "Utgivningsdatum saknas",
        "eng": "Missing publication date",
    },
    "uriViolation": {"swe": "URI saknas", "eng": "Missing URI"},
    "languageViolation": {"swe": "Språkkod felaktig", "eng": "Invalid language code"},
    "relatedItemTypeMissing": {
        "swe": "Värdpublikation saknas",
        "eng": "Missing host publication",
    },
    "relatedItemTypeViolation": {
        "swe": "Värdpublikation felaktig",
        "eng": "Invalid host publication",
    },
}


def parse_flags(validation_flags, enrichment_flags, normalization_flags, audit_flags):
    (validation_errors, validation_flags) = _parse_flag_type(validation_flags)
    (enrichment_errors, enrichment_flags) = _parse_flag_type(enrichment_flags)
    (normalization_errors, normalization_flags) = _parse_flag_type(normalization_flags)
    (audit_errors, audit_flags) = _parse_flag_type(audit_flags)
    errors = []
    errors.extend(validation_errors)
    errors.extend(enrichment_errors)
    errors.extend(normalization_errors)
    errors.extend(audit_errors)

    flags = {
        "validation": validation_flags,
        "enrichment": enrichment_flags,
        "normalization": normalization_flags,
        "audit": audit_flags,
    }
    return errors, flags


def has_selected_flags(flags):
    if (
        flags["validation"]
        or flags["enrichment"]
        or flags["normalization"]
        or flags["audit"]
    ):
        return True
    else:
        return False


def _parse_flag_type(flag_string):
    errors = []
    if flag_string is None:
        return errors, {}

    result = {}
    for flag in flag_string.split(","):
        tokens = flag.split("_")
        if len(tokens) < 2:
            errors.append(f"Invalid flag: '{flag}'")
            continue
        field = "_".join(tokens[:-1])
        flag_val = tokens[-1]
        if (
            field not in DEFAULT_FIELDS
            and LABEL_AUDIT_MAP.get(field) not in DEFAULT_AUDITORS
        ):
            errors.append(f"Invalid flag: '{flag}'")
            continue
        if field not in result:
            result[field] = []
        result[field].append(flag_val)

    return errors, result


def build_export_result(pub, events, selected_flags, oai_id, mods_url):
    source = pub["meta"]["assigner"]["label"]
    try:
        pub_year = pub["publication"][0]["date"]
    except (IndexError, KeyError):
        # Ok. Publication may not have been published yet.
        pub_year = None
    pub_type = _get_url(pub, "publication")
    output_type = _get_url(pub, "output")
    # mods_url = urls[id]['original']
    flags = _get_flags(events, selected_flags)
    repo_url = _get_repo_url(pub)
    return {
        "record_id": oai_id,
        "source": source,
        "publication_year": pub_year,
        "publication_type": pub_type,
        "output_type": output_type,
        "mods_url": mods_url,
        "flags": flags,
        "repository_url": repo_url,
    }


def _get_url(publication, pub_type):
    assert (pub_type == "publication") or (pub_type == "output")
    markings_prefix = "https://id.kb.se/term/swepub/svep"
    swedish_list_prefix = "https://id.kb.se/term/swepub/swedishlist"
    output_type_re = r"^https://id\.kb\.se/term/swepub/[a-zA-Z_\-]+/[a-zA-Z_\-]+$"
    pub_type_re = r"^https://id\.kb\.se/term/swepub/[a-zA-Z_\-]+$"
    regex = pub_type_re
    if pub_type == "output":
        regex = output_type_re
    for gf in publication["instanceOf"]["genreForm"]:
        gf_id = gf["@id"]
        if gf_id.startswith(markings_prefix):
            continue
        if gf_id.startswith(swedish_list_prefix):
            continue
        m = re.match(regex, gf_id)
        if m is None:
            continue
        return m.group(0)
    return None


def _get_repo_url(publication):
    if "identifiedBy" not in publication:
        return None
    for pub_id in publication["identifiedBy"]:
        if pub_id["@type"] == "URI":
            return pub_id["value"]
    return None


def _get_flags(events, selected_flags):
    """Extract desired flags or all if none are selected."""
    result = {}
    validation_flags = {}
    enrichment_flags = {}
    normalization_flags = {}
    audit_flags = {}

    for field, checks in events["field_events"].items():
        validation_flags.update(_get_validation_flags(field, checks, selected_flags))
        enrichment_flags.update(_get_enrichment_flags(field, checks, selected_flags))
        normalization_flags.update(
            _get_normalization_flags(field, checks, selected_flags)
        )

    for auditor, checks in events["audit_events"].items():
        flag = _get_audit_flags(auditor, checks, selected_flags)
        if flag:
            if auditor in ENRICHING_AUDITORS:
                # auto_classify and add_oa go into enrichment flags
                enrichment_flags.update(flag)
            else:
                audit_flags.update(flag)

    if validation_flags:
        result["validation"] = validation_flags
    if enrichment_flags:
        result["enrichment"] = enrichment_flags
    if normalization_flags:
        result["normalization"] = normalization_flags
    if audit_flags:
        result["audit"] = audit_flags

    return result


def _get_validation_flags(field, checks, selected_flags):
    validation_flags = {}
    has_selection = has_selected_flags(selected_flags)
    for path, check in checks.items():
        validation_status = check["validation_status"]
        selected_validation_flags = []
        if field in selected_flags["validation"]:
            selected_validation_flags = selected_flags["validation"][field]
        if has_selection and validation_status not in selected_validation_flags:
            continue
        for flag_event in check["events"]:
            if flag_event["type"] != "validation":
                continue
            flag = {"path": path}
            if "value" in flag_event:
                flag["value"] = flag_event["value"]
            if _should_export_validation(
                has_selection, flag_event, selected_validation_flags
            ):
                if "code" in flag_event and "result" in flag_event:
                    if field not in validation_flags:
                        validation_flags[field] = []
                    flag["code"] = flag_event["code"]
                    flag["result"] = flag_event["result"]
                    validation_flags[field].append(flag)

    return validation_flags


def _should_export_validation(has_selection, flag_event, selected_validation_flags):
    should_export_result = (
        "result" in flag_event and flag_event["result"] in selected_validation_flags
    )
    # Export either if selected or no selection has been made
    return should_export_result or not has_selection


def _get_enrichment_flags(field, checks, selected_flags):
    return _get_flags_for_type(field, checks, selected_flags, "enrichment")


def _get_normalization_flags(field, checks, selected_flags):
    return _get_flags_for_type(field, checks, selected_flags, "normalization")


def _get_flags_for_type(field, checks, selected_flags, flag_type):
    flags = {}
    has_selection = has_selected_flags(selected_flags)
    for path, check in checks.items():
        status = check[f"{flag_type}_status"]
        selected_flags_for_type = []
        if field in selected_flags[flag_type]:
            selected_flags_for_type = selected_flags[flag_type][field]
        if has_selection and status not in selected_flags_for_type:
            continue
        for flag_event in check["events"]:
            if flag_event["type"] != flag_type:
                continue
            flag = {"path": path}
            if "initial_value" in flag_event:
                flag["old_value"] = flag_event["initial_value"]
            if "value" in flag_event:
                flag["new_value"] = flag_event["value"]
            if _should_export_simple(has_selection, status, selected_flags_for_type):
                if "code" in flag_event:
                    if field not in flags:
                        flags[field] = []
                    flag["code"] = flag_event["code"]
                    flags[field].append(flag)

    return flags


def _get_audit_flags(auditor, checks, selected_flags):
    flag_result = {}
    label = AUDIT_LABEL_MAP.get(auditor)
    selected_auditor_flags = selected_flags.get("audit").get(label, [])
    selected_auto_classify_flags = (
        selected_flags.get("enrichment").get(label, [])
        if auditor in ENRICHING_AUDITORS
        else []
    )

    choose_all = False
    if not has_selected_flags(selected_flags):
        choose_all = True

    if (
        not choose_all
        and not selected_auditor_flags
        and not selected_auto_classify_flags
    ):
        return flag_result

    if auditor in DEFAULT_AUDITORS:
        step = checks[0]
        result_value = None
        flag = {}

        if auditor in ENRICHING_AUDITORS:
            # AutoClassifier and OAAuditor are returned separately as they will be moved into enrichment category
            selected_flags = selected_auto_classify_flags
            if step["result"]:
                if "enriched" in selected_flags or choose_all:
                    result_value = "enriched"
            elif not step["result"]:
                if "unchanged" in selected_flags or choose_all:
                    result_value = "unchanged"
            if result_value:
                flag["result"] = result_value
                if step.get("code"):
                    flag["code"] = step.get("code")
                if step.get("value"):
                    if auditor == "OAAuditor":
                        added_oa = []
                        for oa_obj in step.get("value", []):
                            oa_info = {}
                            if oa_obj.get("uri"):
                                oa_info["uri"] = oa_obj.get("uri")
                            if len(oa_obj.get("usageAndAccessPolicy", [])) > 0:
                                if oa_obj.get("usageAndAccessPolicy")[0].get("@id"):
                                    oa_info["policy"] = oa_obj.get("usageAndAccessPolicy")[0].get("@id")
                            if len(oa_obj.get("hasNote", [])) > 0:
                                if oa_obj.get("hasNote")[0].get("@id"):
                                    oa_info["uriVersion"] = oa_obj.get("hasNote")[0].get("@id")
                            for meta in oa_obj.get("meta", []):
                                for source_consulted in meta.get("sourceConsulted", []):
                                    if source_consulted.get("uri"):
                                        oa_info["uriSource"] = source_consulted.get("uri")
                                        continue
                            if oa_info:
                                added_oa.append(oa_info)
                        flag["new_value"] = added_oa
                    else:
                        flag["new_value"] = step.get("value")
                if step.get("initial_value"):
                    flag["old_value"] = step.get("initial_value")
                flag_result[label] = [flag]
            return flag_result

        if auditor == "CreatorCountAuditor":
            step = checks[1]
            if step["result"]:
                if "valid" in selected_auditor_flags or choose_all:
                    # CreatorCountAuditor indicates valid if the result of the validation step is True
                    result_value = "valid"
            elif not step["result"]:
                if "invalid" in selected_auditor_flags or choose_all:
                    # and invalid if False
                    result_value = "invalid"

        elif auditor == "SwedishListAuditor":
            if step["result"] in selected_auditor_flags or choose_all:
                # SwedishListAuditor result value is a string that we don't translate
                result_value = step["result"]

        else:
            if step["result"]:
                if "invalid" in selected_auditor_flags or choose_all:
                    # other auditors indicate invalid if the result is True
                    result_value = "invalid"
            elif not step["result"]:
                if "valid" in selected_auditor_flags or choose_all:
                    # and valid if False
                    result_value = "valid"

        if result_value:
            flag_result[label] = {"result": result_value}

    return flag_result


def _should_export_simple(has_selection, status, selected_flags):
    return status in selected_flags or not has_selection


def get_offsets(limit, offset, total):
    """Return previous and next offset."""
    if limit is None:
        # Without an explicit limit, we return as much as possible (e.g. for export).
        limit = 999999
    if offset is None:
        offset = 0
    prev_offset = offset - limit
    if prev_offset < 0:
        prev_offset = None

    next_offset = offset + limit
    if next_offset >= total:
        next_offset = None

    return prev_offset, next_offset


def process_get_pagination_links(request, endpoint, limit, offset, total):
    """Return prev/next links given a search request."""
    prev_link = next_link = None
    (prev_offset, next_offset) = get_offsets(limit, offset, total)
    _base_url, (proto, _host, _port, _path, netloc) = get_base_url(request)
    args = {}
    for key, values in request.args.lists():
        args[key] = values
    if not endpoint:
        return None, None
    if prev_offset is not None:
        prev_link = _get_pagination_link(
            proto, netloc, endpoint, args, prev_offset
        )
    if next_offset is not None:
        next_link = _get_pagination_link(
            proto, netloc, endpoint, args, next_offset
        )
    return prev_link, next_link


def _get_pagination_link(proto, netloc, endpoint, args, offset):
    params = fragment = None
    expanded_args = []
    if "offset" not in args:
        args["offset"] = offset
    for key, values in args.items():
        if key == "offset":
            expanded_args.append(f"{key}={offset}")
            continue
        for value in values:
            expanded_args.append(f"{key}={value}")
    query = "&".join(expanded_args)
    return urlunparse((proto, netloc, endpoint, params, query, fragment))
