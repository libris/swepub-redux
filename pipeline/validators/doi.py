import unicodedata
import sys

from urllib.parse import quote

from pipeline.validators.shared import remote_verification
from pipeline.util import make_event

# For more info about unicode categories see
# https://www.fileformat.info/info/unicode/category/index.htm and
# http://www.unicode.org/reports/tr44/#General_Category_Values
# Cc = control, e.g. tab and new line.
# Cf = format, e.g. zero width space.
# Z* = line and paragraph separator and white spaces.
#
# If making changes here, remember to update DOI enricher accordingly.
INVALID_DOI_UNICODE_CATEGORIES = {'Cc', 'Cf', 'Zl', 'Zp', 'Zs'}

# List containing unicode code points as integers.
INVALID_DOI_UNICODE = list((ord(c) for c in (chr(i) for i in range(sys.maxunicode))
                            if unicodedata.category(c) in INVALID_DOI_UNICODE_CATEGORIES))

TRANSLATE_DICT = {character: None for character in INVALID_DOI_UNICODE}

DOI_HTTPS_PREFIX = "https://doi.org/"
DOI_HTTP_PREFIX = "http://doi.org/"


def _validate_with_crossref(doi, session):
        # Encode doi to ensure valid url, same is done in forward-proxy.
        url_encoded_doi = quote(doi, safe="/")
        url = f"https://api.crossref.org/works/{url_encoded_doi}/"
        return remote_verification(url, session)


def _validate_with_shortdoi(doi, session):
        # Encode doi to ensure valid url, same is done in forward-proxy.
        url_encoded_doi = quote(doi, safe="/")
        url = f"http://shortdoi.org/{url_encoded_doi}?format=json"
        return remote_verification(url, session)


def _strip_doi_http_prefix(doi):
    if doi.startswith(DOI_HTTPS_PREFIX):
        return doi[len(DOI_HTTPS_PREFIX):]
    elif doi.startswith(DOI_HTTP_PREFIX):
        return doi[len(DOI_HTTP_PREFIX):]
    return doi


def _doi_is_valid_format(doi):
    """ A DOI should have a prefix and suffix, separated by '/'.
    The prefix should start with '10.1' followed by a registrant code.
    The suffix can be of any length except 0. For more info see:
    https://www.doi.org/doi_handbook/2_Numbering.html
    """

    # Split into prefix and suffix.
    doi_parts = doi.split('/', 1)
    if len(doi_parts) != 2:
        # Missing separator in doi.
        return False

    # Check prefix.
    if not doi_parts[0].startswith("10.") or len(doi_parts[0]) < 4:
        return False

    # Check suffix.
    if len(doi_parts[1]) < 1:
        return False

    return True


def validate_unicode(doi, session=None, harvest_cache=None):
    """DOI can incorporate any printable characters from the legal graphic characters of Unicode
    (https://www.doi.org/doi_handbook/2_Numbering.html)."""
    # The translate function removes illegal chars.
    return doi == doi.translate(TRANSLATE_DICT), "unicode", None


def validate_format(doi, session=None, harvest_cache=None):
    stripped_doi = _strip_doi_http_prefix(doi)
    return _doi_is_valid_format(stripped_doi), "format", stripped_doi


def validate_with_remote(doi, session, harvest_cache):
    stripped_doi = _strip_doi_http_prefix(doi)
    if harvest_cache['doi_static'].get(stripped_doi, 0) or harvest_cache['doi_new'].get(stripped_doi, 0):
        return True, "remote.cache", stripped_doi
    if not _validate_with_shortdoi(stripped_doi, session) and not _validate_with_crossref(stripped_doi, session):
            return False, "remote.crossref", stripped_doi
    harvest_cache['doi_new'][stripped_doi] = 1
    return True, "remote", stripped_doi


def validate_doi(field, session, harvest_cache):
    for validator in [validate_unicode, validate_format, validate_with_remote]:
        success, code, new_value = validator(field.value, session, harvest_cache)
        if not success:
            field.events.append(make_event(type="validation", code=code, result="invalid", value=(new_value or field.value)))
            field.validation_status = 'invalid'
            if field.is_enriched():
                field.enrichment_status = 'unsuccessful'
            return
    field.events.append(make_event(type="validation", code=code, result="valid", value=(new_value or field.value)))
    field.value = new_value or field.value
    field.validation_status = 'valid'
    if not field.is_enriched():
        field.enrichment_status = 'unchanged'
