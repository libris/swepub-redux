import re
from log import log_for_OAI_id
from validators.shared import validate_base_unicode

# flake8: noqa W504
isi_regex = re.compile(
    '((000)[0-9]{12})' +  # 000 prefix contains only numbers
    '|' +  # Or
    '(([Aa]19)' +  # Prefix A19 followed by
    '[0-9a-zA-Z]{12})'  # Allows 0-9 and A-Z for the following 12 characters
)

def validate_isi(isi):
    result = validate_base_unicode(isi)
    if result == False:
        #log_for_OAI_id(id, 'ISI validation failed: unicode')
        return False
    
    hit = isi_regex.fullmatch(isi)
    if hit is None:
        #log_for_OAI_id(id, 'ISI validation failed: format')
        return False
    return True
