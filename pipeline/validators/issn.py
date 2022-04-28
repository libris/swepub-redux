import re

from stdnum.issn import is_valid
from stdnum.issn import format as issn_format

from pipeline.validators.shared import remote_verification
from pipeline.util import make_event, Validation, Enrichment

issn_regex = re.compile("[0-9]{4}-?[0-9]{3}[0-9xX]")


def validate_format(issn, session=None, harvest_cache=None):
    if issn is not None and isinstance(issn, str):
        hit = issn_regex.fullmatch(issn)
        if hit is None:
            return False, "format"
        return True, "format"


def validate_checksum(issn, session=None, harvest_cache=None):
    return is_valid(issn), "checksum"


def validate_cache_or_remote(issn, session=None, harvest_cache=None):
    # Formatting/normalizing the ISSN doesn't change validity, it just helps us avoid cache misses,
    # as the static list of ISSNs should have them correctly formatted.
    formatted_issn = issn_format(issn)

    if harvest_cache:
        if harvest_cache["issn_static"].get(formatted_issn, 0) or harvest_cache["issn_new"].get(
            issn, 0
        ):
            return True, "remote.cache"

    if session and not remote_verification(
        f"https://portal.issn.org/resource/ISSN/{issn}?format=json", session
    ):
        return False, "remote"

    if harvest_cache:
        harvest_cache["issn_new"][issn] = 1
    return True, "remote"


def validate_issn(field, session=None, harvest_cache=None):
    if field.validation_status == Validation.INVALID and field.enrichment_status in [
        Enrichment.UNCHANGED,
        Enrichment.UNSUCCESSFUL,
    ]:
        return

    for validator in [validate_format, validate_checksum, validate_cache_or_remote]:
        success, code = validator(field.value, session, harvest_cache)
        if not success:
            field.events.append(
                make_event(event_type="validation", code=code, result="invalid", value=field.value)
            )
            field.validation_status = Validation.INVALID
            if field.is_enriched():
                field.enrichment_status = Enrichment.UNSUCCESSFUL
            return
    field.events.append(
        make_event(event_type="validation", code=code, result="valid", value=field.value)
    )
    field.validation_status = Validation.VALID
    if not field.is_enriched():
        field.enrichment_status = Enrichment.UNCHANGED
