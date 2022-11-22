from os import getenv, path
import json

import cld3

from pipeline.auditors import BaseAuditor
from pipeline.util import get_title_by_language

categories = json.load(
    open(
        path.join(
            path.dirname(path.abspath(__file__)), "../../resources/categories.json"
        )
    )
)


def _eligible_for_autoclassification(publication):
    # 1. Publication year >= 2012
    if publication.year is None or int(publication.year) < 2012:
        return False
    # 2. Abstract is English or Swedish, with a length that's not suspiciously low
    summary = publication.summary or ""
    if not summary or len(summary) < 200:
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


def _create_subject(code, lang):
    return {
        "@type": "Topic",
        "@id": f"https://id.kb.se/term/uka/{code}",
        "inScheme": {
            "@id": "https://id.kb.se/term/uka/",
            "@type": "ConceptScheme",
            "code": "uka.se",
        },
        "code": code,
        "prefLabel": categories.get(code, {}).get(lang),
        "language": {
            "@type": "Language",
            "@id": f"https://id.kb.se/language/{lang}",
            "code": lang,
        },
        "hasNote": [{"@type": "Note", "label": "Autoclassified by Swepub"}],
    }


class AutoclassifierAuditor(BaseAuditor):
    """An 'auditor' class used to check autoclassify publications with no level 3/5 classification."""

    def __init__(self):
        self.name = AutoclassifierAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, session, _harvest_id):
        # TODO: if SWEPUB_SKIP_AUTOCLASSIFIER, don't load this class at all
        if getenv("SWEPUB_SKIP_AUTOCLASSIFIER"):
            return publication, audit_events

        if not _eligible_for_autoclassification(publication):
            return publication, audit_events

        publication, new_audit_events, result = self._auto_classify(
            publication, audit_events, session
        )

        return publication, new_audit_events

    def _auto_classify(self, publication, audit_events, session):
        summary = (publication.summary or "")[:5000].strip()

        language_prediction_summary = cld3.get_language(summary)
        # If we can't figure out the language of the summary, skip
        if (
            not language_prediction_summary
            or not language_prediction_summary.is_reliable
        ):
            return publication, audit_events, False
        language = language_prediction_summary.language
        # If guessed language not English or Swedish, skip
        if language not in ["en", "sv"]:
            return publication, audit_events, False

        title = get_title_by_language(publication, language)
        current_codes = set(publication.ukas())

        # Get non-UKA keywords in the target language; set Annif URL
        if language == "sv":
            language_id = "https://id.kb.se/language/swe"
            annif_url = getenv("ANNIF_SV_URL")
        else:
            language_id = "https://id.kb.se/language/eng"
            annif_url = getenv("ANNIF_EN_URL")
        keywords = " ".join(publication.keywords(language=language_id))

        try:
            r = session.post(
                f"{annif_url}/suggest",
                data={
                    "text": f"{title} {summary} {keywords}",
                    "limit": 5,
                    "threshold": 0.5,
                },
            )
            if r.status_code != 200:
                return publication, audit_events, False
            suggestions = r.json()["results"]
        except Exception as e:
            return publication, audit_events, False

        if not suggestions:
            return publication, audit_events, False


        # The suggestion API returns suggestions for level 1, 3 and 5 (as it should),
        # but for autoclassification we should only add level 3.
        # Additionally, we should add no more than 3 classifications.
        suggested_codes = set()
        for suggestion in [
            d for d in suggestions if d["uri"].split("/")[-1] not in current_codes
        ]:
            # Extract UKA code from URI
            code = suggestion["uri"].split("/")[-1]
            # Skip sugggested level 1
            if len(code) == 1:
                continue
            # Don't autoclassify on level 5; if we find one, add the level 3 part of it.
            if len(code) == 3 or len(code) == 5:
                suggested_codes.add(code[:3])
            if len(suggested_codes) == 3:
                break

        # We've got a maximum of 3 suggested codes, all on level 3; now expand them to level 1
        expanded_suggested_codes = set(suggested_codes)
        for code in suggested_codes:
            expanded_suggested_codes.add(code[:1])

        new_codes = expanded_suggested_codes - current_codes

        if not new_codes:
            return publication, audit_events, False

        initial_value = publication.uka_swe_classification_list

        classifications = []
        for code in new_codes:
            classifications.append(_create_subject(code, "eng"))
            classifications.append(_create_subject(code, "swe"))
        publication.add_subjects(classifications)

        value = publication.uka_swe_classification_list
        audit_events.add_event(self.name, "auto_classify", True, initial_value, value)

        return publication, audit_events, True
