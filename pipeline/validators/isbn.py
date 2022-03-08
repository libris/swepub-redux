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
    success, code = validate_format(field.value) or validate_checksum(field.value)

    if success:
        field.events.append(make_event(type="validation", code=code, result="valid", initial_value=field.value))
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.events.append(make_event(type="validation", code=code, result="invalid", initial_value=field.value))
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
