import re
from util import make_event

uka_regexp = re.compile('^[0-9]$|^[0-9]{3}$|^[0-9]{5}$')

def validate_uka(field):
    uka = field.value

    hit = uka_regexp.fullmatch(uka)
    if hit is None:
        field.events.append(make_event(type="validation", code="format", result="invalid", value=uka))
        field.validation_status = 'invalid'
        return False
    field.events.append(make_event(type="validation", code="format", result="valid", value=uka))
    field.validation_status = 'valid'
    if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    return True
