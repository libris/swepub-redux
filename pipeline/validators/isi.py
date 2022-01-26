import re
from validators.shared import validate_base_unicode
from util import make_event

# flake8: noqa W504
isi_regex = re.compile(
    '((000)[0-9]{12})' +  # 000 prefix contains only numbers
    '|' +  # Or
    '(([Aa]19)' +  # Prefix A19 followed by
    '[0-9a-zA-Z]{12})'  # Allows 0-9 and A-Z for the following 12 characters
)

def validate_isi(isi, path, events):
    result = validate_base_unicode(isi)
    if result == False:
        events.append(make_event("validation", "ISI", path, "unicode", "invalid"))
        return False
    
    hit = isi_regex.fullmatch(isi)
    if hit is None:
        events.append(make_event("validation", "ISI", path, "format", "invalid"))
        return False
    return True
