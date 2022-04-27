from pipeline.util import make_event, Validation, Enrichment


def validate_is_numeric(value):
    return (value.isnumeric() and int(value) > 0), "numeric"


def validate_creator_count(field):
    success, code = validate_is_numeric(field.value)

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
