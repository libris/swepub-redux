import re
from util import update_at_path, unicode_translate, make_event

# flake8: noqa W504
orcid_regex = re.compile(
    '(0000-?)' +
    '(000[1-3]-?)' +
    '([0-9]{4}-?)' +
    '([0-9]{3}-?[0-9xX])'
)

orcid_extend_regex = re.compile('000-?000[1-3]')

def recover_orcid(orcid, body, path, id, events):
    translated = unicode_translate(orcid)
    if translated != orcid:
        initial = orcid
        orcid = translated
        update_at_path(body, path, orcid)
        events.append(make_event("enrichment", "ORCID", path, "unicode", orcid, initial_value=initial))

    if orcid_extend_regex.match(orcid):
        initial = orcid
        orcid = '0' + orcid
        update_at_path(body, path, orcid)
        events.append(make_event("enrichment", "ORCID", path, "extend", orcid, initial_value=initial))

    hit = orcid_regex.finditer(orcid)
    orcid_list = [h.group() for h in hit]
    if len(orcid_list) != 0:
       if orcid_list[0] != orcid:
           events.append(make_event("enrichment", "ORCID", path, "split", orcid_list[0], initial_value=orcid))
           update_at_path(body, path, orcid_list[0])
