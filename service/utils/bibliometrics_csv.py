from io import StringIO
import csv

CREATOR_FIELDS = [
    "familyName",
    "givenName",
    "localId",
    "localIdBy",
    "ORCID",
    "affiliation",
    "freetext_affiliations",
]

# maps column names to use in result csv file to labels in api result json
column_name_label_dict = {
    "record_id": "recordId",
    "source": "source",
    "duplicate_ids": "duplicateIds",
    "publication_count": "publicationCount",
    "creator_count": "creatorCount",
    "creators": "creators",
    "title": "title",
    "summary": "summary",
    "output_types": "outputTypes",
    "content_marking": "contentMarking",
    "publication_year": "publicationYear",
    "publication_status": "publicationStatus",
    "DOI": "DOI",
    "ISBN": "ISBN",
    "ISI_id": "ISI",
    "scopus_id": "scopusId",
    "pubmed_id": "PMID",
    "open_access": "openAccess",
    "open_access_version": "openAccessVersion",
    "archive_URI": "archiveURI",
    "electronic_locator": "electronicLocator",
    "one_digit_topics": "oneDigitTopics",
    "three_digit_topics": "threeDigitTopics",
    "five_digit_topics": "fiveDigitTopics",
    "keywords": "keywords",
    "languages": "languages",
    "publication_channel": "publicationChannel",
    "publisher": "publisher",
    "ISSN": "ISSN",
    "swedish_list": "swedishList",
    "series": "series",
    "series_title": "seriesTitle",
    "autoclassified": "autoclassified",
    "DOAJ": "DOAJ",
}


def export(api_result_data, chosen_fields, flavor="csv", total=0):
    delimiter = ","
    if flavor == "tsv":
        delimiter = "\t"

    column_names = []
    include_all = False

    if len(chosen_fields) == 0:
        # include all fields as default
        include_all = True

    elif (
        any(cf in chosen_fields for cf in CREATOR_FIELDS)
        and "creators" not in chosen_fields
    ):
        chosen_fields.append("creators")

    for column_name, label in column_name_label_dict.items():
        if include_all or label in chosen_fields:
            column_names.append(column_name)

    rows = [_get_row(api_result_data, column_names, include_all, chosen_fields, flavor)]
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=column_names, delimiter=delimiter)
    if total == 0:
        writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _get_row(data, column_names, include_all, chosen_fields, flavor="csv"):
    row = dict()

    for column_name in column_names:
        label = column_name_label_dict.get(column_name)
        if column_name == "creators":
            value = _get_creator_string(data, include_all, chosen_fields, flavor)
        elif column_name == "open_access":
            value = "true" if data.get("openAccess", False) else "false"
        elif column_name in (
            "DOI",
            "ISBN",
            "ISSN",
            "keywords",
            "source",
            "output_types",
        ):
            value = _make_string_from_list(data.get(label, []), flavor)
        elif column_name in (
            "one_digit_topics",
            "three_digit_topics",
            "five_digit_topics",
        ):
            value = _make_string_from_list(
                data.get("subjects", {}).get(label, []), flavor
            )
        elif column_name == "duplicate_ids":
            value = _make_string_from_list(data.get(label, []), flavor)
        elif column_name == "languages":
            value = _make_string_from_list(data.get("languages", []), flavor)
        else:
            value = data.get(label, "") if data.get(label) is not None else ""
            value = f"{value}"
        row.update({column_name: value})
    return row


def _get_creator_string(data, include_all, chosen_fields, flavor="csv"):
    result_string = ""
    creators = data.get("creators", {})

    include_every_part = False
    # include all subparts as default,
    # if include_all
    # or if 'creators' has been chosen but no subfields have been chosen
    if include_all or all(field not in chosen_fields for field in CREATOR_FIELDS):
        include_every_part = True

    for index, c in enumerate(creators):

        creator_parts = []
        for field in CREATOR_FIELDS:
            if include_every_part or field in chosen_fields:
                if field == "freetext_affiliations":
                    creator_parts.append(_get_freetext_affiliations(c.get(field)))
                else:
                    creator_parts.append(
                        c.get(field, "") if c.get(field) is not None else ""
                    )

        creator_substring = _make_string_from_list(creator_parts, flavor)

        if index == 0:
            result_string = creator_substring
        else:
            result_string = f"{result_string};{creator_substring}"

    return result_string


def _make_string_from_list(creator_parts, flavor="csv"):
    delim = ","
    if flavor == "tsv":
        delim = "\t"
    result_string = ""
    for index, item in enumerate(creator_parts):
        if index == 0:
            result_string = item
        else:
            result_string = f"{result_string}{delim}{item}"
    return result_string


def _get_info_comment(query, handled_at):
    date_part = ""
    query_part = ""
    if handled_at:
        date_part = f"Query handled at {handled_at}. "
    if query:
        query_part = f"Query parameters: {query}"
    if handled_at or query:
        return f"# Swepub bibliometric export. {date_part}{query_part}\n"
    else:
        return ""


def _get_freetext_affiliations(affiliations):
    """Get a flat textual representation of an affiliation tree
    We use comma and space for nodes in a branch and pipe between branches."""
    if not affiliations:
        return ""
    formatted_affils = []
    for affil in affiliations:
        formatted_affils.append(", ".join(affil))
    return "|".join(formatted_affils)
