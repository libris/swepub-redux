import re
from pipeline.util import (
    update_at_path,
    add_sibling_at_path,
    unicode_translate,
    make_event,
    FieldMeta,
    Enrichment
)

# flake8: noqa W504
issn_regex = re.compile(
    r"(?:(?<!(\d[^0-9-])))"
    + r"(?:(?<![0-9-]))"  # Check that not preceded by digit or and not number or hyphen
    + r"([0-9]{4})"  # Check that not preceded by digit
    + r"(-?)"  # Four consecutive numbers
    + r"[^0-9]*"  # Accept a correct delimiter if one exists
    + r"([0-9]{3})"  # Any number of non-digit signs as delimiter
    + r"[^0-9]??"  # Three consecutive numbers
    + r"([0-9xX])"  # optional non-numerical sign before the control number
    + r"(?:(?![0-9-]))"  # Control number
    + r"(?:(?![ ]\d))"  # Make sure the code isn't followed by a number or hyphen  # Check that not followed by non digit or hyphen and digit
)


def recover_issn(body, field, cached_paths):
    issn = field.value
    path = field.path
    created_fields = []

    translated = unicode_translate(issn)
    if translated != issn:
        initial = issn
        issn = translated
        update_at_path(body, path, issn, cached_paths)
        field.events.append(
            make_event(
                event_type="enrichment",
                code="unicode",
                value=issn,
                initial_value=initial,
                result="enriched",
            )
        )
        field.enrichment_status = Enrichment.ENRICHED
        field.value = issn

    answ = issn_regex.findall(issn)
    # Skip first element in part since it's empty or contains non wanted delimiter
    recovered = ["".join(part[1:]) for part in answ]

    if len(recovered) > 0:
        if recovered[0] != issn:
            field.events.append(
                make_event(
                    event_type="enrichment",
                    code="recovery",
                    value=recovered[0],
                    initial_value=issn,
                    result="enriched",
                )
            )
            update_at_path(body, path, recovered[0], cached_paths)
            field.enrichment_status = Enrichment.ENRICHED
            field.value = recovered[0]

        if len(recovered) > 1:
            for found_value in recovered[1:]:
                field.events.append(
                    make_event(
                        event_type="enrichment",
                        code="split",
                        value=found_value,
                        initial_value=issn,
                        result="enriched",
                    )
                )
                new_path = add_sibling_at_path(body, path, type="ISSN", value=found_value, cached_paths=cached_paths)
                created_fields.append(
                    FieldMeta(path=new_path, id_type=field.id_type, value=found_value)
                )

    if field.enrichment_status != Enrichment.ENRICHED:
        field.enrichment_status = Enrichment.UNSUCCESSFUL
    return created_fields
