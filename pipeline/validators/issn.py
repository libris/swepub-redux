import re

from stdnum.issn import is_valid
from stdnum.issn import format as issn_format

from pipeline.validators.shared import remote_verification
from pipeline.util import make_event

issn_regex = re.compile('[0-9]{4}-?[0-9]{3}[0-9xX]')


def validate_format(field):
    issn = field.value
    if issn is not None and isinstance(issn, str):
        hit = issn_regex.fullmatch(issn)
        if hit is None:
            field.events.append(make_event(type="validation", code="format", result="invalid", value=issn))
            return False, "format"
        return True, "format"


def validate_checksum(field):
    issn = field.value
    if not is_valid(issn):
        field.events.append(make_event(type="validation", code="checksum", result="invalid", value=issn))
        return False, "checksum"
    return True, "checksum"


def validate_cache_or_remote(field, session=None, harvest_cache=None):
    issn = field.value
    # Formatting/normalizing the ISSN doesn't change validity, it just helps us avoid cache misses,
    # as the static list of ISSNs should have them correctly formatted.
    formatted_issn = issn_format(issn)

    if harvest_cache:
        if harvest_cache['issn_static'].get(formatted_issn, 0) or harvest_cache['issn_new'].get(issn, 0):
            field.events.append(make_event(type="validation", code="remote.cache", result="valid", value=issn))
            return True, "remote.cache"

    if session and not remote_verification(f'https://portal.issn.org/resource/ISSN/{issn}?format=json', session):
        field.events.append(make_event(type="validation", code="remote", result="invalid", value=issn))
        return False, "remote"

    if harvest_cache:
        harvest_cache['issn_new'][issn] = 1
    field.validation_status = 'valid'
    field.events.append(make_event(type="validation", code="remote", result="valid", value=issn))
    return True, "remote"


def validate_issn(field, session=None, harvest_cache=None):
    success, code = validate_format(field) or validate_checksum(field) or validate_cache_or_remote(field, session, harvest_cache)

    if success:
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
    return success, code
