import re

from stdnum.iso7064.mod_11_2 import is_valid

from pipeline.validators.shared import validate_base_unicode
from pipeline.util import make_event

    # flake8: noqa W504
orcid_regex = re.compile(
    r'(?:(https?://orcid\.org/)?)' +  # Check for optional url prefix
    '([0-9]{4}-?){3}' +  # Three groups of four digits delimited by hyphen
    '([0-9]{3})' +  # Last group of three digits
    '([0-9xX])'  # And last character that can be a digit or an x
)
 

def strip_url(orcid):
    if orcid.startswith('http'):
        return orcid.split('/')[-1]
    return orcid


def validate_unicode(field):
    result = validate_base_unicode(field.value)
    if result:
        return True, "unicode"
    else:
        field.events.append(make_event(type="validation", code="unicode", result="invalid", value=field.value))
        return False, "unicode"


def validate_format(field):
    hit = orcid_regex.fullmatch(field.value)
    if hit:
        return True, "format"
    else:
        field.events.append(make_event(type="validation", code="format", result="invalid", value=field.value))
        return False, "format"


def validate_span(field):
    try:
        orcnum = int(strip_url(field.value).replace('-', '')[:-1])
        inspan = 15000000 <= orcnum <= 35000001
        if inspan:
            return True, "span"
        else:
            field.events.append(make_event(type="validation", code="span", result="invalid", value=field.value))
            return False, "span"
    except ValueError:
        field.events.append(make_event(type="validation", code="span", result="invalid", value=field.value))
        return False, "span"


def validate_checksum(field):
    if is_valid(strip_url(field.value).upper().replace('-', '')):
        return True, "checksum"
    else:
        field.events.append(make_event(type="validation", code="checksum", result="invalid", value=field.value))
        return False, "checksum"


def validate_orcid(field):
    success, code = validate_unicode(field) or validate_format(field) or validate_span(field) or validate_checksum(field)

    if success:
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
    return success, code
