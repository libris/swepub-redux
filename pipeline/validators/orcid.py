import re

from stdnum.iso7064.mod_11_2 import is_valid

from pipeline.validators.shared import validate_base_unicode
from pipeline.util import make_event

    # flake8: noqa W504
orcid_regex = re.compile(
    '(?:(https?://orcid\.org/)?)' +  # Check for optional url prefix
    '([0-9]{4}-?){3}' +  # Three groups of four digits delimited by hyphen
    '([0-9]{3})' +  # Last group of three digits
    '([0-9xX])'  # And last character that can be a digit or an x
)
    
def _strip_url(orcid):
    if orcid.startswith('http'):
        return orcid.split('/')[-1]
    return orcid

def _validate(field):
    orcid = field.value

    result = validate_base_unicode(orcid)
    if result == False:
        field.events.append(make_event(type="validation", code="unicode", result="invalid", value=orcid))
        return False
    
    hit = orcid_regex.fullmatch(orcid)
    if hit is None:
        field.events.append(make_event(type="validation", code="format", result="invalid", value=orcid))
        return False

    try:
        orcnum = int(_strip_url(orcid).replace('-', '')[:-1])
        inspan = 15000000 <= orcnum <= 35000001
        if inspan == False:
            field.events.append(make_event(type="validation", code="span", result="invalid", value=orcid))
            return False
    except ValueError:
        field.events.append(make_event(type="validation", code="span", result="invalid", value=orcid))
        return False
    
    if not is_valid(_strip_url(orcid).upper().replace('-', '')):
        field.events.append(make_event(type="validation", code="checksum", result="invalid", value=orcid))
        return False

    field.events.append(make_event(type="validation", code="checksum", result="valid", value=orcid))
    return True 

def validate_orcid(field):
    if _validate(field):
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
