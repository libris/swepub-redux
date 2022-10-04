import cld3

from pipeline.auditors import BaseAuditor
from pipeline.util import get_title_by_language, get_summary_by_language


class AutoclassifyAuditor(BaseAuditor):
    """An 'auditor' class used to check autoclassify publications with no level 3/5 classification."""

    def __init__(self):
        self.name = AutoclassifyAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, session):
        if not self._eligible_for_autoclassification(publication):
            return publication, audit_events

        publication, new_audit_events, result = self._auto_classify(publication, audit_events, session)

        return publication, new_audit_events

        #code = "auto_classify"
        #result = False
        #if publication.is_article and publication.missing_issn_or_any_empty_issn:
        #    pub_status = publication.get_publication_status_list
        #    if "https://id.kb.se/term/swepub/Published" in pub_status or len(pub_status) == 0:
        #        result = True
        #new_audit_events = self._add_audit_event(audit_events, code, result)
        #return publication, new_audit_events

    def _eligible_for_autoclassification(self, publication):
        # 1. Publication year >= 2012
        if publication.year is None or int(publication.year) < 2012:
            return False
        # 2. Abstract
        summary = publication.summary or ""
        if not summary or len(summary) < 50:
            return False
        # 3. Publication status == (Published || None)
        if (
            publication.publication_status is not None
            and publication.publication_status != "https://id.kb.se/term/swepub/Published"
        ):
            return False
        # 4. No 3-level/5-level classification
        if publication.is_classified:
            return False
        return True

    def _auto_classify(self, publication, audit_events, session):
        summary = (publication.summary or "")[:5000].strip()
        language_prediction_summary = cld3.get_language(summary)

        if not language_prediction_summary or not language_prediction_summary.is_reliable:
            return publication, audit_events, False

        language = language_prediction_summary.language 

        if language not in ["en", "sv"]:
            return publication, audit_events, False

        title = get_title_by_language(publication, language)

        current_ukas = set(publication.ukas())

        # Get non-UKA keywords in the target language
        if language == "en":
            language_id = "https://id.kb.se/language/eng"
        elif language == "sv":
            language_id = "https://id.kb.se/language/swe"
        keywords = " ".join(publication.keywords(language=language_id))

        try:
            r = session.post(
                f"http://127.0.0.1:5000/v1/projects/omikuji-parabel-{language}/suggest",
                data={
                    "text": f"{summary}",
                    "limit": 5,
                    "threshold": 0.2
                }
            )
            if r.status_code != 200:
                return publication, audit_events, False
            suggestions = r.json()["results"]
        except Exception as e:
            print("Error:", e)
            return publication, audit_events, False

        if not suggestions:
            return publication, audit_events, False

        suggested_ukas = set([d["uri"].split("/")[-1] for d in suggestions])

        print("CURRENT", current_ukas)
        print("SUGGESTED", suggested_ukas)
        new_ukas = suggested_ukas - current_ukas
        print("NEW", new_ukas)

        return publication, audit_events, True

    def _add_audit_event(self, audit_events, code, result):
        audit_events.add_event(self.name, code, result)
        return audit_events

#                       code = "auto_classify"
#                       initial_value = old_publication.uka_swe_classification_list
#                       value = publication.uka_swe_classification_list
#                       result = "1"
#
#                       events["audit_events"]["AutoclassifierAuditor"] = [
#                           {
#                               "code": "auto_classify",
#                               "result": "enriched",
#                               "initial_value": initial_value,
#                               "value": value,
#                           }
#                       ]
