import re
from stdnum.issn import is_valid
from validators.shared import remote_verification
from util import make_event

issn_regex = re.compile('[0-9]{4}-?[0-9]{3}[0-9xX]')
    
def validate_issn(issn, path, session, events, harvest_cache):
    if issn is not None and isinstance(issn, str):
        hit = issn_regex.fullmatch(issn)
        if hit is None:
            return False

    if not is_valid(issn):
        events.append(make_event("validation", "ISSN", path, "checksum", "invalid"))
        return False

    if harvest_cache['issn'].get(issn, 0) or harvest_cache['id'].get(issn, 0):
        return True

    if not remote_verification(f'https://portal.issn.org/resource/ISSN/{issn}?format=json', session):
        events.append(make_event("validation", "ISSN", path, "remote", "invalid"))
        return False

    harvest_cache['id'][issn] = 1
    return True
