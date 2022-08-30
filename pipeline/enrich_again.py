from pipeline.storage import get_connection

def enrich_again(harvest_cache):
    print("localid_without_orcid", harvest_cache["localid_without_orcid"])
    print("localid_to_orcid", harvest_cache["localid_to_orcid"])
    return

    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        for localid_key, oai_ids in harvest_cache["localid_without_orcid"].items():
            orcid = harvest_cache["localid_to_orcid"].get(localid_key)
            print("k, v", localid_key, oai_id)
            if orcid:
                for oai_id in oai_ids:
                    for row in cur.execute("SELECT data FROM converted WHERE oai_id = ?", [oai_id]):
                        converted = json.loads(row)
                        publication = Publication(converted)


                print(f"HIT for {oai_id}: {orcid}")
        
# For debugging
if __name__ == "__main__":
    enrich_again(harvest_cache)
