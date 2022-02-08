from util import make_event

def validate_creator_count(field):
    if field.value.isnumeric() and int(field.value) > 0:
        field.events.append(make_event(type="validation", code="numeric", result="valid", value=field.value))
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.events.append(make_event(type="validation", code="numeric", result="invalid", value=field.value))
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'

