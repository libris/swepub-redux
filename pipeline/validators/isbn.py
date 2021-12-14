import re
from log import log_for_OAI_id
from stdnum.isbn import is_valid, compact

# flake8: noqa W504
isbn13_regex = re.compile(
    '97[89][- ]?' +  # Optional prefix for ISBN13
    '([0-9]+?[- ]?){3}' +  # Accept three middle fields with varying lengths
    '[0-9]')

# flake8: noqa W504
isbn10_regex = re.compile(
    '([0-9]{1,6}?[- ]?){3}' +  # Accept three middle fields with varying lengths
    '[0-9xX]')

def _validate_format(isbn, id):
    hit13 = isbn13_regex.fullmatch(isbn)
    if hit13 and len(compact(isbn)) == 13:
        return True
    hit10 = isbn10_regex.fullmatch(isbn)
    if hit10 and len(compact(isbn)) == 10:
        return True
    log_for_OAI_id(id, 'ISBN validation failed: format')
    return False

def _validate_checksum(isbn, id):
    if is_valid(isbn):
        return True
    log_for_OAI_id(id, 'ISBN validation failed: checksum')
    return False

def validate_isbn(isbn, id):
    result = _validate_format(isbn, id)
    result &= _validate_checksum(isbn, id)
    return result