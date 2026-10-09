from pipeline.util import update_at_path, make_event, unicode_translate, Enrichment


def recover_unicode(body, field):
    translated = unicode_translate(field.value)
    if translated != field.value:
        update_at_path(body, field.path, translated)
        field.events.append(
            make_event(
                event_type="enrichment", code="unicode", initial_value=field.value, value=translated
            )
        )
        field.enrichment_status = Enrichment.ENRICHED

    if field.enrichment_status != Enrichment.ENRICHED:
        field.enrichment_status = Enrichment.UNSUCCESSFUL
