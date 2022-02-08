import re
from util import update_at_path, unicode_translate, make_event

    # flake8: noqa W504
isi_regex = re.compile(
    '(?<![/0-9a-zA-Z])' +  # Shouldnt be preceded by chars that it can contain or '/' (prevent doi)
    '((000[0-9]{12})' +  # Accept one of the two valid formats
    '|' +
    '([Aa]19[0-9a-zA-Z]{12}))' +
    '(?:(?![0-9a-zA-Z]))'  # Shouln't be exceded by chars it can contain
)


def recover_isi(body, field):
    original = field.value
    isi = field.value
    translated = unicode_translate(isi)
    if translated != isi:
        isi = translated
        update_at_path(body, field.path, isi)
        field.events.append(make_event(type="enrichment", code="unicode", value=isi, initial_value=original, result="enriched"))
        field.enrichment_status = "enriched"
        field.value = isi

    hit = isi_regex.search(isi)
    if hit and hit.group() != isi:
        update_at_path(body, field.path, hit.group())
        field.events.append(make_event(type="enrichment", code="recovery", value=hit.group(), initial_value=isi))
        field.enrichment_status = "enriched"
        field.value = hit.group()
    
    if len(isi) == 30 and isi[:15] == isi[15:]:
        update_at_path(body, field.path, isi[:15])
        field.events.append(make_event(type="enrichment", code="double", value=isi[:15], initial_value=isi))
        field.enrichment_status = "enriched"
        field.value = isi[:15]
