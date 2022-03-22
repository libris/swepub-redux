import re

from pipeline.validators.shared import validate_base_unicode

from pipeline.util import make_event

# flake8: noqa W504
isi_regex = re.compile(
    "((000)[0-9]{12})"
    + "|"  # 000 prefix contains only numbers
    + "(([Aa]19)"  # Or
    + "[0-9a-zA-Z]{12})"  # Prefix A19 followed by  # Allows 0-9 and A-Z for the following 12 characters
)


def _validate_base_unicode(field):
    return validate_base_unicode(field.value), "unicode"


def validate_format(field):
    hit = isi_regex.fullmatch(field.value)
    return hit is not None, "format"


def validate_isi(field):
    if field.validation_status == "invalid" and field.enrichment_status in [
        "unchanged",
        "unsuccessful",
    ]:
        return

    for validator in [_validate_base_unicode, validate_format]:
        success, code = validator(field)
        if not success:
            field.events.append(
                make_event(event_type="validation", code=code, result="invalid", value=field.value)
            )
            field.validation_status = "invalid"
            return
    field.validation_status = "valid"
