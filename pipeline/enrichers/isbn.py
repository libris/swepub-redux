import re
from stdnum.isbn import compact
from util import update_at_path, make_event

# flake8: noqa W504
isbn_regex = re.compile(
    '(?<![-./0-9])' +  # Check that not preceded by specific characters
    '(97[89][-]?)?' +  # Optional prefix for ISBN13
    '([0-9]+[-]?){3}' +  # Accept three middle fields with varying lengths
    '([0-9xX])' +  # Find control number
    '(?:(?![-0-9]))'  # Make sure the code isnt followed by a number or hyphen
)

def recover_isbn(isbn, body, path, id, events):
    answ = isbn_regex.finditer(isbn)
    res = []
    for pattern in answ:
        p = compact(pattern.group())
        if len(p) == 10 or len(p) == 13:
            res.append(pattern.group())
    
    if not res:
        return
    
    if res[0] != isbn:
        update_at_path(body, path, res[0])
        events.append(make_event("enrichment", "ISBN", path, "split", res[0], initial_value=isbn))
    