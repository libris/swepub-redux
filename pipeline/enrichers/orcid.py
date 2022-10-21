import re
from pipeline.util import update_at_path, unicode_translate, make_event, Enrichment

# flake8: noqa W504
orcid_regex = re.compile("(0000-?)" + "(000[1-3]-?)" + "([0-9]{4}-?)" + "([0-9]{3}-?[0-9xX])")

orcid_extend_regex = re.compile("000-?000[1-3]")


def recover_orcid(body, field, cached_paths={}):
    path = field.path
    orcid = field.value

    translated = unicode_translate(orcid)
    if translated != orcid:
        initial = orcid
        orcid = translated
        update_at_path(body, path, orcid, cached_paths)
        field.events.append(
            make_event(
                event_type="enrichment",
                code="unicode",
                value=orcid,
                initial_value=initial,
                result="enriched",
            )
        )
        field.enrichment_status = Enrichment.ENRICHED
        field.value = orcid

    if orcid_extend_regex.match(orcid):
        initial = orcid
        orcid = "0" + orcid
        update_at_path(body, path, orcid, cached_paths)
        field.events.append(
            make_event(
                event_type="enrichment",
                code="extend",
                value=orcid,
                initial_value=initial,
                result="enriched",
            )
        )
        field.enrichment_status = Enrichment.ENRICHED
        field.value = orcid

    hit = orcid_regex.finditer(orcid)
    orcid_list = [h.group() for h in hit]
    if len(orcid_list) != 0:
        if orcid_list[0] != orcid:
            field.events.append(
                make_event(
                    event_type="enrichment",
                    code="recovery",
                    value=orcid_list[0],
                    initial_value=orcid,
                    result="enriched",
                )
            )
            update_at_path(body, path, orcid_list[0], cached_paths)
            field.enrichment_status = Enrichment.ENRICHED
            field.value = orcid_list[0]

    if field.enrichment_status != Enrichment.ENRICHED:
        field.enrichment_status = Enrichment.UNSUCCESSFUL
