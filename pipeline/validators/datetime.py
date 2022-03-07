from datetime import datetime

from pipeline.validators.shared import validate_base_unicode
from pipeline.util import make_event


def _validate(field):
    dt = field.value
    """Valid date formats are YYYY and YYYY-MM-DD, as specified in Swepub MODS specification.
    """
    if isinstance(dt, str):
        if not validate_base_unicode(dt):
            field.events.append(make_event(type="validation", code="unicode", result="invalid", value=dt))
            return False

        try:
            datetime.strptime(dt, '%Y')
            return True
        except ValueError:
            try:
                datetime.strptime(dt, '%Y-%m-%d')
                return True
            except ValueError:
                field.events.append(make_event(type="validation", code="format", result="invalid", value=dt))
                return False

    field.events.append(make_event(type="validation", code="format", result="invalid", value=dt))
    return False


def validate_date_time(field):
    if _validate(field):
        field.events.append(make_event(type="validation", code="format", result="valid", value=field.value))
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
