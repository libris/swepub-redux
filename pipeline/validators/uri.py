from validators.shared import validate_base_unicode
from util import make_event


def validate_uri(field):
    if validate_base_unicode(field.value):
        field.events.append(make_event(type="validation", code="unicode", result="valid", value=field.value))
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.events.append(make_event(type="validation", code="unicode", result="invalid", value=field.value))
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
