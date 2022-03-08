from pipeline.util import make_event


def validate_is_numeric(value):
    return (value.isnumeric() and int(value) > 0), "numeric"


def validate_creator_count(field):
    success, code = validate_is_numeric(field.value)

    if success:
        field.events.append(make_event(type="validation", code=code, result="valid", value=field.value))
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.events.append(make_event(type="validation", code=code, result="invalid", value=field.value))
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
