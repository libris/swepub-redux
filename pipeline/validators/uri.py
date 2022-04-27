from pipeline.validators.shared import validate_base_unicode
from pipeline.util import make_event, Validation, Enrichment


def validate_uri(field):
    if validate_base_unicode(field.value):
        field.events.append(
            make_event(event_type="validation", code="unicode", result="valid", value=field.value)
        )
        field.validation_status = Validation.VALID
        if not field.is_enriched():
            field.enrichment_status = Enrichment.UNCHANGED
        return True
    else:
        field.events.append(
            make_event(event_type="validation", code="unicode", result="invalid", value=field.value)
        )
        field.validation_status = Validation.INVALID
        if field.is_enriched():
            field.enrichment_status = Enrichment.UNSUCCESSFUL
        return False
