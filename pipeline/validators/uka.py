import re
from log import log_for_OAI_id
from validators.shared import validate_base_unicode

uka_regexp = re.compile('^[0-9]$|^[0-9]{3}$|^[0-9]{5}$')

def validate_uka(uka):
    hit = uka_regexp.fullmatch(uka)
    if hit is None:
        #log_for_OAI_id(id, 'UKA validation failed: format')
        return False
    return True
