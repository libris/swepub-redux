import re

from stdnum.isbn import is_valid, compact

from pipeline.util import make_event


# flake8: noqa W504
isbn13_regex = re.compile(
    "97[89][- ]?"
    + "([0-9]+?[- ]?){3}"  # Optional prefix for ISBN13
    + "[0-9]"  # Accept three middle fields with varying lengths
)

# flake8: noqa W504
isbn10_regex = re.compile(
    "([0-9]{1,6}?[- ]?){3}" + "[0-9xX]"  # Accept three middle fields with varying lengths
)


def validate_format(isbn):
    hit13 = isbn13_regex.fullmatch(isbn)
    if hit13 and len(compact(isbn)) == 13:
        return True, "format"
    hit10 = isbn10_regex.fullmatch(isbn)
    if hit10 and len(compact(isbn)) == 10:
        return True, "format"
    return False, "format"


def validate_checksum(isbn):
    return is_valid(isbn), "checksum"


def validate_isbn(field):
    if field.validation_status == "invalid" and field.enrichment_status in [
        "unchanged",
        "unsuccessful",
    ]:
        return

    for validator in [validate_format, validate_checksum]:
        success, code = validator(field.value)
        if not success:
            field.events.append(
                make_event(event_type="validation", code=code, result="invalid", value=field.value)
            )
            field.validation_status = "invalid"
            if field.is_enriched():
                field.enrichment_status = "unsuccessful"
            return
    field.events.append(
        make_event(event_type="validation", code=code, result="valid", value=field.value)
    )
    field.validation_status = "valid"
    if not field.is_enriched():
        field.enrichment_status = "unchanged"
