import orjson as json

from pipeline.publication import Publication
from pipeline.storage import get_connection, dict_factory, serialize
from pipeline.util import append_at_path, make_event


def enrich_again(harvest_cache):
    print("localid_without_orcid", harvest_cache["localid_without_orcid"])
    print("localid_to_orcid", harvest_cache["localid_to_orcid"])

    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        for localid_key, oai_ids in harvest_cache["localid_without_orcid"].items():
            orcid = harvest_cache["localid_to_orcid"].get(localid_key)
            print("k, v", localid_key, oai_ids)
            if orcid:
                for oai_id, agent_path in oai_ids:
                    print(f"HIT for {oai_id}, {agent_path}: {orcid}")
                    rows = cur.execute("SELECT data, events FROM converted WHERE oai_id = ?", [oai_id]).fetchall()
                    #for row in cur.execute("SELECT data, events FROM converted WHERE oai_id = ?", [oai_id]):
                    for row in rows:
                        converted = json.loads(row["data"])
                        converted_events = json.loads(row["events"])
                        new_path = append_at_path(converted, agent_path, type="ORCID", new_value=orcid)
                        event = {
                            "enrichment_status": "enriched", "normalization_status": "unchanged", "validation_status": "valid",
                            "events": [
                                {
                                    "code": "recovery",
                                    "value": orcid,
                                    "result": "enriched"
                                }
                            ]
                        }
                        orcid_events = converted_events["field_events"].get("ORCID", {})
                        orcid_events[new_path] = event
                        converted_events["field_events"]["ORCID"] = orcid_events
                        #contributions = contributions.

                        cur.execute("UPDATE converted SET data = ?, events = ? WHERE oai_id = ?", [json.dumps(converted), json.dumps(converted_events, default=serialize), oai_id])
                con.commit()


# For debugging
if __name__ == "__main__":
    enrich_again(harvest_cache)
