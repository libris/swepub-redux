import re
from pipeline.util import update_at_path, unicode_translate, make_event, Enrichment

# flake8: noqa W504
isi_regex = re.compile(
    "(?<![/0-9a-zA-Z])"
    + "((00[01][0-9]{12})"  # Shouldn't be preceded by chars that it can contain or '/' (prevent doi)
    + "|"  # Accept one of the two valid formats
    + "([Aa]19[0-9a-zA-Z]{12}))"
    + "(?:(?![0-9a-zA-Z]))"  # Shouldn't be exceeded by chars it can contain
)


def recover_isi(body, field, cached_paths={}):
    original = field.value
    isi = field.value
    translated = unicode_translate(isi)
    if translated != isi:
        isi = translated
        update_at_path(body, field.path, isi, cached_paths)
        field.events.append(
            make_event(
                event_type="enrichment",
                code="unicode",
                value=isi,
                initial_value=original,
                result="enriched",
            )
        )
        field.enrichment_status = Enrichment.ENRICHED
        field.value = isi

    hit = isi_regex.search(isi)
    if hit and hit.group() != isi:
        update_at_path(body, field.path, hit.group(), cached_paths)
        field.events.append(
            make_event(
                event_type="enrichment", code="recovery", value=hit.group(), initial_value=isi
            )
        )
        field.enrichment_status = Enrichment.ENRICHED
        field.value = hit.group()

    if len(isi) == 30 and isi[:15] == isi[15:]:
        update_at_path(body, field.path, isi[:15], cached_paths)
        field.events.append(
            make_event(event_type="enrichment", code="double", value=isi[:15], initial_value=isi)
        )
        field.enrichment_status = Enrichment.ENRICHED
        field.value = isi[:15]
