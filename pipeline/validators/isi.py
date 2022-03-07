import re

from pipeline.validators.shared import validate_base_unicode

from pipeline.util import make_event

# flake8: noqa W504
isi_regex = re.compile(
    '((000)[0-9]{12})' +  # 000 prefix contains only numbers
    '|' +  # Or
    '(([Aa]19)' +  # Prefix A19 followed by
    '[0-9a-zA-Z]{12})'  # Allows 0-9 and A-Z for the following 12 characters
)

def validate_isi(field):
    isi = field.value
    result = validate_base_unicode(isi)
    if result == False:
        field.events.append(make_event(type="validation", code="unicode", result="invalid", initial_value=isi))
        field.validation_status = 'invalid'
        return False, "unicode"
    
    hit = isi_regex.fullmatch(isi)
    if hit is None:
        field.events.append(make_event(type="validation", code="format", result="invalid", initial_value=isi))
        field.validation_status = 'invalid'
        return False, "format"
    else:
        field.events.append(make_event(type="validation", code="format", result="valid", initial_value=isi))
        field.validation_status = 'valid'
        return True, "format"
