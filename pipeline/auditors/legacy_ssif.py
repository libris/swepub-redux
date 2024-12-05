from pipeline.auditors import BaseAuditor
from pipeline.util import SSIF_BASE
from pipeline.ldcache import get_description

class LegacySSIFAuditor(BaseAuditor):
    """Used to flag use of legacy SSIF codes, and migrate classifications to SSIF 2025 when possible"""

    def __init__(self):
        self.name = LegacySSIFAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        #old_classifications = publication.classifications

        for classification in publication.classifications:
            description = get_description(classification["@id"])
            if not description:
                continue
            is_replaced_bys = description.get("isReplacedBy", [])
            if is_replaced_bys:
                if len(is_replaced_bys) == 1:
                    # If there's exactly one possible replacement, use it
                    classification["@id"] = is_replaced_bys[0]["@id"]
                else:
                    replaced_by_ids = list(map(lambda x: x["@id"].removeprefix(SSIF_BASE), is_replaced_bys))
                    level_3 = replaced_by_ids[0][:3]
                    if all(classification.startswith(level_3) for classification in replaced_by_ids):
                        # All SSIF codes have the same level 3, so use it
                        classification["@id"] = f"{SSIF_BASE}{level_3}"
                    else:
                        narrow_match = description.get("narrowMatch", [])
                        if len(narrow_match) == 1:
                            classification["@id"] = narrow_match[0]["@id"]
                        else:
                            print("No SSIF 2011->2025 mapping possible")
                            audit_events.add_event(self.name, "SSIF_2011_not_migrated", '', publication.classifications, '')

        return publication, audit_events
