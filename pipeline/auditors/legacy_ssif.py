from pipeline.auditors import BaseAuditor
from pipeline.util import SSIF_BASE
from pipeline.ldcache import get_description

class LegacySSIFAuditor(BaseAuditor):
    """Used to flag use of legacy SSIF codes, and migrate classifications to SSIF 2025 when possible"""

    def __init__(self):
        self.name = LegacySSIFAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        ssifs_not_migrated = set()
        for classification in publication.classifications:
            if not (description := get_description(classification["@id"])):
                continue
            if is_replaced_bys := description.get("isReplacedBy", []):
                if len(is_replaced_bys) == 1:
                    classification["@id"] = is_replaced_bys[0]["@id"]
                else:
                    replaced_by_ids = list(map(lambda x: x["@id"].removeprefix(SSIF_BASE), is_replaced_bys))
                    level_3 = replaced_by_ids[0][:3]
                    if all(classification.startswith(level_3) for classification in replaced_by_ids):
                        classification["@id"] = f"{SSIF_BASE}{level_3}"
                    elif (narrow_match := description.get("narrowMatch", [])) and len(narrow_match) == 1:
                        classification["@id"] = narrow_match[0]["@id"]
                    elif (close_match := description.get("closeMatch", [])) and len(close_match) == 1:
                        classification["@id"] = close_match[0]["@id"]
                    else:
                        ssifs_not_migrated.add(classification["@id"])
        if ssifs_not_migrated:
            audit_events.add_event(self.name, "SSIF_2011_not_migrated", '', list(ssifs_not_migrated), '')

        return publication, audit_events
