from pipeline.auditors import BaseAuditor

class LocalidAuditor(BaseAuditor):
    """An 'auditor' class used to check for stale LocalID->ORCID cache entries."""

    def __init__(self):
        self.name = LocalidAuditor.__name__

    def audit(self, publication, audit_events, harvest_cache, session, harvest_id):
        localid_to_orcid_source = harvest_cache["localid_to_orcid_sources"].get(publication.id)
        if localid_to_orcid_source:
            for cache_key in localid_to_orcid_source.get("cache_keys", []):
                cached_localid = harvest_cache["localid_to_orcid"].get(cache_key)
                if cached_localid and len(cached_localid) > 2:
                    if cached_localid[2] != harvest_id:
                        print("popping", cache_key)
                        harvest_cache["localid_to_orcid"].pop(cache_key)
                        try:
                            localid_to_orcid_source["cache_keys"].remove(cache_key)
                        except Exception:
                            pass
            if len(localid_to_orcid_source["cache_keys"]) == 0:
                harvest_cache["localid_to_orcid_sources"].pop(publication.id)
        return publication, audit_events


# finns current_oai_id i harvest_cache["localid_to_orcid_sources"]? Isåfall,
# kolla upp alla dess cache_keys och ta bort de som inte har current_harvest_id

# vidare - OM incremental (och fromtime != None): reseta harvest_time för source-org i fråga