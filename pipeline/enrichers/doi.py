from util import update_at_path, unicode_translate
from log import log_for_OAI_id
import unicodedata
import sys

# See DOI validator in validator service for more info on these.
INVALID_DOI_UNICODE_CATEGORIES = {'Cc', 'Cf', 'Zl', 'Zp', 'Zs'}

# List containing unicode code points as integers.
INVALID_DOI_UNICODE = list((ord(c) for c in (chr(i) for i in range(sys.maxunicode))
                            if unicodedata.category(c) in INVALID_DOI_UNICODE_CATEGORIES))

TRANSLATE_DICT = {character: None for character in INVALID_DOI_UNICODE}

# Replace fraction slash with regular slash, as in UnicodeAsciiTranslator used in BaseEnricher.
TRANSLATE_DICT[ord(u'\u2044')] = ord('/')

DOI_START = "10."
VALID_STARTS = (DOI_START, "https://doi.org/10.", "http://doi.org/10.")

def recover_doi(doi, body, path, id):
    translated = doi.translate(TRANSLATE_DICT)
    if translated != doi:
        doi = translated
        update_at_path(body, path, doi)
    
    if doi.startswith(VALID_STARTS):
        return
    else:
        hit = doi.find(DOI_START)
        if hit != -1:
            update_at_path(body, path, doi[hit:])
            log_for_OAI_id(id, 'DOI enrichment: recovery')
