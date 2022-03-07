import re

from stdnum.isbn import is_valid, compact

from pipeline.util import make_event


# flake8: noqa W504
isbn13_regex = re.compile(
    '97[89][- ]?' +  # Optional prefix for ISBN13
    '([0-9]+?[- ]?){3}' +  # Accept three middle fields with varying lengths
    '[0-9]')

# flake8: noqa W504
isbn10_regex = re.compile(
    '([0-9]{1,6}?[- ]?){3}' +  # Accept three middle fields with varying lengths
    '[0-9xX]')


def validate_format(field):
    isbn, path = field.value, field.path
    hit13 = isbn13_regex.fullmatch(isbn)
    if hit13 and len(compact(isbn)) == 13:
        return True, "format"
    hit10 = isbn10_regex.fullmatch(isbn)
    if hit10 and len(compact(isbn)) == 10:
        return True, "format"
    field.events.append(make_event(type="validation", code="format", result="invalid", initial_value=isbn))
    return False, "format"


def validate_checksum(field):
    isbn, path = field.value, field.path
    if is_valid(isbn):
        field.events.append(make_event(type="validation", code="checksum", result="valid", initial_value=field.value))
        return True, "checksum"
    field.events.append(make_event(type="validation", code="checksum", result="invalid", initial_value=isbn))
    return False, "checksum"


def validate_isbn(field):
    if validate_format(field) and validate_checksum(field):
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
