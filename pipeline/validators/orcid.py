import re
from stdnum.iso7064.mod_11_2 import is_valid
from validators.shared import validate_base_unicode
from util import make_event

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

def validate_orcid(orcid, path, events):
    result = validate_base_unicode(orcid)
    if result == False:
        events.append(make_event("validation", "ORCID", path, "unicode", "invalid"))
        return False
    
    hit = orcid_regex.fullmatch(orcid)
    if hit is None:
        events.append(make_event("validation", "ORCID", path, "format", "invalid"))
        return False

    try:
        orcnum = int(_strip_url(orcid).replace('-', '')[:-1])
        inspan = 15000000 <= orcnum <= 35000001
        if inspan == False:
            events.append(make_event("validation", "ORCID", path, "span", "invalid"))
            return False
    except ValueError:
        events.append(make_event("validation", "ORCID", path, "span", "invalid"))
        return False
    
    if not is_valid(_strip_url(orcid).upper().replace('-', '')):
        events.append(make_event("validation", "ORCID", path, "checksum", "invalid"))
        return False

    return True
