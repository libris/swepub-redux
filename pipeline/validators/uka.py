import re
from util import make_event

uka_regexp = re.compile('^[0-9]$|^[0-9]{3}$|^[0-9]{5}$')

def validate_uka(uka, path, events):
    hit = uka_regexp.fullmatch(uka)
    if hit is None:
        events.append(make_event("validation", "UKA", path, "format", "invalid", initial_value=uka))
        return False
    return True
