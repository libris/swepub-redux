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


def _validate_base_unicode(field):
    return validate_base_unicode(field.value), "unicode"


def validate_format(field):
    hit = isi_regex.fullmatch(field.value)
    return hit is not None, "format"


def validate_isi(field):
    success, code = _validate_base_unicode(field) or _validate_format(field)

    if success:
        field.validation_status = 'valid'
    else:
        field.events.append(make_event(type="validation", code=code, result="invalid", initial_value=field.value))
        field.validation_status = 'invalid'
