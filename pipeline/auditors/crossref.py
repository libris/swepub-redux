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
                    result, modified_properties = publication.add_crossref_data(crossref)
                    if result:
                        continue
            except Exception as e:
                print(f"Enrichment from Crossref failed for ID {publication.id}: {e}")
                print(traceback.format_exc())
                continue

        if result and modified_properties:
            print(modified_properties)
            for modified in modified_properties:
                new_audit_events = self._add_audit_event(
                    audit_events, modified["name"], modified["code"], result, modified["value"]
                )
            print(new_audit_events)
            return publication, new_audit_events, result
        else:
            return publication, audit_events, result

    def _clean_identifier(self, identifier):
        cleaned_identifier = identifier
        # DOIs in Crossref/Unpaywall mirrors are stored without the https?://doi.org/ prefix,
        # while DOIs in Swepub are (at this point) *with* prefix, so we remove any prefix before looking it up.
        if identifier.startswith(("http://doi.org/", "https://doi.org/")):
            cleaned_identifier = re.sub(self.doi_cleaner_regex, "", identifier)
        return cleaned_identifier

    def _add_audit_event(self, audit_events, auditor_name, code, result, value):
        # For legacy reasons (sigh) we need to each type of "audit" that this Auditor does
        # needs to have its own "auditor name".
        audit_events.add_event(auditor_name, code, result, value=value)
        return audit_events
