import re

from stdnum.iso7064.mod_11_2 import is_valid

from pipeline.validators.shared import validate_base_unicode
from pipeline.util import make_event, Validation, Enrichment, get_at_path

# flake8: noqa W504
orcid_regex = re.compile(
    r"(?:(https?://orcid\.org/)?)"
    + "([0-9]{4}-?){3}"  # Check for optional url prefix
    + "([0-9]{3})"  # Three groups of four digits delimited by hyphen
    + "([0-9xX])"  # Last group of three digits  # And last character that can be a digit or an x
)


def strip_url(orcid):
    if orcid.startswith("http"):
        return orcid.split("/")[-1]
    return orcid


def validate_unicode(orcid):
    result = validate_base_unicode(orcid)
    if result:
        return True, "unicode"
    else:
        return False, "unicode"


def validate_format(orcid):
    hit = orcid_regex.fullmatch(orcid)
    if hit:
        return True, "format"
    else:
        return False, "format"


def validate_span(orcid):
    try:
        orcnum = int(strip_url(orcid).replace("-", "")[:-1])
        inspan = 15000000 <= orcnum <= 35000001
        if inspan:
            return True, "span"
        else:
            return False, "span"
    except ValueError:
        return False, "span"


def validate_checksum(orcid):
    if is_valid(strip_url(orcid).upper().replace("-", "")):
        return True, "checksum"
    else:
        return False, "checksum"


def validate_orcid(field, body, harvest_cache):
    if field.validation_status == Validation.INVALID and field.enrichment_status in [
        Enrichment.UNCHANGED,
        Enrichment.UNSUCCESSFUL,
    ]:
        return

    for validator in [validate_unicode, validate_format, validate_span, validate_checksum]:
        success, code = validator(field.value)
        if not success:
            field.events.append(
                make_event(event_type="validation", code=code, result="invalid", value=field.value)
            )
            field.validation_status = Validation.INVALID
            if field.is_enriched():
                field.enrichment_status = Enrichment.UNSUCCESSFUL
            return

    # At this point we have a valid ORCID. If the same agent also has a local ID, save the
    # local ID->ORCID key->value in the cache so that we can later add ORCID in records where
    # we encounter the same local ID (but no ORCID)
    print(field.path)
    parent_path = field.path.rsplit(".", 2)[0]
    parent_value = get_at_path(body, parent_path)
    for id_by in parent_value:
        if id_by.get("@type") == "Local" and id_by.get("value") and id_by.get("source", {}).get("code"):
            cache_key = f"{id_by.get('source').get('code')}_{id_by.get('value')}"
            harvest_cache["localid_to_orcid"][cache_key] = field.value
            print("Added", id_by.get("value"), "to cache for", field.value)
            break

    field.validation_status = Validation.VALID
    if not field.is_enriched():
        field.enrichment_status = Enrichment.UNCHANGED
