from pipeline.storage import dict_factory
from pipeline.util import FieldMeta, Enrichment, Validation, get_at_path, append_at_path, get_localid_cache_key, make_event
from jsonpath_rw import parse


def recover_orcid_from_localid(body, field, harvest_cache, source, cached_paths={}, read_only_cursor=None):
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

    if read_only_cursor:
        read_only_cursor.row_factory = dict_factory
        result = read_only_cursor.execute("SELECT * FROM localid_to_orcid WHERE hash = ?", [cache_key]).fetchone()
        if result:
            orcid = result["orcid"]
            source_oai_id = result["source_oai_id"]
            print(f"LocalID MATCH! source {source_oai_id}, enriched {body['@id']}, {person_name}")
            new_path = append_at_path(body, parent_path, type="ORCID", new_value=orcid, cached_paths=cached_paths)
            field.events.append(
                make_event(
                    event_type="enrichment",
                    code="add_orcid_from_localid",
                    value=orcid,
                    initial_value=f"{source_oai_id}, {field.value.get('value')}",
                    result="enriched",
                )
            )
            created_fields.append(
                FieldMeta(path=new_path, id_type=field.id_type, value=orcid, validation_status=Validation.VALID)
            )
            field.enrichment_status = Enrichment.ENRICHED
            source_oai_ids = harvest_cache["enriched_from_other_record"].get(body["@id"], [])
            source_oai_ids.append(source_oai_id)
            harvest_cache["enriched_from_other_record"][body["@id"]] = list(set(source_oai_ids))
            return created_fields
        # If no result, add it to the list of records with localID but no ORCID
        else:
            print("Adding to localid_without_orcid", cache_key, body["@id"], person_name)
            harvest_cache["localid_without_orcid"][cache_key] = body["@id"]
