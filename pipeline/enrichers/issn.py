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

def recover_issn(body, field):
    issn = field.value
    path = field.path

    translated = unicode_translate(issn)
    if translated != issn:
        initial = issn
        issn = translated
        update_at_path(body, path, issn)
        field.events.append(make_event(type="enrichment", code="unicode", value=issn, initial_value=initial, result="enriched"))
        field.enrichment_status = 'enriched'
        field.value = issn

    answ = issn_regex.findall(issn)
    # Skip first element in part since it's empty or contains non wanted delimiter
    recovered = [''.join(part[1:]) for part in answ]
    if len(recovered) > 0 and recovered[0] != issn:
        field.events.append(make_event(type="enrichment", code="split", value=recovered[0], initial_value=issn, result="enriched"))
        update_at_path(body, path, recovered[0])
        field.enrichment_status = 'enriched'
        field.value = recovered[0]

    if field.enrichment_status != 'enriched':
        field.enrichment_status = 'unsuccessful'
