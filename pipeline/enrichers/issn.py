import re
from util import update_at_path, unicode_translate, make_event

# flake8: noqa W504
issn_regex = re.compile(
    '(?:(?<!(\d[^0-9-])))' +  # Check that not preceded by digit or and not number or hyphen
    '(?:(?<![0-9-]))' +       # Check that not preceded by digit
    '([0-9]{4})' +            # Four consecutive numbers
    '(-?)' +                  # Accept a correct delimiter if one exists
    '[^0-9]*' +               # Any number of non-digit signs as delimiter
    '([0-9]{3})' +            # Three consecutive numbers
    '[^0-9]??' +              # optional non-numerical sign before the control number
    '([0-9xX])' +             # Control number
    '(?:(?![0-9-]))' +        # Make sure the code isn't followed by a number or hyphen
    '(?:(?![ ]\d))'           # Check that not followed by non digit or hyphen and digit
)

def recover_issn(issn, body, path, id, events):
    translated = unicode_translate(issn)
    if translated != issn:
        issn = translated
        update_at_path(body, path, issn)
        events.append(make_event("enrichment", "ISSN", path, "unicode", issn))
        
    answ = issn_regex.findall(issn)
    # Skip first element in part since it's empty or contains non wanted delimiter
    recovered = [''.join(part[1:]) for part in answ]
    if len(recovered) > 0 and recovered[0] != issn:
        events.append(make_event("enrichment", "ISSN", path, "split", recovered))
        update_at_path(body, path, recovered[0])
