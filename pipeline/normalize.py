from html import unescape
from html.parser import HTMLParser
import re

from stdnum.issn import format as issn_format

from pipeline.util import update_at_path, make_event

def normalize_issn(body, field):
    issn = field.value
    path = field.path

    new_value = issn_format(issn)
    if new_value != issn:
        update_at_path(body, path, new_value)
        field.events.append(make_event(type="normalization", code="format", value=new_value, initial_value=issn, result="normalized"))
        field.normalization_status = 'normalized'
        field.value = new_value


def normalize_isbn(body, field):
    isbn = field.value
    path = field.path

    new_value = isbn.replace('-', '').upper()
    if new_value != isbn:
        update_at_path(body, path, new_value)
        field.events.append(make_event(type="normalization", code="format", value=new_value, initial_value=isbn, result="normalized"))
        field.normalization_status = 'normalized'
        field.value = new_value


def normalize_isi(body, field):
    isi = field.value

    new_value = isi.upper()
    if new_value != isi:
        update_at_path(body, path, new_value)
        field.events.append(make_event(type="normalization", code="capitalize", value=new_value, initial_value=isi, result="normalized"))
        field.normalization_status = 'normalized'
        field.value = new_value


def normalize_orcid(body, field):
    HTTP_PREFIX = 'http://orcid.org/'
    HTTPS_PREFIX = 'https://orcid.org/'
    orcid = field.value
    path = field.path
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
        field.events.append(make_event(type="normalization", result="normalized", code=code, value=enriched_value, initial_value=orcid))
        field.normalization_status = 'normalized'
        field.value = enriched_value

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
        field.events.append(make_event(type="normalization", result="normalized", code="format.delimiters", value=enriched, initial_value=initial))
        field.normalization_status = 'normalized'
        field.value = enriched


def normalize_doi(body, field):
    HTTPS_PREFIX = 'https://doi.org/'
    DOI_PREFIX = '10.'
    doi_prefix = re.compile(r'(https?://doi\.org/)?(10\..*)')
    doi = field.value
    path = field.path
    # normalize_doi_prefix
    enriched_value = doi
    path = field.path

    # _prefix_cleaner
    doi_match = doi_prefix.findall(doi)
    new_value = ''.join(doi_match[0]) if doi_match else doi
    if doi != new_value:
        update_at_path(body, path, new_value)
        field.events.append(make_event(type="normalization", result="normalized", code="prefix.remove", value=new_value, initial_value=doi))
        field.normalization_status = 'normalized'
        field.value = new_value

    code = ''
    if new_value.startswith('http:'):
        code = 'prefix.update'
        enriched_value = new_value[:4] + 's' + new_value[4:]
    elif new_value.startswith(DOI_PREFIX):
        code = 'prefix.add'
        enriched_value = HTTPS_PREFIX + new_value
    if new_value != enriched_value:
        update_at_path(body, path, enriched_value)
        field.events.append(make_event(type="normalization", result="normalized", code=code, value=enriched_value, initial_value=doi))
        field.normalization_status = 'normalized'
        field.value = enriched_value


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


def normalize_free_text(body, field):
    free_text = field.value
    path = field.path
    field.enrichment_status = 'unchanged'
    # strip tags
    s = MLStripper()
    s.feed(unescape(free_text))
    new_value = s.get_data()
    if new_value != free_text:
        update_at_path(body, path, new_value)
        field.events.append(make_event(type="normalization", code="strip_tags", result="normalized", value=new_value, initial_value=free_text))
        field.normalization_status = 'normalized'
        field.value = new_value
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
        field.events.append(make_event(type="normalization", code="clean_text", result="normalized", initial_value=free_text, value=new_value))
        field.normalization_status = 'normalized'
        field.value = new_value
