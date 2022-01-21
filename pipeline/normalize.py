from util import update_at_path, make_event
from stdnum.issn import format as issn_format
from html import unescape
from html.parser import HTMLParser
import re

def normalize_issn(issn, body, path, events):
    new_value = issn_format(issn)
    if new_value != issn:
        update_at_path(body, path, new_value)
        events.append(make_event("normalization", "ISSN", path, "format", new_value))

def normalize_isbn(isbn, body, path, events):
    new_value = isbn.replace('-', '').upper()
    if new_value != isbn:
        update_at_path(body, path, new_value)
        events.append(make_event("normalization", "ISBN", path, "format", new_value))

def normalize_isi(isi, body, path, events):
    new_value = isi.upper()
    if new_value != isi:
        update_at_path(body, path, new_value)
        events.append(make_event("normalization", "ISI", path, "capitalize", new_value))

HTTP_PREFIX = 'http://orcid.org/'
HTTPS_PREFIX = 'https://orcid.org/'
def normalize_orcid(orcid, body, path, events):
    # normalize_orcid_prefix
    enriched_value = orcid
    code = ''
    if orcid.startswith('http:'):
        code = 'prefix.update'
        enriched_value = orcid[:4] + 's' + orcid[4:]
    elif orcid and orcid[0].isnumeric():
        code = 'prefix.add'
        enriched_value = HTTPS_PREFIX + orcid
    if orcid != enriched_value:
        update_at_path(body, path, enriched_value)
        events.append(make_event("normalization", "ORCID", path, code, enriched_value))
    
    # get_orcid_with_delimiters
    initial = enriched_value
    orcid = enriched_value
    if orcid.startswith(HTTPS_PREFIX):
        orcid = orcid[len(HTTPS_PREFIX):]
    stripped = filter(lambda x: x.isdigit() or x == 'x', list(orcid.lower()))
    enriched = '-'.join(map(''.join, zip(*[iter(stripped)] * 4))).upper()
    enriched = HTTPS_PREFIX + enriched

    if initial != enriched:
        update_at_path(body, path, enriched)
        events.append(make_event("normalization", "ORCID", path, "format.delimiters", enriched))

HTTPS_PREFIX = 'https://doi.org/'
DOI_PREFIX = '10.'
doi_prefix = re.compile(r'(https?://doi\.org/)?(10\..*)')
def normalize_doi(doi, body, path, events):
    # normalize_doi_prefix
    enriched_value = doi
    code = ''
    if doi.startswith('http:'):
        code = 'prefix.update'
        enriched_value = doi[:4] + 's' + doi[4:]
    elif doi.startswith(DOI_PREFIX):
        code = 'prefix.add'
        enriched_value = HTTPS_PREFIX + doi
    if doi != enriched_value:
        update_at_path(body, path, enriched_value)
        events.append(make_event("normalization", "DOI", path, code, enriched_value))
    
    # _prefix_cleaner
    doi_match = doi_prefix.findall(doi)
    new_value = ''.join(doi_match[0]) if doi_match else doi
    if doi != new_value:
        update_at_path(body, path, new_value)
        events.append(make_event("normalization", "DOI", path, "prefix.remove", new_value))

class MLStripper(HTMLParser):

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def normalize_free_text(free_text, body, path, events):
    # strip tags
    s = MLStripper()
    s.feed(unescape(free_text))
    new_value = s.get_data()
    if new_value != free_text:
        update_at_path(body, path, new_value)
        events.append(make_event("normalization", "free_text", path, "strip_tags", None))
        free_text = new_value
    
    # clean_text
    # \n, \r, \t etc. are replaced with a single space
    text = re.sub(r'[\a\b\f\n\r\t\v]+', ' ', free_text)
    # ASCII characters 1 to 32 shouldn't be in the text
    escapes = ''.join([chr(char) for char in range(1, 32)])
    translator = str.maketrans('', '', escapes)
    new_value = text.translate(translator)
    if new_value != free_text:
        update_at_path(body, path, new_value)
        events.append(make_event("normalization", "free_text", path, "clean_text", None))
        free_text = new_value