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


def recover_orcid(body, field):
    path = field.path
    orcid = field.value

    translated = unicode_translate(orcid)
    if translated != orcid:
        initial = orcid
        orcid = translated
        update_at_path(body, path, orcid)
        field.events.append(make_event(type="enrichment", code="unicode", value=orcid, initial_value=initial, result="enriched"))
        field.enrichment_status = 'enriched'
        field.value = orcid

    if orcid_extend_regex.match(orcid):
        initial = orcid
        orcid = '0' + orcid
        update_at_path(body, path, orcid)
        field.events.append(make_event(type="enrichment", code="extend", value=orcid, initial_value=initial, result="enriched"))
        field.enrichment_status = 'enriched'
        field.value = orcid

    hit = orcid_regex.finditer(orcid)
    orcid_list = [h.group() for h in hit]
    if len(orcid_list) != 0:
        if orcid_list[0] != orcid:
            field.events.append(make_event(type="enrichment", code="split", value=orcid_list[0], initial_value=orcid, result="enriched"))
            update_at_path(body, path, orcid_list[0])
            field.enrichment_status = 'enriched'
            field.value = orcid_list[0]

    if field.enrichment_status != 'enriched':
        field.enrichment_status = 'unsuccessful'
