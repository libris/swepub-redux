from pipeline.auditors import BaseAuditor


class ModsFixer(BaseAuditor):
    """A class to do things that should've ideally been done in the MODS-to-JSON-LD XSLT, but weren't possible for some reason."""


    def __init__(self):
        self.name = ModsFixer.__name__


    def audit(self, publication, audit_events, _harvest_cache, _session):
        for contribution in publication.contributions:
            contribution.affiliations = self._handle_affiliations(contribution.affiliations)
        return publication, audit_events


    # Merges affiliations that refer to the same thing but have been split up by language
    def _handle_affiliations(self, affiliations):
        grouped = {}
        not_grouped = []

        for affiliation in affiliations:
            id_by = affiliation.get("identifiedBy", [])
            if id_by and affiliation.get("nameByLang"):
                language, name = list(affiliation.get("nameByLang").items())[0]
                id_by_value = id_by[0].get("value", "")

                key = None
                # Merge affiliations that have @type ROR and the same identifiedBy value (i.e., ROR ID).
                if id_by[0].get("@type", "") == "ROR":
                    key = f"ROR-{id_by_value}"
                # Merge affiliations with source/authority kb.se and identical identifiedBy value
                # *if* they have *different* languages; if they have the same
                # language, we don't, because in that case they probably express specific institutions.
                elif id_by[0].get("source", {}).get("code", "") == "kb.se":
                    key = f"kb.se-{id_by_value}"

                if key:
                    if key not in grouped:
                        grouped[key] = {'@type': 'Organization', 'nameByLang': {}, 'identifiedBy': id_by}
                    if language not in grouped[key]['nameByLang']:
                        grouped[key]['nameByLang'][language] = name
                    elif id_by[0].get("@type", "") == "ROR":
                        grouped[key]['nameByLang'][language] = name
                    else:
                        not_grouped.append(affiliation)
                else:
                    not_grouped.append(affiliation)
            else:
                not_grouped.append(affiliation)

        return [v for _k, v in grouped.items()] + not_grouped
