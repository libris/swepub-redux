import requests
from auditors import BaseAuditor
from os import environ
import json

#INFO_API = environ.get("SWEPUB_INFO_API")
#SUBJECTS_ENDPOINT = environ.get("SWEPUB_INFO_API_SUBJECTS")

def sort_mappings(unsorted):
    """Create a tree given a dict
    We expect the dict to contain keys of length 1, 3, or 5. These lengths
    correspond to different levels in the tree. A longer key must have a
    shorter key as "parent".
    """
    sorted_subjects = {}
    # We iterate over the keys sorted by first prefix and then length
    # `1` comes first, `101` comes before `10101`, which comes before `2`
    for k in sorted(unsorted.keys(), key=lambda k: len(k)):
        v = unsorted[k]
        if len(k) == 1:
            if k not in sorted_subjects:
                sorted_subjects[k] = v
        elif len(k) == 3:
            assert k[:1] in sorted_subjects
            if 'subcategories' not in sorted_subjects[k[:1]]:
                sorted_subjects[k[:1]]['subcategories'] = {}
            sorted_subjects[k[:1]]['subcategories'][k] = v
        elif len(k) == 5:
            assert k[:1] in sorted_subjects
            # `subcategories` key should have been added in the previous case
            assert 'subcategories' in sorted_subjects[k[:1]]
            assert k[:3] in sorted_subjects[k[:1]]['subcategories']
            if 'subcategories' not in sorted_subjects[k[:1]]['subcategories'][k[:3]]:
                sorted_subjects[k[:1]]['subcategories'][k[:3]]['subcategories'] = {}
            sorted_subjects[k[:1]]['subcategories'][k[:3]]['subcategories'][k] = v
    return sorted_subjects

mappings = sort_mappings(json.load(open("./pipeline/ssif_research_subjects.json")))


class SubjectsAuditor(BaseAuditor):
    """A class used to expand research subjects."""

    def __init__(self, subjects=None):
        self.name = SubjectsAuditor.__name__
        self.subjects = subjects

    def audit(self, publication, audit_events):
        """Expand research subjects if possible."""
        if self.subjects is None:
            self._load_subject_codes()
        subjects = publication.subjects
        complimentary_subjects = self._get_complimentary_subjects(publication)
        publication.subjects = subjects + complimentary_subjects

        step = "Expand research subjects"
        result = False
        if len(complimentary_subjects) > 0:
            #logger.info(
            #    f"Expanded {len(complimentary_subjects)} research subjects",
            #    extra={"auditor": self.name},
            #)
            result = True
        new_audit_events = self._add_audit_event(audit_events, step, result)
        return (publication, new_audit_events)

    def _load_subject_codes(self):
        self.subjects = mappings
        #"""Try to load subjects from Info API"""
        #try:
        #    response = requests.get(INFO_API + SUBJECTS_ENDPOINT)
        #    if response.status_code != 200:
        #        #logger.error(f"Bad response from Info API: {response.status_code}")
        #        print.error(f"Bad response from Info API: {response.status_code}")
        #        exit(-1)
        #        return
        #    self.subjects = response.json()
        #except requests.exceptions.ConnectionError as e:
            #logger.error(
            #    f"Could not access Info API: {e}", extra={"auditor": self.name}
            #)
        #    print(
        #        f"Could not access Info API: {e}", extra={"auditor": self.name}
        #    )
        #    exit(-1)
        #    return

    def _get_complimentary_subjects(self, publication):
        """Find and add complimentary research subjects"""
        missing_codes_swe = set()
        missing_codes_eng = set()
        found_codes = set()
        for subj in self._get_research_subjects(publication):
            if subj.get("inScheme", {}).get("code") != "uka.se":
                continue
            if "code" not in subj:
                continue
            # There should be a language code, but if there isn't we'll default
            # to swedish
            lang = subj.get("language", {}).get("code", "swe")
            if lang == "eng":
                missing_codes = missing_codes_eng
            else:
                missing_codes = missing_codes_swe
            code = subj["code"]
            found_codes.add(code)
            missing_codes.discard(code)
            if len(code) == 1:
                continue
            elif len(code) == 3:
                parent = code[:1]
                if parent in found_codes:
                    continue
                missing_codes.add(parent)
            elif len(code) == 5:
                parent = code[:3]
                if parent not in found_codes:
                    missing_codes.add(parent)
                grandparent = code[:1]
                if grandparent not in found_codes:
                    missing_codes.add(grandparent)
        result = []
        for code in sorted(missing_codes_swe):
            result.append(self._build_subject(code, "swe"))
        for code in sorted(missing_codes_eng):
            result.append(self._build_subject(code, "eng"))

        return result

    def _get_research_subjects(self, publication):
        """Get research subjects from publication"""
        uka_prefix = "https://id.kb.se/term/uka/"
        research_subjects = []
        for subj in publication.subjects:
            if "@id" in subj and subj["@id"].startswith(uka_prefix):
                research_subjects.append(subj)

        return research_subjects

    def _build_subject(self, code, lang):
        """Build a complete research subject"""
        if len(code) == 1:
            label = self.subjects[code][lang]
            return _get_subject(code, label, lang, broader_topics=[])
        elif len(code) == 3:
            parent = self.subjects[code[:1]]
            broader_topics = [parent[lang]]
            label = parent["subcategories"][code][lang]
            return _get_subject(code, label, lang, broader_topics)

    def _add_audit_event(self, audit_events, step, is_missing):
        audit_events.add_event(self.name, step, is_missing)
        return audit_events


def _get_subject(code, label, lang, broader_topics=[]):
    """Create subject from template"""
    subject = {
        "@id": f"https://id.kb.se/term/uka/{code}",
        "@type": "Topic",
        "code": code,
        "prefLabel": label,
        "language": {
            "@id": f"https://id.kb.se/language/{lang}",
            "@type": "Language",
            "code": lang,
        },
        "inScheme": {
            "@id": "https://id.kb.se/term/uka/",
            "@type": "ConceptScheme",
            "code": "uka.se",
        },
    }
    broader = _get_broader(broader_topics)
    if broader:
        subject["broader"] = broader
    return subject


def _get_broader(topics):
    """Create `broader` structure"""
    if not topics:
        return None
    topic = topics.pop(0)
    broader = {"prefLabel": topic}
    if topics:
        next_level = _get_broader(topics)
        if next_level:
            broader["broader"] = next_level
    return broader