from pipeline.ldcache import embellish
from pipeline.auditors import BaseAuditor

# INFO_API = environ.get("SWEPUB_INFO_API")
# SUBJECTS_ENDPOINT = environ.get("SWEPUB_INFO_API_SUBJECTS")


class SubjectsAuditor(BaseAuditor):
    """A class used to expand research subjects."""

    def __init__(self):
        self.name = SubjectsAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, _session):
        """Expand research subjects if possible."""

        old_items = publication.classifications

        is_missing = False

        new_items = []

        for item in publication.classifications:
            embellished = embellish(item, ["broader"])
            new_items.append(embellished)

            if embellished is not item:
                is_missing = True

        publication.classifications = new_items

        audit_events.add_event(self.name, "expand_research_subjects", is_missing)

        return publication, audit_events
