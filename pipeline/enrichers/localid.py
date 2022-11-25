from pipeline.util import FieldMeta, Enrichment, Validation, get_at_path, append_at_path, get_localid_cache_key, make_event
from jsonpath_rw import parse


def recover_orcid_from_localid(body, field, harvest_cache, source, cached_paths={}):
    created_fields = []
    parent_path = field.path.rsplit(".", 1)[0]

    all_ids_for_agent = get_at_path(body, parent_path, cached_paths)

    for id_value in all_ids_for_agent:
        if id_value.get("@type") == "ORCID":
            # This agent already has an ORCID so nothing to do
            return

    if not isinstance(field.value, dict) or not field.value.get("source", {}).get("code") or not field.value.get("value"):
        return

    parent_path_2 = field.path.rsplit(".", 3)[0]
    parent_path_2_value = get_at_path(body, parent_path_2, cached_paths)
    person_name = f"{parent_path_2_value.get('agent', {}).get('familyName', '')} {parent_path_2_value.get('agent', {}).get('givenName', '')}".strip()
    if not person_name:
        return

    cache_key = get_localid_cache_key(field.value, person_name, source)
    cache_result = harvest_cache["localid_to_orcid"].get(cache_key)
    if cache_result:
        orcid, source_id = cache_result
        new_path = append_at_path(body, parent_path, type="ORCID", new_value=orcid, cached_paths=cached_paths)
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
