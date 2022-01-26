from urllib.parse import quote
import unicodedata
import sys
from validators.shared import remote_verification
from util import make_event

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

def _validate_printable_chars_and_no_ws(doi):
    """DOI can incorporate any printable characters from the legal graphic characters of Unicode
    (https://www.doi.org/doi_handbook/2_Numbering.html)."""
    # The translate function removes illegal chars.
    return doi == doi.translate(TRANSLATE_DICT)

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

def validate_doi(doi, path, session, events):
    if not _validate_printable_chars_and_no_ws(doi):
        events.append(make_event("validation", "DOI", path, "unicode", "invalid"))
        return False
    
    stripped_doi = _strip_doi_http_prefix(doi)
    if not _doi_is_valid_format(stripped_doi):
        events.append(make_event("validation", "DOI", path, "format", "invalid"))
        return False

    valid = _validate_with_shortdoi(stripped_doi, session)
    if not valid:
        valid = _validate_with_crossref(stripped_doi, session)
        if not valid:
            events.append(make_event("validation", "DOI", path, "remote.crossref", "invalid"))
            return False

    return True
