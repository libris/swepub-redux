import re
from os import getenv
import traceback

from pipeline.auditors import BaseAuditor

CROSSREF_URL = getenv("SWEPUB_CROSSREF_URL", "http://oamirror.libris.kb.se:8080/works/")


class CrossrefAuditor(BaseAuditor):
    doi_cleaner_regex = re.compile(r"https?://doi.org/")

    def __init__(self):
        self.name = CrossrefAuditor.__name__

    def audit(self, publication, audit_events, harvest_cache, session):
        if not getenv("SWEPUB_SKIP_REMOTE"):
            publication, new_audit_events, result = self._check_crossref(
                publication, audit_events, session
            )

        return publication, new_audit_events

    def _check_crossref(self, publication, audit_events, session):
        result = False
        code = "add_crossref"

        modified_properties = []
        for doi in publication.identifiedby_dois:
            try:
                r = session.get(f"{CROSSREF_URL}{self._clean_identifier(doi)}", timeout=10)
                if r.status_code == 200:
                    #print(f"Crossref match found for {publication.id}: {doi}")
                    #print(publication.publication_information.body)
                    crossref = r.json()
                    added, modified_properties = publication.add_crossref_data(crossref)
                    if added:
                        result = True
            except Exception as e:
                print(f"Enrichment from Crossref failed for ID {self.id}: {e}")
                print(traceback.format_exc())
                continue

        if result:
            #print(publication.publication_information.body)
            new_audit_events = self._add_audit_event(
                audit_events, code, result, modified_properties
            )
            return publication, new_audit_events, result
        else:
            return publication, audit_events, result

    def _clean_identifier(self, identifier):
        cleaned_identifier = identifier
        # DOIs in DOAB and Unpaywall mirror are stored without the https?://doi.org/ prefix,
        # while DOIs in Swepub are (at this point) *with* prefix, so we remove any prefix before looking it up.
        if identifier.startswith(("http://doi.org/", "https://doi.org/")):
            cleaned_identifier = re.sub(self.doi_cleaner_regex, "", identifier)
        return cleaned_identifier

    def _add_audit_event(self, audit_events, code, result, value):
        audit_events.add_event(self.name, code, result, value=value)
        return audit_events
