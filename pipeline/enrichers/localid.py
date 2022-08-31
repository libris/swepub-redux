from pipeline.util import FieldMeta, Enrichment, Validation, get_at_path, append_at_path, get_localid_cache_key, make_event

def recover_orcid_from_localid(body, field, harvest_cache, source):
    created_fields = []
    parent_path = field.path.rsplit(".", 1)[0]
    all_ids_for_agent = get_at_path(body, parent_path)

    for id_value in all_ids_for_agent:
        if id_value.get("@type") == "ORCID":
            # This agent already has an ORCID so nothing to do
            return

    if not isinstance(field.value, dict) or not field.value.get("source", {}).get("code") or not field.value.get("value"):
        return

    cache_key = get_localid_cache_key(field.value, source)
    cache_result = harvest_cache["localid_to_orcid_static"].get(cache_key) or harvest_cache["localid_to_orcid_new"].get(cache_key)
    if cache_result:
        orcid, source_id = cache_result
        new_path = append_at_path(body, parent_path, type="ORCID", new_value=orcid)
        field.events.append(
            make_event(
                event_type="enrichment",
                code="add_orcid_from_localid",
                value=orcid,
                initial_value=f"{source_id}, {field.value.get('value')}",
                result="enriched",
            )
        )
        created_fields.append(
            FieldMeta(path=new_path, id_type=field.id_type, value=orcid, validation_status=Validation.VALID)
        )
        field.enrichment_status = Enrichment.ENRICHED
        return created_fields
