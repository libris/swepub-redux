from util import update_at_path
from log import log_for_OAI_id
from stdnum.issn import format as issn_format

def normalize_issn(issn, body, path, id):
    new_value = issn_format(issn)
    if new_value != issn:
        update_at_path(body, path, new_value)
        log_for_OAI_id(id, "ISSN normalized")
        print(f"Fixed up {issn} -> {new_value}")