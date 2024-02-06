import re
from pipeline.util import make_event, Validation, Enrichment

ssif_regexp = re.compile("^[0-9]$|^[0-9]{3}$|^[0-9]{5}$")


def validate_ssif(field):
    ssif = field.value

    hit = ssif_regexp.fullmatch(ssif)
    if hit is None:
        field.events.append(
            make_event(event_type="validation", code="format", result="invalid", value=ssif)
        )
        field.validation_status = Validation.INVALID
        return False
    field.events.append(
        make_event(event_type="validation", code="format", result="valid", value=ssif)
    )
    field.validation_status = Validation.VALID
    if not field.is_enriched():
        field.enrichment_status = Enrichment.UNCHANGED
    return True
