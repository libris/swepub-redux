import re
from os import getenv

from pipeline.auditors import BaseAuditor

UNPAYWALL_URL = getenv("SWEPUB_UNPAYWALL_URL", "http://oamirror.libris.kb.se:8080/v2/")


class ORCIDAuditor(BaseAuditor):
    doi_cleaner_regex = re.compile(r"https?://doi.org/")

    def __init__(self):
        self.name = ORCIDAuditor.__name__

    def audit(self, publication, audit_events, harvest_cache, _session):
        for idx, contribution in enumerate(publication.contributions):
            if contribution.local_id and not contribution.orcid:
                print("contrib", idx, contribution.body)
                cache_key = f"{contribution.local_id.get('source').get('code')}_{contribution.local_id.get('value')}"

                agent_path = f"instanceOf.contribution.[{idx}].agent.identifiedBy"

                cache_list = harvest_cache["localid_without_orcid"].get(cache_key, [])
                cache_list.append([publication.id, agent_path])
                harvest_cache["localid_without_orcid"][cache_key] = cache_list
        return publication, audit_events

    #def audit(self, publication, audit_events, harvest_cache, _session):
    #    result = False
    #    code = "add_orcid_from_local_id"
#
    #    modified = False
    #    contributions = publication.contributions
    #    for contribution in contributions:
    #        local_id = contribution.local_id
    #        if local_id and not contribution.has_orcid:
    #            cache_key = f"{local_id.get('source').get('code')}_{local_id.get('value')}"
    #            cache_result = harvest_cache["localid_to_orcid"].get(cache_key)
    #            if cache_result:
    #                identified_bys = contribution.identified_bys
    #                identified_bys.append({'@type': 'ORCID', 'value': cache_result[0]})
    #                contribution.identified_bys = identified_bys
    #                modified = True
    #                continue
    #    if modified:
    #        publication.contributions = contributions
#
    #    new_audit_events = self._add_audit_event(audit_events, code, result, "")
    #    return publication, new_audit_events

    def _add_audit_event(self, audit_events, code, result, value):
        audit_events.add_event(self.name, code, result, value=value)
        return audit_events
