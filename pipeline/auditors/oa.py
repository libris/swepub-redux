import re
from os import getenv

from pipeline.auditors import BaseAuditor

UNPAYWALL_URL = getenv("SWEPUB_UNPAYWALL_URL", "http://oamirror.libris.kb.se:8080/v2/")


class OAAuditor(BaseAuditor):
    doi_cleaner_regex = re.compile(r"https?://doi.org/")

    def __init__(self):
        self.name = OAAuditor.__name__

    def audit(self, publication, audit_events, harvest_cache, session):
        publication, new_audit_events, result = self._check_doab(
            publication, audit_events, harvest_cache
        )

        if not result and not getenv("SWEPUB_SKIP_UNPAYWALL", False):
            publication, new_audit_events, result = self._check_unpaywall(
                publication, audit_events, session
            )

        return publication, new_audit_events

    def _check_doab(self, publication, audit_events, harvest_cache):
        result = False
        code = "add_oa"

        identifiers = (
            publication.identifiedby_isbns
            + publication.identifiedby_dois
            + publication.identifiedby_partof_dois
        )
        download_uris = []
        added_electroniclocators = []
        for identifier in identifiers:
            uris_from_db = harvest_cache["doab"].get(self._clean_identifier(identifier))
            if uris_from_db:
                # There can be multiple URIs separated by '||'
                for uri in uris_from_db.split("||"):
                    download_uris.append(uri)

        download_uris = list(set(download_uris))
        if download_uris:
            # print(f'DOAB download URI(s) found ({len(download_uris)})')
            added, new_electronic_locator = publication.add_doab_download_uris(download_uris)
            if added:
                result = True
                added_electroniclocators.extend(new_electronic_locator)

        if result:
            new_audit_events = self._add_audit_event(
                audit_events, code, result, added_electroniclocators
            )
            return publication, new_audit_events, result
        else:
            return publication, audit_events, result

    def _check_unpaywall(self, publication, audit_events, session):
        result = False
        code = "add_oa"

        added_electroniclocators = []
        for doi in publication.identifiedby_dois:
            try:
                r = session.get(f"{UNPAYWALL_URL}{self._clean_identifier(doi)}", timeout=10)
                if r.status_code == 200:
                    # print(f'Unpaywall match found')
                    doi_object = r.json()
                    added, new_electronic_locator = publication.add_unpaywall_data(doi_object)
                    if added:
                        result = True
                        added_electroniclocators.extend(new_electronic_locator)
            except Exception:
                continue
                # print(f"Failed fetching Unpaywall data for {doi}: {e}")

        if result:
            new_audit_events = self._add_audit_event(
                audit_events, code, result, added_electroniclocators
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
