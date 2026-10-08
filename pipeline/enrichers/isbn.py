import re

from stdnum.isbn import compact

from pipeline.util import update_at_path, add_sibling_at_path, make_event, FieldMeta, Enrichment, unicode_translate

# flake8: noqa W504
isbn_regex = re.compile(
    "(?<![-./0-9])"
    + "(97[89][-]?)?"  # Check that not preceded by specific characters
    + "([0-9]+[-]?){3}"  # Optional prefix for ISBN13
    + "([0-9xX])"  # Accept three middle fields with varying lengths
    + "(?:(?![-0-9]))"  # Find control number  # Make sure the code isn't followed by a number or hyphen
)


def recover_isbn(body, field):
    original = field.value
    isbn = field.value
    path = field.path
    created_fields = []

    translated = unicode_translate(isbn)
    if translated != isbn:
        isbn = translated
        update_at_path(body, path, isbn)
        field.events.append(
            make_event(
                event_type="enrichment",
                code="unicode",
                value=isbn,
                initial_value=original,
                result="enriched",
            )
        )
        field.enrichment_status = Enrichment.ENRICHED
        field.value = isbn

    answ = isbn_regex.finditer(isbn)
    res = []
    for pattern in answ:
        p = compact(pattern.group())
        if len(p) == 10 or len(p) == 13:
            res.append(pattern.group())

    if not res:
        return

    if len(res) > 0:
        if res[0] != isbn:
            update_at_path(body, path, res[0])
            field.value = res[0]
            field.enrichment_status = Enrichment.ENRICHED
            field.events.append(
                make_event(
                    event_type="enrichment",
                    code="recovery",
                    value=res[0],
                    initial_value=isbn,
                    result="enriched",
                )
            )

        if len(res) > 1:
            for found_value in res[1:]:
                field.events.append(
                    make_event(
                        event_type="enrichment",
                        code="split",
                        value=found_value,
                        initial_value=isbn,
                        result="enriched",
                    )
                )
                new_path = add_sibling_at_path(body, path, type="ISBN", value=found_value)
                created_fields.append(
                    FieldMeta(path=new_path, id_type=field.id_type, value=found_value)
                )

    if field.enrichment_status != Enrichment.ENRICHED:
        field.enrichment_status = Enrichment.UNSUCCESSFUL

    return created_fields
