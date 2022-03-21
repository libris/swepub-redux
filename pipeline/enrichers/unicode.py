from pipeline.util import update_at_path, make_event, unicode_translate


def recover_unicode(body, field):
    translated = unicode_translate(field.value)
    if translated != field.value:
        update_at_path(body, field.path, translated)
        field.events.append(
            make_event(
                event_type="enrichment", code="unicode", initial_value=field.value, value=translated
            )
        )
        field.enrichment_status = "enriched"

    if field.enrichment_status != "enriched":
        field.enrichment_status = "unsuccessful"
