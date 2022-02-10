import re
from stdnum.issn import is_valid
from validators.shared import remote_verification
from util import make_event

issn_regex = re.compile('[0-9]{4}-?[0-9]{3}[0-9xX]')


def _validate(field, session, harvest_cache):
    issn = field.value
    path = field.path

    if issn is not None and isinstance(issn, str):
        hit = issn_regex.fullmatch(issn)
        if hit is None:
            field.events.append(make_event(type="validation", code="format", result="invalid", value=issn))
            return False

    if not is_valid(issn):
        field.events.append(make_event(type="validation", code="checksum", result="invalid", value=issn))
        return False

    if harvest_cache['issn'].get(issn, 0) or harvest_cache['id'].get(issn, 0):
        field.events.append(make_event(type="validation", code="remote.cache", result="valid", value=issn))
        return True

    if not remote_verification(f'https://portal.issn.org/resource/ISSN/{issn}?format=json', session):
        field.events.append(make_event(type="validation", code="remote", result="invalid", value=issn))
        return False

    harvest_cache['id'][issn] = 1
    field.validation_status = 'valid'
    field.events.append(make_event(type="validation", code="remote", result="valid", value=issn))
    return True


def validate_issn(field, session, harvest_cache):
    if _validate(field, session, harvest_cache):
        field.validation_status = 'valid'
        if not field.is_enriched():
            field.enrichment_status = 'unchanged'
    else:
        field.validation_status = 'invalid'
        if field.is_enriched():
            field.enrichment_status = 'unsuccessful'
