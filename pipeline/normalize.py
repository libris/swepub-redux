from util import update_at_path
from log import log_for_OAI_id
from stdnum.issn import format as issn_format

def normalize_issn(issn, body, path, id):
    new_value = issn_format(issn)
    if new_value != issn:
        update_at_path(body, path, new_value)
        log_for_OAI_id(id, "ISSN normalized")

def normalize_isbn(isbn, body, path, id):
    new_value = isbn.replace('-', '').upper()
    if new_value != isbn:
        update_at_path(body, path, new_value)
        log_for_OAI_id(id, "ISBN normalized")

def normalize_isi(isi, body, path, id):
    new_value = isi.upper()
    if new_value != isi:
        update_at_path(body, path, new_value)
        log_for_OAI_id(id, "ISI normalized")