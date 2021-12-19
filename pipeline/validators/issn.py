import re
from stdnum.issn import is_valid
from log import log_for_OAI_id
from validators.shared import validate_base_unicode, remote_verification

issn_regex = re.compile('[0-9]{4}-?[0-9]{3}[0-9xX]')
    
def validate_issn(issn, id, session):
    if issn is not None:
        hit = issn_regex.fullmatch(issn)
        if hit is None:
            return False

    if not is_valid(issn):
        log_for_OAI_id(id, 'ISSN validation failed: checksum')
        return False

    if not remote_verification(f'https://portal.issn.org/resource/ISSN/{issn}?format=json', session):
        log_for_OAI_id(id, 'ISSN validation failed: remote')
        return False

    return True