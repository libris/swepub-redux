import itertools
from functools import reduce
from dateutil.parser import parse as parse_date
from jsonpath_rw_ext import parse
from auditors.swedishlist import Level

from auditors.swedishlist import SwedishListAuditor
from auditors.creatorcount import CreatorCountAuditor
from auditors.uka import UKAAuditor
from auditors.contributor import ContributorAuditor
from auditors.issn import ISSNAuditor
from auditors.autoclassifier import AutoClassifier
from auditors.subjects import SubjectsAuditor
from util import make_audit_event

AUDITORS = [
    SwedishListAuditor(),
    CreatorCountAuditor(),
    ContributorAuditor(),
    UKAAuditor(),
    ISSNAuditor(),
    #AutoClassifier(),
    SubjectsAuditor(),
]

auditors = AUDITORS

RAW_ISSN_PATHS = (
    'partOf.[*].identifiedBy[?(@.@type=="ISSN")].value',
    'partOf.[*].indirectlyIdentifiedBy[?(@.@type=="ISSN")].value',
    'partOf.[*].hasSeries.[*].identifiedBy[?(@.@type=="ISSN")].value',
    'partOf.[*].hasSeries.[*].indirectlyIdentifiedBy[?(@.@type=="ISSN")].value',
    'hasSeries.[*].identifiedBy[?(@.@type=="ISSN")].value',
    'hasSeries.[*].indirectlyIdentifiedBy[?(@.@type=="ISSN")].value',
    'identifiedBy[?(@.@type=="ISSN")].value',
    'indirectlyIdentifiedBy[?(@.@type=="ISSN")].value',
)
ISSN_PATHS = [parse(p) for p in RAW_ISSN_PATHS]

RAW_DATE_PATH = 'publication[?(@.@type=="Publication")].date'
DATE_PATH = parse(RAW_DATE_PATH)

RAW_TITLE_PATH = 'instanceOf.hasTitle[?(@.@type=="Title")].mainTitle'
TITLE_PATH = parse(RAW_TITLE_PATH)

RAW_SUBTITLE_PATH = 'instanceOf.hasTitle[?(@.@type=="Title")].subtitle'
SUBTITLE_PATH = parse(RAW_SUBTITLE_PATH)

RAW_LANGUAGE_PATH = 'instanceOf.language[?(@.@type=="Language")].code'
LANGUAGE_PATH = parse(RAW_LANGUAGE_PATH)

RAW_SUMMARY_PATH = 'instanceOf.summary[?(@.@type=="Summary")]'
SUMMARY_PATH = parse(RAW_SUMMARY_PATH)

RAW_SUMMARY_LANG_PATH = 'instanceOf.summary[?(@.@type=="Summary")].language.@id'
SUMMARY_LANG_PATH = parse(RAW_SUMMARY_LANG_PATH)

RAW_PUBLICATION_STATUS_PATH = 'instanceOf.hasNote[?(@.@type=="PublicationStatus")].@id'
PUBLICATION_STATUS_PATH = parse(RAW_PUBLICATION_STATUS_PATH)

RAW_SUBJECT_PATH = 'instanceOf.subject[?(@.@type=="Topic")]'
SUBJECT_PATH = parse(RAW_SUBJECT_PATH)

RAW_CREATORCOUNT_PATH = 'instanceOf.[*].hasNote[?(@.@type=="CreatorCount")].label'
CREATORCOUNT_PATH = parse(RAW_CREATORCOUNT_PATH)

RAW_GENREFORM_PATH = 'instanceOf.genreForm.[*].@id'
GENREFORM_PATH = parse(RAW_GENREFORM_PATH)

RAW_CONTRIB_PATH = 'instanceOf.contribution[?(@.@type=="Contribution")]'
CONTRIB_PATH = parse(RAW_CONTRIB_PATH)

RAW_ARTICLE_PATHS = (
    'instanceOf.genreForm[?(@.@id=="https://id.kb.se/term/swepub/JournalArticle")]',
    'instanceOf.genreForm[?(@.@id=="https://id.kb.se/term/swepub/journal-article")]',
    'instanceOf.genreForm[?(@.@id=="https://id.kb.se/term/swepub/magazine-article")]',
    'instanceOf.genreForm[?(@.@id=="https://id.kb.se/term/swepub/newspaper-article")]',
    'instanceOf.genreForm[?(@.@id=="https://id.kb.se/term/swepub/journal-issue")]',
)
ARTICLE_PATHS = [parse(a) for a in RAW_ARTICLE_PATHS]

AUT_ROLES = [
    "http://id.loc.gov/vocabulary/relators/aut",
    "http://id.loc.gov/vocabulary/relators/cre"
]
EDT_ROLES = ["http://id.loc.gov/vocabulary/relators/edt"]

EDT_PUB_TYPES = [
    "https://id.kb.se/term/swepub/EditorialCollection",
    "https://id.kb.se/term/swepub/EditorialProceedings"
]
REPORT_PUB_TYPES = [
    "https://id.kb.se/term/swepub/Report"
]
EDT_OUTPUT_TYPES = [
    "https://id.kb.se/term/swepub/publication/edited-book",
    "https://id.kb.se/term/swepub/publication/journal-issue",
    "https://id.kb.se/term/swepub/conference/proceeding"
]
REPORT_OUTPUT_TYPES = [
    "https://id.kb.se/term/swepub/publication/report"
]
EDT_TYPES = EDT_PUB_TYPES + EDT_OUTPUT_TYPES
REPORT_TYPES = REPORT_PUB_TYPES + REPORT_OUTPUT_TYPES

RAW_UKA_PATH = 'instanceOf.subject[?(@.inScheme.code=="uka.se")].code'
UKA_PATH = parse(RAW_UKA_PATH)

class AuditEvents:
    """An encapsulated representation of the audit event log."""

    def __init__(self, data=None):
        if data is None:
            data = []
        self._audit_events = data

    @property
    def data(self):
        """Return the underlying audit event data."""
        return self._audit_events

    def add_event(self, name, step, result, code=None, initial_value=None, value=None):
        """Add an audit event."""
        # if name not in self._audit_events:
        #     self._audit_events[name] = []
        # audit_event = {'step': step, 'result': result}
        # if code:
        #     audit_event['code'] = code
        # if initial_value:
        #     audit_event['initial_value'] = initial_value
        # if value:
        #     audit_event['value'] = value
        # self._audit_events[name].append(audit_event)
        self._audit_events.append(make_audit_event(
            name=name, type="audit", code=code, step=step, result=result, initial_value=initial_value
        ))

    def get_event_result(self, name, step_name):
        """Get result for specific audit step or None if not found."""
        if name not in self._audit_events:
            return None
        for step in self._audit_events[name]:
            if step['step'] == step_name:
                return step['result']
        return None


class Publication:
    """An encapsulated representation of the publication."""

    def __init__(self, publication):
        self._publication = publication

    @property
    def data(self):
        """Return the underlying publication data."""
        return self._publication

    @property
    def id(self):
        """Return publication ID."""
        if '@id' in self._publication:
            return self._publication['@id']
        return None

    @property
    def year(self):
        """Return the publication year as a string or None if missing or invalid."""
        dates = DATE_PATH.find(self._publication)
        # TODO add logging?
        if len(dates) == 1 and dates[0].value:
            try:
                parsed_date = parse_date(dates[0].value)
                return '{}'.format(parsed_date.year)
            except ValueError:
                return None
        else:
            return None

    @property
    def issns(self):
        """Return a list of all ISSNs ordered by importance."""
        issns = itertools.chain.from_iterable(
            issn_path.find(self._publication) for issn_path in ISSN_PATHS)
        return [issn.value for issn in issns if issn.value]

    @property
    def title(self):
        """Return the publication's main title."""
        title = TITLE_PATH.find(self._publication)
        if len(title) == 1 and title[0].value:
            return title[0].value
        return None

    @property
    def subtitle(self):
        """Return the publication's subtitle."""
        title = SUBTITLE_PATH.find(self._publication)
        if len(title) == 1 and title[0].value:
            return title[0].value
        return None

    @property
    def language(self):
        """Return the publication's language."""
        language = LANGUAGE_PATH.find(self._publication)
        if len(language) == 1 and language[0].value:
            return language[0].value
        return None

    @property
    def summaries(self):
        """Return a list of all summaries."""
        summaries = SUMMARY_PATH.find(self._publication)
        return [summary.value for summary in summaries if summary.value]

    def get_english_summary(self):
        """Get summary text in English if it exists."""
        return self._get_lang_summary('eng')

    def get_swedish_summary(self):
        """Get summary text in Swedish if it exists."""
        return self._get_lang_summary('swe')

    def _get_lang_summary(self, lang):
        """Get summary for specified language if it exists."""
        for summary in self.summaries:
            if 'language' not in summary:
                continue
            if 'code' not in summary['language']:
                continue
            if summary['language']['code'] != lang:
                continue
            if 'label' in summary:
                return summary['label']
        return None

    @property
    def status(self):
        """Return publication status or None if missing."""
        pub_statuses = PUBLICATION_STATUS_PATH.find(self._publication)
        # FIXME Can we have more than one pub status?
        if len(pub_statuses) == 1 and pub_statuses[0].value:
            return pub_statuses[0].value
        else:
            return None

    @property
    def is_classified(self):
        """Return True if publication has at least one 3 or 5 level UKA subject."""
        SUBJECT_PREFIX = 'https://id.kb.se/term/uka/'
        for code in self.subject_codes:
            if not code.startswith(SUBJECT_PREFIX):
                continue
            short = code[len(SUBJECT_PREFIX):]
            if len(short) == 3 or len(short) == 5:
                return True
        return False

    @property
    def subjects(self):
        """Return a list of all subjects."""
        subjects = SUBJECT_PATH.find(self._publication)
        return [subj.value for subj in subjects if subj.value]

    @subjects.setter
    def subjects(self, subjects):
        """Set publication subjects to supplied list."""
        if "instanceOf" not in self._publication:
            self._publication["instanceOf"] = {}
        self._publication["instanceOf"]["subject"] = subjects

    def add_subjects(self, subjects):
        """Add a list of subjects to the publication.

        Each subject is flagged with "Autoclassified by Swepub"."""
        if 'instanceOf' not in self._publication:
            self._publication['instanceOf'] = {}
        if 'subject' not in self._publication['instanceOf']:
            self._publication['instanceOf']['subject'] = []
        flag = "Autoclassified by Swepub"
        marked_subjects = [self._add_note(subj, flag) for subj in subjects]
        self._publication['instanceOf']['subject'].extend(marked_subjects)

    def _add_note(self, obj, text):
        if 'hasNote' not in obj:
            obj['hasNote'] = []
        note = {
            "@type": "Note",
            "label": text
        }
        obj['hasNote'].append(note)
        return obj

    @property
    def keywords(self):
        """Return a list of keywords (non-uka/hsv subjects)."""
        subjects = self.subjects
        keywords = []
        for subj in subjects:
            if 'inScheme' in subj and 'code' in subj['inScheme']:
                code = subj['inScheme']['code']
                if code == "hsv" or code == "uka.se":
                    continue
            if 'prefLabel' in subj:
                keywords.append(subj['prefLabel'])
        return keywords

    @property
    def subject_codes(self):
        """Return a list of all subject identifiers."""
        return [subj['@id'] for subj in self.subjects if '@id' in subj]

    @property
    def creator_count(self):
        """Return creator count or None if missing."""
        creator_count = CREATORCOUNT_PATH.find(self._publication)
        if len(creator_count) != 1:
            return None
        count = creator_count[0].value
        if not count:
            return None
        try:
            return int(count)
        except ValueError:
            return None

    def count_creators(self):
        """Return actual creator count based on publication and output type."""
        # Reports need to be handled separately
        if self.is_report:
            return self._count_creators_report()

        roles = AUT_ROLES
        if self.has_editors:
            roles = EDT_ROLES
        return self._simple_count_creators(roles)

    def _count_creators_report(self):
        edt_count = 0
        count = 0
        for contribution in CONTRIB_PATH.find(self._publication):
            if contribution.value and 'role' in contribution.value:
                for role in contribution.value['role']:
                    if role['@id'] in AUT_ROLES:
                        count += 1
                        # If we find an `AUT_ROLE`, we don't care about other roles
                        break
                    elif role['@id'] in EDT_ROLES:
                        edt_count += 1

        # If a report only has editors, we return that count
        if count == 0 and edt_count > 0:
            return edt_count
        # otherwise, we only count aut/cre
        else:
            return count

    def _simple_count_creators(self, roles):
        count = 0
        for contribution in CONTRIB_PATH.find(self._publication):
            if contribution.value and 'role' in contribution.value:
                for role in contribution.value['role']:
                    if role['@id'] in roles:
                        count += 1
                        # We only count max one role per contribution
                        break
        return count

    @property
    def has_editors(self):
        """Return True if publication is proceeding or collection."""
        genreforms = GENREFORM_PATH.find(self._publication)
        has_editors = False
        for gf in genreforms:
            if gf.value in EDT_TYPES:
                has_editors = True
                break
        return has_editors

    @property
    def is_report(self):
        """Return True if publication is report."""
        genreforms = GENREFORM_PATH.find(self._publication)
        is_report = False
        for gf in genreforms:
            if gf.value in REPORT_TYPES:
                is_report = True
                break
        return is_report

    @property
    def level(self):
        """Return the publication's level according to the Swedish List."""
        if ('instanceOf' not in self._publication
                or 'genreForm' not in self._publication['instanceOf']):
            return None

        for gform in self._publication['instanceOf']['genreForm']:
            # Peer-reviewed always trumps non-peer-reviewed
            if '@id' in gform and gform['@id'] == Level.PEERREVIEWED.value:
                return Level.PEERREVIEWED

            if '@id' in gform and gform['@id'] == Level.NONPEERREVIEWED.value:
                return Level.NONPEERREVIEWED

        return None

    @level.setter
    def level(self, level):
        """Set the publication's level."""
        # Ensure that the publication is unmarked
        self._publication = self._purge_markings(self._publication)
        if level is None:
            return

        if 'instanceOf' not in self._publication:
            self._publication['instanceOf'] = {}
        if 'genreForm' not in self._publication['instanceOf']:
            self._publication['instanceOf']['genreForm'] = []
        genreforms = self._publication['instanceOf']['genreForm']
        genreforms.append({'@id': level.value})
        self._publication['instanceOf']['genreForm'] = genreforms

    def _purge_markings(self, publication):
        if 'instanceOf' not in publication:
            return publication
        if 'genreForm' not in publication['instanceOf']:
            return publication
        genreforms = publication['instanceOf']['genreForm']
        new_gforms = [gform for gform in genreforms if _is_unmarked(gform)]
        publication['instanceOf']['genreForm'] = new_gforms
        return publication

    def ukas(self):
        """Return a unique list of all UKAs"""
        ukas = UKA_PATH.find(self._publication)
        return list(set([uka.value for uka in ukas if uka.value]))

    @property
    def has_duplicate_contributor_persons(self):
        """Returns True if publication has more than one contributor person \
        with same identifiedBy, givenName, familyName and role."""
        try:
            contributions = self._publication.get('instanceOf').get('contribution')
            p: dict
            persons = [p for p in contributions if p.get('agent') and p.get('agent').get('@type') == "Person"]
        except AttributeError:
            return False
        # Compare two or more persons
        if len(persons) < 2:
            return False
        # Compare person a and the next person in the range, person b
        for person_a_index in range(0, len(persons) - 1):
            for person_b_index in range(person_a_index + 1, len(persons)):
                person_a = persons[person_a_index]
                person_b = persons[person_b_index]
                agent_a = person_a.get('agent')
                agent_b = person_b.get('agent')
                # Compare identifiedBy by converting to sets
                identified_by_set_a = {self._tuplify_dicts_recursively(d) for d in agent_a.get('identifiedBy', [])}
                identified_by_set_b = {self._tuplify_dicts_recursively(d) for d in agent_b.get('identifiedBy', [])}
                if identified_by_set_a == identified_by_set_b:
                    # Found matching identifiedBy's
                    # Let's check names and roles
                    if all([agent_a.get('givenName'), agent_a.get('familyName'), agent_b.get('givenName'), agent_b.get('familyName')]):
                        person_a_givenName = agent_a.get('givenName').strip().lower()
                        person_a_familyName = agent_a.get('familyName').strip().lower()
                        person_b_givenName = agent_b.get('givenName').strip().lower()
                        person_b_familyName = agent_b.get('familyName').strip().lower()
                        if person_a_givenName == person_b_givenName and person_a_familyName == person_b_familyName:
                            # Found matching name
                            # Compare roles by converting to sets
                            roles_list_a = person_a.get('role', [])
                            roles_set_a = set(tuple(d.items()) for d in roles_list_a)
                            roles_list_b = person_b.get('role', [])
                            roles_set_b = set(tuple(d.items()) for d in roles_list_b)
                            if roles_set_a == roles_set_b:
                                return True
        return False

    @staticmethod
    def _tuplify_dicts_recursively(dictionary):
        tuplified = []
        for k, v in dictionary.items():
            tuplified.append((k, Publication._tuplify_dicts_recursively(v) if isinstance(v, dict) else v))
        return tuple(sorted(tuplified))

    @property
    def is_article(self):
        articles = itertools.chain.from_iterable(article_path.find(self._publication) for article_path in ARTICLE_PATHS)
        article_values = [article.value for article in articles if article.value]
        return len(article_values) > 0

    @property
    def missing_issn_or_any_empty_issn(self):
        return len(self.issns) == 0 or any(issn.strip() == '' for issn in self.issns)

    @property
    def get_publication_status_list(self):
        notes = []
        if self._publication.get('instanceOf') and self._publication.get('instanceOf').get('hasNote'):
            notes = self._publication.get('instanceOf').get('hasNote')
        publication_status = [note.get('@id') for note in notes if
                              note.get('@type') and note.get('@type') == 'PublicationStatus']
        return publication_status

    @property
    def uka_swe_classification_list(self):
        """Returns a list of all uka classifications in Swedish with code and prefLabel for each"""
        classification_list = []
        uka_prefix = "https://id.kb.se/term/uka/"
        swe_lang_id = "https://id.kb.se/language/swe"
        for subj in self._publication.get("instanceOf", {}).get("subject", {}):
            if subj.get("@type", "") == "Topic":
                code = subj.get("@id")
                if not code:
                    continue
                if not code.startswith(uka_prefix):
                    continue
                if subj.get("language", {}).get("@id", "") == swe_lang_id:
                    code = subj.get("code")
                    label = subj.get("prefLabel")
                    cl_string = f"{code}" if code else ""
                    cl_string += f" {label}" if label else ""
                    if cl_string:
                        classification_list.append(cl_string)
        return classification_list


def _is_unmarked(gform):
    levels = [Level.PEERREVIEWED.value, Level.NONPEERREVIEWED.value]
    return '@id' not in gform or gform['@id'] not in levels


def audit(body):    
    initial_val = (Publication(body), AuditEvents())
    (updated_publication, audit_events) = reduce(lambda acc, auditor: auditor.audit(*acc), auditors, initial_val)
    return updated_publication, audit_events
