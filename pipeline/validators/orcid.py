import re
from stdnum.iso7064.mod_11_2 import is_valid
from log import log_for_OAI_id
from validators.shared import validate_base_unicode

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

def validate_orcid(orcid):
    result = validate_base_unicode(orcid)
    if result == False:
        #log_for_OAI_id(id, 'ORCID validation failed: unicode')
        return False
    
    hit = orcid_regex.fullmatch(orcid)
    if hit is None:
        #log_for_OAI_id(id, 'ORCID validation failed: format')
        return False

    try:
        orcnum = int(_strip_url(orcid).replace('-', '')[:-1])
        inspan = 15000000 <= orcnum <= 35000001
        if inspan == False:
            #log_for_OAI_id(id, 'ORCID validation failed: span')
            return False
    except ValueError:
        #log_for_OAI_id(id, 'ORCID validation failed: span')
        return False
    
    if not is_valid(_strip_url(orcid).upper().replace('-', '')):
        #log_for_OAI_id(id, 'ORCID validation failed: checksum')
        return False

    return True
