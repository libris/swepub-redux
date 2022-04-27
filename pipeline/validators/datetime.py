from datetime import datetime

from pipeline.validators.shared import validate_base_unicode
from pipeline.util import make_event, Validation, Enrichment


def validate_format(dt):
    """Valid date formats are YYYY and YYYY-MM-DD, as specified in Swepub MODS specification."""
    if isinstance(dt, str):
        if not validate_base_unicode(dt):
            # field.events.append(make_event(type="validation", code="unicode", result="invalid", value=dt))
            return False, "unicode"

        try:
            datetime.strptime(dt, "%Y")
            return True, "format"
        except ValueError:
            try:
                datetime.strptime(dt, "%Y-%m-%d")
                return True, "format"
            except ValueError:
                return False, "format"

    return False, "format"


def validate_date_time(field):
    success, code = validate_format(field.value)

    if success:
        field.events.append(
            make_event(event_type="validation", code=code, result="valid", value=field.value)
        )
        field.validation_status = Validation.VALID
        if not field.is_enriched():
            field.enrichment_status = Enrichment.UNCHANGED
    else:
        field.events.append(
            make_event(event_type="validation", code=code, result="invalid", value=field.value)
        )
        field.validation_status = Validation.INVALID
        if field.is_enriched():
            field.enrichment_status = Enrichment.UNSUCCESSFUL
