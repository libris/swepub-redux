import requests
from auditors import BaseAuditor
from os import environ

YEAR_CUTOFF = "2012"
ENGLISH = 'https://id.kb.se/language/eng'
SWEDISH = 'https://id.kb.se/language/swe'
PUBLISHED = 'https://id.kb.se/term/swepub/Published'
CLASSIFY_API = environ.get('SWEPUB_CLASSIFY_API')


class AutoClassifier(BaseAuditor):
    """A class used to automatically classify publications."""

    def __init__(self):
        self.name = AutoClassifier.__name__

    def audit(self, publication, audit_events):
        """Autoclassify publication if needed."""
        eng_summary = publication.get_english_summary()
        swe_summary = publication.get_swedish_summary()
        # 1. Publication year >= 2012
        if publication.year is None or publication.year < YEAR_CUTOFF:
            return self._skip_publication(publication, audit_events)
        # 2. Swe/eng abstract
        if not (eng_summary or swe_summary):
            return self._skip_publication(publication, audit_events)
        # 3. Publication status == (Published || None)
        if (publication.status is not None
                and publication.status != PUBLISHED):
            return self._skip_publication(publication, audit_events)
        # 4. No 3-level/5-level classification
        if publication.is_classified:
            return self._skip_publication(publication, audit_events)

        title = publication.title
        # subtitle can include useful info, so we add it if it exists
        subtitle = publication.subtitle
        if subtitle:
            title = f"{title} {subtitle}"
        keywords = publication.keywords
        language = publication.language
        # We prefer Swedish over English
        if language == 'swe' and swe_summary:
            summary = swe_summary
        elif language == 'eng' and eng_summary:
            summary = eng_summary
        elif swe_summary:
            summary = swe_summary
        else:
            # Thanks to 2. above, we'll always have this if there's no Swedish summary
            summary = eng_summary
        classifications = self._get_classifications(publication.id, title, summary, keywords)
        result = False
        code = None
        initial_value = None
        value = None
        if classifications:
            initial_value = publication.uka_swe_classification_list
            publication.add_subjects(classifications)
            result = True
            code = "autoclassified"
            value = publication.uka_swe_classification_list
            #logger.info(
            #    f"Autoclassifying publication {publication.id}", extra={'auditor': self.name})
        new_audit_events = self._add_audit_event(audit_events, result, code, initial_value, value)

        return (publication, new_audit_events)

    def _get_classifications(self, pub_id, title, summary, keywords):
        LANGS = ['eng', 'swe']
        payload = {
            "level": 3,
            "title": title,
            "abstract": summary,
            "keywords": ",".join(keywords)
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(CLASSIFY_API, json=payload, headers=headers)
        except requests.exceptions.ConnectionError as e:
            #logger.error(f"Could not access Classify API: {e}", extra={'auditor': self.name})
            print(f"Could not access Classify API: {e}", extra={'auditor': self.name})
            exit(-1)
            return []
        status = response.status_code
        if status != 200:
            #logger.error(
            #    f"Autoclassifying {pub_id} failed, response code was {status}",
            #    extra={'auditor': self.name})
            print(
                f"Autoclassifying {pub_id} failed, response code was {status}",
                extra={'auditor': self.name})
            exit(-1)
            return None
        body = response.json()
        classifications = []
        if 'suggestions' in body:
            for item in body['suggestions']:
                for lang in LANGS:
                    if lang in item:
                        classifications.append(item[lang])
        return classifications

    @staticmethod
    def _add_audit_event(audit_events, result, code=None, initial_value=None, value=None):
        name = AutoClassifier.__name__
        step = 'Autoclassifying publication'
        audit_events.add_event(name, step, result, code, initial_value, value)
        return audit_events

    def _skip_publication(self, publication, audit_events):
        autoclassifying = False
        new_audit_events = self._add_audit_event(audit_events, autoclassifying)
        return (publication, new_audit_events)
