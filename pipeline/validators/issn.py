import re
from stdnum.issn import is_valid
from log import log_for_OAI_id
from validators.shared import validate_base_unicode, remote_verification
from util import make_event

issn_regex = re.compile('[0-9]{4}-?[0-9]{3}[0-9xX]')
    
def validate_issn(issn, path, session, events):
    if issn is not None and isinstance(issn, str):
        hit = issn_regex.fullmatch(issn)
        if hit is None:
            return False

    if not is_valid(issn):
        events.append(make_event("validation", "ISSN", path, "checksum", "invalid"))
        return False

    if not remote_verification(f'https://portal.issn.org/resource/ISSN/{issn}?format=json', session):
        events.append(make_event("validation", "ISSN", path, "remote", "invalid"))
        return False

    return True