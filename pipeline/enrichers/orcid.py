import re
from util import update_at_path, unicode_translate
from log import log_for_OAI_id

# flake8: noqa W504
orcid_regex = re.compile(
    '(0000-?)' +
    '(000[1-3]-?)' +
    '([0-9]{4}-?)' +
    '([0-9]{3}-?[0-9xX])'
)

orcid_extend_regex = re.compile('000-?000[1-3]')

def recover_orcid(orcid, body, path, id):
    translated = unicode_translate(orcid)
    if translated != orcid:
        orcid = translated
        update_at_path(body, path, orcid)

    if orcid_extend_regex.match(orcid):
        orcid = '0' + orcid
        update_at_path(body, path, orcid)
        log_for_OAI_id(id, 'ORCID enrichment: extend')

    # What ?! This is stupid ?!
    #hit = orcid_regex.finditer(orcid)
    #orcid_list = [h.group() for h in hit]
    #if len(orcid_list) != 0:
    #    if len(orcid_list) > 1:
    #        log_for_OAI_id(id, f'More than one ORCID was recovered by regex regex_result: {orcid_list}, input_value: {orcid}')
    #        return
    #    elif orcid_list[0] != orcid:
    #        log_for_OAI_id(id, 'ORCID enrichment: split')
    #        update_at_path(body, path, orcid_list[0])
