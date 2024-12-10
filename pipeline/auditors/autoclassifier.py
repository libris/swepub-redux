from os import getenv, path
import json

from simplemma.langdetect import lang_detector

from pipeline.auditors import BaseAuditor
from pipeline.util import SWEPUB_CLASSIFIER_ID, SSIF_BASE, get_title_by_language

from pipeline.ldcache import get_description


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


def _create_classification(code):
    classification = get_description(f"{SSIF_BASE}{code}").copy()
    classification["@annotation"] = {
        "assigner": {"@id": SWEPUB_CLASSIFIER_ID}
    }
    return classification


class AutoclassifierAuditor(BaseAuditor):
    """An 'auditor' class used to check autoclassify publications with no level 3/5 classification."""

    def __init__(self):
        self.name = AutoclassifierAuditor.__name__

    def audit(self, publication, audit_events, _harvest_cache, session):
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

        language, lang_score = lang_detector(summary, lang=("sv", "en"))[0]
        # If we can't figure out the language of the summary, skip
        if (
            language not in ["sv", "en"]
            or lang_score < 0.5
        ):
            return publication, audit_events, False

        title = get_title_by_language(publication, language)
        current_codes = set(publication.ssifs())

        annif_url = getenv("ANNIF_SV_URL" if language == "sv" else "ANNIF_EN_URL")

        # Get non-SSIF keywords in the target language
        keywords = " ".join(publication.keywords(langtag=language))

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
            # Extract SSIF code from URI
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

        initial_value = _get_ssif_swe_classification_list(publication.classifications)

        classifications = [_create_classification(code) for code in new_codes]

        publication.body.setdefault("instanceOf", {}).setdefault(
            "classification", []
        ).extend(classifications)

        value = _get_ssif_swe_classification_list(publication.classifications)
        audit_events.add_event(self.name, "auto_classify", True, initial_value, value)

        return publication, audit_events, True


def _get_ssif_swe_classification_list(classifications):
    """
    Returns a list of all SSIF classifications in Swedish with code and prefLabel for each

    >>> _get_ssif_swe_classification_list([
    ...     {"@type": "Classification", "code": "1", "prefLabel": "Ett"},
    ...     {"@id": "https://id.kb.se/term/ssif/1", "@type": "Classification",
    ...      "code": "1", "prefLabel": "Ett"},
    ...     {"@id": "https://id.kb.se/term/ssif/1", "@type": "Classification",
    ...      "code": "1", "prefLabelByLang": {"sv": "Ett"}},
    ...     {"@id": "https://id.kb.se/term/ssif/1", "@type": "Classification",
    ...      "code": "1", "prefLabelByLang": {"en": "One"}},
    ...     {"@id": "https://id.kb.se/term/other/1", "@type": "Classification",
    ...      "code": "1", "prefLabelByLang": {"sv": "Ett"}},
    ... ])
    ['1 Ett', '1 Ett']
    """
    code_label_list = []

    for term in classifications:
        if term.get("@type", "") == "Classification":
            term_id = term.get("@id")
            if not term_id or not term_id.startswith(SSIF_BASE):
                continue

            code = term.get("code", "")
            for lang, label in term.get("prefLabelByLang", {}).items():
                if lang == 'sv':
                    break
            else:
                label = term.get("prefLabel", "")

            if code and label:
                code_label_list.append(f"{code} {label}")

    return code_label_list
