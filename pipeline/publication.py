from pipeline.util import *

import itertools
import datetime
from dateutil.parser import parse as parse_date
from html import unescape

from simplemma.langdetect import lang_detector
from bs4 import BeautifulSoup
from unidecode import unidecode


"""Max length in characters to compare text"""
MAX_LENGTH_STRING_TO_COMPARE = 1000

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
    "https://id.kb.se/term/swepub/output/publication/edited-book",
    "https://id.kb.se/term/swepub/output/publication/journal-issue",
    "https://id.kb.se/term/swepub/output/conference/proceeding"
]
REPORT_OUTPUT_TYPES = [
    "https://id.kb.se/term/swepub/output/publication/report"
]
EDT_TYPES = EDT_PUB_TYPES + EDT_OUTPUT_TYPES
REPORT_TYPES = REPORT_PUB_TYPES + REPORT_OUTPUT_TYPES

# TODO: Is this list actually up to date?
ARTICLE_TYPES = [
    "https://id.kb.se/term/swepub/JournalArticle",
    "https://id.kb.se/term/swepub/journal-article",
    "https://id.kb.se/term/swepub/magazine-article",
    "https://id.kb.se/term/swepub/newspaper-article",
    "https://id.kb.se/term/swepub/journal-issue",
]

NO_PARENS_REGEX = re.compile(r"\([^()]*\)")

class Publication:
    """Abstract publication format and API to access its properties """

    """Match ratios for various pubications fields, see SequenceMatcher """
    STRING_MATCH_RATIO_MAIN_TITLE = 0.9
    STRING_MATCH_RATIO_SUB_TITLE = 0.9
    STRING_MATCH_RATIO_SUMMARY = 0.9

    PUBLICATION_STATUS_RANKING = {
        'https://id.kb.se/term/swepub/Published': 1,
        'https://id.kb.se/term/swepub/EpubAheadOfPrint/OnlineFirst': 2,
        'https://id.kb.se/term/swepub/InPrint': 3,
        'https://id.kb.se/term/swepub/Accepted': 4,
        'https://id.kb.se/term/swepub/Submitted': 5,
        'https://id.kb.se/term/swepub/Preprint': 6
    }

    def __init__(self, body):
        self._body = body

    def __eq__(self, publication):
        """ Two publication is considered eq if whole body is equal """
        return self.body == publication.body

    @property
    def id(self):
        """Return local publication id"""
        if '@id' in self.body:
            return self.body['@id']
        return None

    @property
    def source_org(self):
        """Returns org code"""
        return self.body.get("meta", {}).get("assigner", {}).get("label")

    @property
    def body(self):
        """Return raw publication data"""
        return self._body

    @property
    def elements_size(self):
        """Return number of elements to determine if this is a master publication"""
        size = 0
        if 'instanceOf' in self.body:
            size = sum(len(x) for x in self.body['instanceOf'].values())
        return size

    @property
    def main_title(self):
        """Return value of instanceOf.hasTitle[?(@.@type=="Title")].mainTitle if it exists and
            there is no subtitle.
            If a subtitle exist then the return value is split at the first colon and the first string
            is returned,
            i.e 'main:sub' returns main.
            None otherwise """
        has_title_array = self.body.get('instanceOf', {}).get('hasTitle', [])
        main_title_raw = None
        sub_title_raw = None
        for h_t in has_title_array:
            if isinstance(h_t, dict) and h_t.get('@type') == 'Title':
                main_title_raw = h_t.get('mainTitle')
                sub_title_raw = h_t.get('subtitle')
                break
        if not empty_string(sub_title_raw):
            return main_title_raw
        main_title, sub_title = split_title_subtitle_first_colon(main_title_raw)
        if not empty_string(main_title):
            return main_title
        else:
            return None

    @property
    def sub_title(self):
        sub_title_array = self.body.get('instanceOf', {}).get('hasTitle', [])
        main_title_raw = None
        for h_t in sub_title_array:
            if isinstance(h_t, dict) and h_t.get('@type') == 'Title' and h_t.get('subtitle'):
                return h_t.get('subtitle')
            else:
                main_title_raw = h_t.get('mainTitle')
                break
        main_title, sub_title = split_title_subtitle_first_colon(main_title_raw)
        if not empty_string(sub_title):
            return sub_title
        else:
            return None

    @property
    def language(self):
        """Return the publication's language."""
        return get_language(self.body)

    @property
    def summary(self):
        return get_summary(self.body)

    @property
    def summaries(self):
        """Return a list of all summaries."""
        return self.body.get('instanceOf', {}).get('summary', [])

    def get_english_summary(self):
        """Get summary text in English if it exists."""
        return self._get_lang_summary("eng")

    def get_swedish_summary(self):
        """Get summary text in Swedish if it exists."""
        return self._get_lang_summary("swe")

    def _get_lang_summary(self, lang):
        """Get summary for specified language if it exists."""
        for summary in self.summaries:
            if "language" not in summary:
                continue
            if "code" not in summary["language"]:
                continue
            if summary["language"]["code"] != lang:
                continue
            if "label" in summary:
                return summary["label"]
        return None

    @property
    def publication_date(self):
        return get_publication_date(self.body)

    @property
    def year(self):
        """Return the publication year as a string or None if missing or invalid."""
        pub_year = self.publication_date
        if pub_year:
            try:
                parsed_date = parse_date(pub_year)
                return '{}'.format(parsed_date.year)
            except ValueError:
                return None
        return None

    @property
    def issns(self):
        """Return a list of all ISSNs ordered by importance."""
        issns = set()
        for is_part_of in self.body.get("isPartOf", []) + self.body.get("hasSeries", []):
            if isinstance(is_part_of, dict):
                for el in is_part_of.get("identifiedBy", []) + is_part_of.get("indirectlyIdentifiedBy", []):
                    if el.get("@type") == "ISSN":
                        issns.add(el.get("value"))
                for series in is_part_of.get("hasSeries", []):
                    for el in series.get("identifiedBy", []) + series.get("indirectlyIdentifiedBy", []):
                        if el.get("@type") == "ISSN":
                            issns.add(el.get("value"))
        for issn in self.body.get("identifiedBy", []) + self.body.get("indirectlyIdentifiedBy", []):
            if isinstance(issn, dict) and issn.get("@type") == "ISSN":
                issns.add(issn.get("value"))
        return [issn for issn in issns if issn]

    @property
    def publication_information(self):
        """ Return first occurrence of PublicationInformation from publication field"""
        for p in self.body.get('publication', []):
            if isinstance(p, dict) and p.get('@type') == 'Publication':
                return PublicationInformation(p)
        return None

    @publication_information.setter
    def publication_information(self, publication_information):
        """ Sets array for publication_information from array of PublicationInformation objects """
        self._body['publication'] = [publication_information.body]

    @property
    def usage_and_access_policy(self):
        """Return a list of usage and access policies or None if unset"""
        return self.body.get("usageAndAccessPolicy", None)

    @usage_and_access_policy.setter
    def usage_and_access_policy(self, policies):
        """Sets usage and access policies to supplied list"""
        self._body["usageAndAccessPolicy"] = policies

    @property
    def usage_and_access_policy_by_type(self):
        """Return usage and access policies split into categories
        The categories are access policies, embargoes, links, and other."""
        access_policies = []
        embargoes = []
        links = []
        others = []
        for item in self.usage_and_access_policy:
            if item.get("@type") == "AccessPolicy":
                access_policies.append(item)
            elif item.get("@type") == "Embargo":
                embargoes.append(item)
            elif item.get("@id"):
                links.append(item)
            else:
                others.append(item)
        return access_policies, embargoes, links, others

    @property
    def genre_form(self):
        return genre_form(self.body)

    def add_genre_form(self, new_genre_forms):
        """ Sets array of genreforms for instanceOf.genreForm.[*].@id """
        genre_forms = list(set(new_genre_forms) - set(self.genre_form))
        for genre_form in genre_forms:
            self.body['instanceOf']['genreForm'].append({'@id': genre_form})

    @property
    def contributions(self):
        """ Return array of Contribution objects from instanceOf.contribution """
        contributions = []
        contributions_json_array = self.body.get('instanceOf', {}).get('contribution', [])
        if contributions_json_array is not None:
            for c in contributions_json_array:
                contributions.append(Contribution(c))
        return contributions

    @contributions.setter
    def contributions(self, contributions):
        """ Sets array for instanceOf.contribution from array of Contributions objects """
        self._body['instanceOf']['contribution'] = [c.body for c in contributions]

    @property
    def publication_status(self):
        """ Return value for instanceOf.hasNote[?(@.@type=="PublicationStatus")].@id if exist, None otherwise """
        publication_date_array = self.body.get('instanceOf', {}).get('hasNote', [])
        pub_statuses = []
        for p_d in publication_date_array:
            if isinstance(p_d, dict) and p_d.get('@type') == 'PublicationStatus':
                pub_statuses.append(p_d.get('@id'))
        # FIXME Can we have more than one pub status?
        if len(pub_statuses) == 1 and pub_statuses[0]:
            return pub_statuses[0]
        else:
            return None

    @publication_status.setter
    def publication_status(self, new_status):
        """ Sets status value in instanceOf.hasNote[?(@.@type=="PublicationStatus")].@id """
        i = 0
        for n in self.body.get('instanceOf', {}).get('hasNote', []):
            if n['@type'] == 'PublicationStatus':
                self._body['instanceOf']['hasNote'][i]['@id'] = new_status
                break
            else:
                i += 1

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
    def is_autoclassified(self):
        for subject in self.subjects:
            for note in subject.get("hasNote", []):
                if note.get("label", "") == "Autoclassified by Swepub":
                    return True
        return False

    # language: e.g. https://id.kb.se/language/swe or https://id.kb.se/language/eng
    def keywords(self, language=None):
        subjects = self.subjects
        keywords = []
        for subj in subjects:
            if language and subj.get("language", {}).get("@id", "") != language:
                continue
            if "inScheme" in subj and "code" in subj["inScheme"]:
                code = subj["inScheme"]["code"]
                if code == "hsv" or code == "uka.se":
                    continue
            if "prefLabel" in subj:
                keywords.append(subj["prefLabel"])
        return keywords

    @property
    def subject_codes(self):
        """Return a list of all subject identifiers."""
        return [subj['@id'] for subj in self.subjects if '@id' in subj]

    @property
    def subjects(self):
        """ Return array of subjects from instanceOf.subject """
        subjects_json_array = self.body.get('instanceOf', {}).get('subject', [])
        if subjects_json_array is None:
            return []
        return subjects_json_array

    @subjects.setter
    def subjects(self, subjects):
        """ Sets array of subjects for instanceOf.subject """
        self._body['instanceOf']['subject'] = subjects

    def add_subjects(self, subjects):
        """Add a list of subjects to the publication.

        Each subject is flagged with "Autoclassified by Swepub"."""
        if "instanceOf" not in self._body:
            self._body["instanceOf"] = {}
        if "subject" not in self.body["instanceOf"]:
            self._body["instanceOf"]["subject"] = []
        self._body["instanceOf"]["subject"].extend(subjects)

    @property
    def creator_count(self):
        """Return creator count or None if missing."""
        for c_c in self.body.get('instanceOf', {}).get('hasNote', []):
            if isinstance(c_c, dict) and c_c.get("@type") == "CreatorCount":
                count = c_c.get("label")
                if not count:
                    return None
                try:
                    return int(count)
                except ValueError:
                    return None
        return None

    @creator_count.setter
    def creator_count(self, new_creator_count):
        """ Sets status value in instanceOf.[*].hasNote[?(@.@type=="CreatorCount")].label """
        i = 0
        for n in self.body.get('instanceOf', {}).get('hasNote', []):
            if n['@type'] == 'CreatorCount':
                self._body['instanceOf']['hasNote'][i]['label'] = new_creator_count
                break
            else:
                i += 1

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

        for contribution in self.body.get('instanceOf', {}).get('contribution', []):
            if isinstance(contribution, dict) and contribution.get("@type") == "Contribution":
                for role in contribution.get('role', []):
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
        for contribution in self.body.get('instanceOf', {}).get('contribution', []):
            if isinstance(contribution, dict) and contribution.get("@type") == "Contribution":
                for role in contribution.get('role', []):
                    if role['@id'] in roles:
                        count += 1
                        # We only count max one role per contribution
                        break
        return count

    @property
    def has_editors(self):
        """Return True if publication is proceeding or collection."""
        has_editors = False
        for g_f in genre_form(self.body):
            if g_f in EDT_TYPES:
                has_editors = True
                break
        return has_editors

    @property
    def is_report(self):
        """Return True if publication is report."""
        is_report = False
        for g_f in genre_form(self.body):
            if g_f in REPORT_TYPES:
                is_report = True
                break
        return is_report

    @property
    def level(self):
        """Return the publication's level according to the Swedish List."""
        if ('instanceOf' not in self.body
                or 'genreForm' not in self.body['instanceOf']):
            return None

        for gform in self.body['instanceOf']['genreForm']:
            # Peer-reviewed always trumps non-peer-reviewed
            if '@id' in gform and gform['@id'] == str(Level.PEERREVIEWED):
                return Level.PEERREVIEWED

            if '@id' in gform and gform['@id'] == str(Level.NONPEERREVIEWED):
                return Level.NONPEERREVIEWED

        return None

    @level.setter
    def level(self, level):
        """Set the publication's level."""
        # Ensure that the publication is unmarked
        self._body = self._purge_markings(self.body)
        if level is Level.NONE:
            return

        if 'instanceOf' not in self.body:
            self.body['instanceOf'] = {}
        if 'genreForm' not in self.body['instanceOf']:
            self.body['instanceOf']['genreForm'] = []
        genreforms = self.body['instanceOf']['genreForm']
        genreforms.append({'@id': str(level)})
        self.body['instanceOf']['genreForm'] = genreforms

    @staticmethod
    def _is_unmarked(gform):
        levels = [str(Level.PEERREVIEWED), str(Level.NONPEERREVIEWED)]
        return '@id' not in gform or gform['@id'] not in levels

    def _purge_markings(self, publication):
        if 'instanceOf' not in publication:
            return publication
        if 'genreForm' not in publication['instanceOf']:
            return publication
        genreforms = publication['instanceOf']['genreForm']
        new_gforms = [gform for gform in genreforms if self._is_unmarked(gform)]
        publication['instanceOf']['genreForm'] = new_gforms
        return publication

    def ukas(self, skip_autoclassified=False):
        """Return a unique list of all UKAs"""
        ukas = set()
        for uka in self.body.get('instanceOf', {}).get('subject', []):
            if skip_autoclassified:
                for note in uka.get("hasNote", []):
                    if note.get("label", "") == "Autoclassified by Swepub":
                        continue
            if isinstance(uka, dict) and uka.get("inScheme", {}).get("code", "") == "uka.se":
                ukas.add(uka.get("code"))
        return list([uka for uka in ukas if uka])

    @property
    def has_duplicate_contributor_persons(self):
        """Returns True if publication has more than one contributor person \
        with same identifiedBy, givenName, familyName and role."""
        try:
            contributions = self.body.get('instanceOf').get('contribution')
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
                    if all([agent_a.get('givenName'), agent_a.get('familyName'), agent_b.get('givenName'),
                            agent_b.get('familyName')]):
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
        for article in self.body.get("instanceOf", {}).get("genreForm", []):
            if isinstance(article, dict) and article.get("@id") in ARTICLE_TYPES:
                return True
        return False

    @property
    def notes(self):
        """ Return array of notes from instanceOf.[*].hasNote[?(@.@type=="Note")].label """
        notes = set()
        for n in self.body.get('instanceOf', {}).get('hasNote', []):
            if isinstance(n, dict) and n.get('@type') == 'Note':
                notes.add(n.get('label'))
        return [n for n in notes if n]

    def add_notes(self, new_notes):
        """ Sets array of notes for instanceOf.[*].hasNote[?(@.@type=="Note")].label """
        new_notes = list(set(new_notes) - set(self.notes))
        for new_note in new_notes:
            self.body['instanceOf']['hasNote'].append({'@type': 'Note', 'label': new_note})

    @property
    def has_series(self):
        """ Return array of HasSeries objects from hasSeries """
        has_series_objects = []
        has_series_json_array = self.body.get('hasSeries', [])
        for serie in has_series_json_array:
            if isinstance(serie, dict):
                has_series_objects.append(HasSeries(serie))
        return has_series_objects

    def add_series(self, is_part_of):
        new_has_series = is_part_of.has_series
        self_has_series = self.has_series
        for new_has_serie in new_has_series:
            if new_has_serie not in self_has_series:
                self_has_series.append(new_has_serie)
        if len(self_has_series) > 0:
            self.body['hasSeries'] = [has_serie.body for has_serie in self_has_series]

    @property
    def missing_issn_or_any_empty_issn(self):
        return len(self.issns) == 0 or any(issn.strip() == '' for issn in self.issns)

    @property
    def get_publication_status_list(self):
        notes = []
        if self.body.get('instanceOf') and self.body.get('instanceOf').get('hasNote'):
            notes = self.body.get('instanceOf').get('hasNote')
        publication_status = [note.get('@id') for note in notes if
                              note.get('@type') and note.get('@type') == 'PublicationStatus']
        return publication_status

    @property
    def uka_swe_classification_list(self):
        """Returns a list of all uka classifications in Swedish with code and prefLabel for each"""
        classification_list = []
        uka_prefix = "https://id.kb.se/term/uka/"
        swe_lang_id = "https://id.kb.se/language/swe"
        for subj in self.body.get("instanceOf", {}).get("subject", {}):
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

    @property
    def identifiedby_isbns(self):
        """Return a list of all ISBN (including isPartOf)"""
        isbns = set()
        for isbn in self.body.get("identifiedBy", []):
            if isinstance(isbn, dict) and isbn.get("@type") == "ISBN":
                isbns.add(isbn.get("value"))
        for is_part_of in self.body.get("isPartOf", {}):
            for isbn in is_part_of.get("identifiedBy", []):
                if isinstance(isbn, dict) and isbn.get("@type") == "ISBN":
                    isbns.add(isbn.get("value"))
        return [isbn for isbn in isbns if isbn]

    @property
    def identifiedby_dois(self):
        """Returns a list of all DOI identifiedBy"""
        dois = set()
        for doi in self.body.get('identifiedBy', []):
            if isinstance(doi, dict) and doi.get("@type") == "DOI":
                dois.add(doi.get("value"))
        return [doi for doi in dois if doi]

    @property
    def identifiedby_ispartof_dois(self):
        """Returns a list of all DOI isPartOf identifiedBy"""
        dois = set()
        for is_part_of in self.body.get('isPartOf', []):
            if isinstance(is_part_of, dict) and "identifiedBy" in is_part_of:
                for doi in is_part_of.get("identifiedBy", []):
                    if doi.get("@type") == "DOI":
                        dois.add(doi.get("value"))
        return [doi for doi in dois if doi]

    @property
    def electroniclocator_uris(self):
        return list(itertools.chain.from_iterable(
            [d.get('uri') for d in self.body['electronicLocator'] if d.get('uri') is not None]
        ))

    def add_doab_download_uris(self, download_uris):
        """Add a MediaObject in electronicLocator for each DOAB download URI
        that's not already in the publication."""
        if 'electronicLocator' not in self._body:
            self._body['electronicLocator'] = []

        # Make sure we don't add URIs that are already in the record
        new_uris = set(download_uris) - set(self.electroniclocator_uris)
        new_electroniclocators = []
        if new_uris:
            for new_uri in new_uris:
                new_electroniclocators.append(
                    {
                        '@type': 'MediaObject',
                        'meta': [
                            {
                                '@type': 'AdminMetadata',
                                'sourceConsulted': [
                                    {
                                        '@type': 'SourceData',
                                        'label': 'Information om ÖT hämtad från DOAB.',
                                        'uri': 'https://www.doabooks.org/',
                                        'date': datetime.datetime.utcnow().replace(
                                            tzinfo=datetime.timezone.utc).isoformat()
                                    }
                                ]
                            }
                        ],
                        'uri': new_uri,
                        'usageAndAccessPolicy': [
                            {
                                '@id': 'https://id.kb.se/policy/oa/gratis'
                            }
                        ]
                    }
                )
            self._body['electronicLocator'].extend(new_electroniclocators)
            return True, new_electroniclocators
        return False

    def add_unpaywall_data(self, doi_object):
        """Add a MediaObject in electronicLocator for the Unpaywall download URI
        if it's not already in the publication."""
        if 'electronicLocator' not in self._body:
            self._body['electronicLocator'] = []

        new_electroniclocator = {
            '@type': 'MediaObject',
            'meta': [
                {
                    '@type': 'AdminMetadata',
                    'sourceConsulted': [
                        {
                            '@type': 'SourceData',
                            'label': 'Information om ÖT hämtad från Unpaywall.',
                            'uri': 'https://unpaywall.org/',
                            'date': datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
                        }
                    ]
                }
            ]
        }

        if not doi_object['is_oa']:
            new_electroniclocator['usageAndAccessPolicy'] = [
                {
                    '@id': 'https://id.kb.se/policy/oa/restricted'
                }
            ]
            self._body['electronicLocator'].append(new_electroniclocator)
            return True, [new_electroniclocator]

        if doi_object['best_oa_location']['url'] not in self.electroniclocator_uris:
            new_electroniclocator['usageAndAccessPolicy'] = [
                {
                    '@id': 'https://id.kb.se/policy/oa/gratis'
                }
            ]
            new_electroniclocator['uri'] = doi_object['best_oa_location']['url']
            version = None
            if doi_object['best_oa_location']['version'] == 'submittedVersion':
                version = 'https://id.kb.se/term/swepub/Submitted'
            elif doi_object['best_oa_location']['version'] == 'acceptedVersion':
                version = 'https://id.kb.se/term/swepub/Accepted'
            elif doi_object['best_oa_location']['version'] == 'publishedVersion':
                version = 'https://id.kb.se/term/swepub/Published'
            if version:
                new_electroniclocator['hasNote'] = [
                    {'@id': version}
                ]

            if doi_object['journal_is_in_doaj']:
                if 'status' not in self._body['instanceOf']:
                    self.body['instanceOf']['status'] = []
                self._body['instanceOf']['status'].append(
                    {'@id': "https://id.kb.se/term/swepub/journal-is-in-doaj"}
                )

            self._body['electronicLocator'].append(new_electroniclocator)
            return True, [new_electroniclocator]
        return False, None

    def add_crossref_data(self, crossref):
        """Enriches publication with Crossref data where applicable"""
        modified_properties = []

        # Crossref metadata API JSON format:
        # https://github.com/CrossRef/rest-api-doc/blob/master/api_format.md

        # publisher => publication Publication / agent Agent label
        # publisher-location => publication Publication / place Place label
        # published-print => publication Publication date
        self._add_crossref_pub_info(crossref, modified_properties)

        # published-online => provisionActivity OnlineAvailability date
        self._add_crossref_provision_activity(crossref, modified_properties)

        # issn-type => isPartOf / identifiedBy ISSN value qualifier
        self._add_crossref_issn(crossref, modified_properties)

        # abstract => summary Summary label
        self._add_crossref_summary(crossref, modified_properties)

        # license => license License @id startDate
        self._add_crossref_license(crossref, modified_properties)

        if modified_properties:
            return True, modified_properties
        return False, modified_properties

    def _add_crossref_pub_info(self, crossref, modified_properties):
        if not self.publication_information:
            self._body["publication"] = [{'@type': 'Publication'}]
        pub_info = self.publication_information

        if crossref.get("publisher") and not pub_info.body.get("agent", {}).get("label"):
            pub_info.agent = {"@type": "Agent", "label": crossref.get("publisher")}
            modified_properties.append({"name": "PublisherAdditionAuditor", "code": "add_publisher", "value": crossref.get("publisher")})

        if crossref.get("publisher-location") and not pub_info.body.get("place", {}).get("label"):
            pub_info.place = {"@type": "Place", "label": crossref.get("publisher-location")}
            modified_properties.append({"name": "PublisherLocationAdditionAuditor", "code": "add_publisher_location", "value": crossref.get("publisher-location")})

        if crossref.get("published-print") and not pub_info.date:
            # https://github.com/CrossRef/rest-api-doc/blob/master/api_format.md#partial-date
            pub_info.date = self._date_from_crossref_date_parts(crossref["published-print"]["date-parts"], year_only=True)
            modified_properties.append({"name": "PublishedPrintAdditionAuditor", "code": "add_published_print", "value": pub_info.date})

        if not pub_info._body.get("meta"):
            pub_info._body["meta"] = []
        pub_info._body["meta"].append(self._crossref_source_consulted())

    def _add_crossref_provision_activity(self, crossref, modified_properties):
        if crossref.get("published-online"):
            if not self._body.get("provisionActivity"):
                self._body["provisionActivity"] = []

            if not any(d.get("@type", "") == "OnlineAvailability" for d in self._body["provisionActivity"]):
                date_to_add = self._date_from_crossref_date_parts(crossref["published-online"]["date-parts"])
                self._body["provisionActivity"].append({
                    "@type": "OnlineAvailability",
                    "date": date_to_add,
                    "meta": [self._crossref_source_consulted()]
                })
                modified_properties.append({"name": "ProvisionActivityAdditionAuditor", "code": "add_published_online", "value": date_to_add})

    def _add_crossref_issn(self, crossref, modified_properties):
        # BEWARE! Crossref spec https://github.com/CrossRef/rest-api-doc/blob/master/api_format.md#issn-with-type
        # has "One of eissn, pissn or lissn" but in actual data they use
        # "electronic" and "print". Also unclear what lissn is.
        new_issns = []
        for c_issn in crossref.get("issn-type", []):
            if c_issn.get("value") not in self.issns and c_issn.get("type") in ["electronic", "print"]:
                new_issns.append(c_issn)
        if new_issns:
            # If there's more than one container-title there's no way of knowing which ISSN(s) it belongs to,
            # so in that case we just skip enrichment.
            # https://github.com/CrossRef/rest-api-doc/issues/11
            if len(crossref.get("container-title", [])) > 1:
                return

            if not self._body.get("isPartOf"):
                self._body["isPartOf"] = []

            new_issn_is_part_of = {"@type": "Work"}
            crossref_container_title = ""
            # Only use container-title if there's no ISBN in the Crossref data. Because if there *is*, we
            # can't know for sure what container-title refers to (ISSN or ISBN).
            if crossref.get("container-title") and not crossref.get("isbn-type"):
                crossref_container_title = unescape(crossref["container-title"][0])
                new_issn_is_part_of["hasTitle"] = [{
                    "@type": "Title",
                    "mainTitle": crossref_container_title
                }]

            new_issn_is_part_of["identifiedBy"] = []
            for new_issn in new_issns:
                if not new_issn.get("type") in ["print", "electronic", "eissn", "pissn"]:
                    continue
                new_id_by = {
                    "@type": "ISSN",
                    "value": new_issn.get("value"),
                }
                if new_issn["type"] in ["electronic", "eissn"]:
                    new_id_by["qualifier"] = "electronic"
                elif new_issn["type"] in ["print", "pissn"]:
                    new_id_by["qualifier"] = "print"
                new_issn_is_part_of["identifiedBy"].append(new_id_by)

            if new_issn_is_part_of["identifiedBy"]:
                new_issn_is_part_of["meta"] = [self._crossref_source_consulted()]
                issn_event_log_value = ", ".join(map(lambda x: f"{x['value']} ({x['@type']})", new_issn_is_part_of["identifiedBy"]))
                if new_issn_is_part_of.get("hasTitle"):
                    issn_event_log_value = f"{crossref_container_title}: {issn_event_log_value}"

                # Now check if there's an existing isPartOf or isPartOf.hasSeries that
                # we should add the new ISSN(s) to
                if crossref_container_title:
                    for outer_is_part_of in self.is_part_of:
                        for is_part_of in [outer_is_part_of] + outer_is_part_of.has_series:
                            if is_part_of.main_title:
                                similarity = get_common_substring_factor(self._get_title_for_comparison(is_part_of.main_title), self._get_title_for_comparison(crossref_container_title))
                                if similarity > 0.6:
                                    found_matching_title = True
                                    is_part_of.add_issns(IsPartOf(new_issn_is_part_of))
                                    modified_properties.append({"name": "ISSNAdditionAuditor", "code": "add_issn", "value": issn_event_log_value})
                                    return

                # ...otherwise, just add the new ISNS(s) as a new IsPartOf
                self._body["isPartOf"].append(new_issn_is_part_of)
                modified_properties.append({"name": "ISSNAdditionAuditor", "code": "add_issn", "value": issn_event_log_value})

    @staticmethod
    def _get_title_for_comparison(s):
        return re.sub(NO_PARENS_REGEX, "", unescape(s))

    def _add_crossref_summary(self, crossref, modified_properties):
        # "Abstract as a JSON string or a JATS XML snippet encoded into a JSON string"
        c_summary = crossref.get("abstract")
        if c_summary and not self.summary:
            new_summary_label = ""
            # If we're dealing with JATS XML, do it one way...
            if c_summary.startswith("<jats"):
                soup = BeautifulSoup(c_summary, "lxml")
                # There can be multiple elements: <jats:title>, several <jats:p>, etc.
                # Get rid of the title and its content (which is always (?) just
                # "Abstract"), keep everything else.
                if soup.find("jats:title"):
                    soup.find("jats:title").extract()
                # Get the text without tags
                extracted_abstract = soup.get_text()
                if extracted_abstract:
                    new_summary_label = extracted_abstract
            # Otherwise just strip any tags
            else:
                soup = BeautifulSoup(c_summary, "html.parser")
                cleaned_abstract = soup.get_text()
                if cleaned_abstract:
                    new_summary_label = cleaned_abstract
            if new_summary_label:
                new_summary = {
                    "@type": "Summary",
                    "label": new_summary_label
                }
                # Now try to figure out the language
                predicted_lang, lang_score = lang_detector(new_summary_label, lang=("sv", "en"))[0]
                if predicted_lang in ["sv", "en"] and lang_score >= 0.5:
                    if predicted_lang == "en":
                        new_summary["language"] = {
                            "@type": "Language",
                            "@id": "https://id.kb.se/language/eng",
                            "code": "eng"
                        }
                    elif predicted_lang == "sv":
                        new_summary["language"] = {
                            "@type": "Language",
                            "@id": "https://id.kb.se/language/swe",
                            "code": "swe"
                        }
                new_summary["meta"] = [self._crossref_source_consulted()]
                self._body["instanceOf"]["summary"] = [new_summary]
                modified_properties.append({"name": "SummaryAdditionAuditor", "code": "add_summary", "value": new_summary_label})

    def _add_crossref_license(self, crossref, modified_properties):
        c_license = crossref.get("license")
        if c_license:
            for license in c_license:
                # Crossref content-version and Swepub publication status must match.
                # "vor" is equal to Swepub's Published.
                # "am" is equal to Swepub's Accepted.
                # If there is no publication status in the Swepub publication,
                # it's treated as Published.
                if (
                    (
                        license["content-version"] == "vor"
                        and self.publication_status == "https://id.kb.se/term/swepub/Published"
                    )
                    or (
                        license["content-version"] == "am"
                        and self.publication_status == "https://id.kb.se/term/swepub/Accepted"
                    )
                    or (
                        license["content-version"] == "vor"
                        and not self.publication_status
                    )
                ):
                    # 'start' isn't always present, despite it being required by the spec
                    if not license.get("start"):
                        continue
                    if not self._body.get("license"):
                        self._body["license"] = []
                    self._body["license"].append(
                        {
                            "@id": license["URL"],
                            "@type": "License",
                            "startDate": license["start"]["date-time"],
                            "meta": [self._crossref_source_consulted()],
                        }
                    )
                    modified_properties.append({"name": "LicenseAdditionAuditor", "code": "add_license", "value": license["URL"]})
                    continue

    @staticmethod
    def _date_from_crossref_date_parts(date_parts, year_only=False):
        if year_only:
            return str(date_parts[0][0])
        return "-".join(f"{n}".zfill(2) for n in date_parts[0])

    @staticmethod
    def _crossref_source_consulted():
        return {
            "@type": "AdminMetadata",
            "sourceConsulted": [
                {
                    "@type": "SourceData",
                    "label": "Information hämtad från Crossref.",
                    "uri": "https://crossref.org/",
                    "date": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
                }
            ]
        }

    @property
    def electronic_locators(self):
        """ Return array of ElectronicLocator objects from electronicLocator field """
        electronic_locators = []
        electronic_locators_json_array = self.body.get('electronicLocator', [])
        for e in self.body.get('electronicLocator', []):
            if isinstance(e, dict):
                electronic_locators.append(ElectronicLocator(e))
        return electronic_locators

    @electronic_locators.setter
    def electronic_locators(self, electronic_locators):
        """ Sets array for electronicLocator field from array of ElectronicLocator objects """
        self._body['electronicLocator'] = [e.body for e in electronic_locators]

    @property
    def is_part_of(self):
        """ Return array of IsPartOf objects from isPartOf """
        is_part_of = []
        for p in self.body.get('isPartOf', []):
            if isinstance(p, dict):
                is_part_of.append(IsPartOf(p))
        return is_part_of

    @is_part_of.setter
    def is_part_of(self, is_part_of):
        """ Sets array for isPartOf from array of IsPartOf objects """
        self._body['isPartOf'] = [part.body for part in is_part_of]

    @property
    def identifiedby_ids(self):
        """Return array of items in identifiedBy"""
        return self.get_identifiedby_ids()

    @identifiedby_ids.setter
    def identifiedby_ids(self, identifiedby_ids):
        """Sets identifiedBy array, ex identifiedby_ids= [{'@type': 'DOI', 'value': 'DOI_1'}] """
        self._body['identifiedBy'] = identifiedby_ids

    @property
    def indirectly_identifiedby_ids(self):
        """Return array of items in indirectlyIdentifiedBy"""
        return self.get_indirectly_identifiedby_ids()

    @indirectly_identifiedby_ids.setter
    def indirectly_identifiedby_ids(self, indirectly_identifiedby_ids):
        """Sets indirectlyIdentifiedBy array, ex indirectly_identifiedby_ids= [{'@type': 'DOI', 'value': 'DOI_1'}] """
        self._body['indirectlyIdentifiedBy'] = indirectly_identifiedby_ids

    def get_identifiedby_ids(self, identifier=''):
        """Return either identifiedBy ids values if identifier is set otherwise whole identifiedBy array """
        return get_ids(self.body, 'identifiedBy', identifier)

    def get_indirectly_identifiedby_ids(self, identifier=''):
        """Return either indirectlyIdentifiedBy ids values if identifier is set
        otherwise whole indirectlyIdentifiedBy array """
        return get_ids(self.body, 'indirectlyIdentifiedBy', identifier)

    def has_same_main_title(self, publication):
        """True if publication has the same main title"""
        return compare_text(self.main_title, publication.main_title, self.STRING_MATCH_RATIO_MAIN_TITLE, MAX_LENGTH_STRING_TO_COMPARE)

    def has_same_sub_title(self, publication):
        """True if publication has the same sub title"""
        return compare_text(self.sub_title, publication.sub_title, self.STRING_MATCH_RATIO_SUB_TITLE, MAX_LENGTH_STRING_TO_COMPARE)

    def has_same_summary(self, publication):
        """True if publication has the same summary"""
        return compare_text(self.summary, publication.summary, self.STRING_MATCH_RATIO_SUMMARY, MAX_LENGTH_STRING_TO_COMPARE)

    def has_same_genre_form(self, publication):
        """True if publication has all the genreform the same"""
        if self.genre_form and publication.genre_form:
            return set(self.genre_form) == set(publication.genre_form)
        return False

    def has_higher_publication_status_ranking(self, publication):
        """ True of publication.publication_status is higher than self.publication_status using
         self.PUBLICATION_STATUS_RANKING """

    def has_worse_publication_status_ranking(self, publication):
        """ True if self.publication_status is worse than given publication.publication_status
        based on self.PUBLICATION_STATUS_RANKING. I.e. has publication.PUBLICATION_STATUS_RANKING  has
        precedence over self.PUBLICATION_STATUS_RANKING """
        try:
            master_ranking = self.PUBLICATION_STATUS_RANKING[self.publication_status]
        except KeyError:
            master_ranking = len(self.PUBLICATION_STATUS_RANKING) + 1
        try:
            publication_ranking = self.PUBLICATION_STATUS_RANKING[publication.publication_status]
        except KeyError:
            publication_ranking = len(self.PUBLICATION_STATUS_RANKING) + 1
        return publication_ranking < master_ranking


class Contribution:
    """Abstract Contribution format and API to access its properties
    Populated by instanceOf.contribution in Publication. """

    def __init__(self, body):
        self._body = body
        self._agent_family_name = self.body.get('agent', {}).get('familyName', None)
        self._agent_given_name = self.body.get('agent', {}).get('givenName', None)
        self._agent_name = self.body.get('agent', {}).get('name', None)
        self._agent_identified_by = self.body.get('agent', {}).get('identifiedBy', [])
        self._agent_type = self.body.get('agent', {}).get('@type', None)
        self._agent = self.body.get('agent', {})

    def __eq__(self, other):
        """ Two contributions are equal if name or (given and family name) are the same """
        if not isinstance(other, self.__class__):
            return NotImplemented
        if id(self) == id(other):
            return True
        # Contributions with missing name will never match
        if not self.agent_name or not other.agent_name:
            return False
        return self.agent_name == other.agent_name

    def __hash__(self):
        if self.agent_name:
            return hash(self.agent_name)
        else:
            return id(self)

    @property
    def body(self):
        """Return raw body data"""
        return self._body

    @property
    def agent(self):
        return self._agent

    @property
    def agent_family_name(self):
        """Return value for agent.familyName, None if not exist """
        return self._agent_family_name

    @property
    def agent_given_name(self):
        """Return value for agent.givenName if exist, None otherwise """
        return self._agent_given_name

    @property
    def agent_name(self):
        """Return agent.name as comma-separated string if exist, otherwise agent_given_name + ' ' + agent_family_name"""
        if self._agent_name and len(self._agent_name) > 0:
            if isinstance(self._agent_name, list):
                return ', '.join(self._agent_name)
            return self._agent_name
        else:
            return safe_concat(self.agent_family_name, self.agent_given_name)

    @property
    def agent_type(self):
        """Return agent type"""
        return self._agent_type

    @property
    def affiliations(self):
        """ Return hasAffiliation values if exist, Empty list otherwise """
        return self.body.get('hasAffiliation', [])

    @affiliations.setter
    def affiliations(self, affiliations):
        """ Sets hasAffiliation values """
        if affiliations:
            self._body['hasAffiliation'] = affiliations

    @property
    def identified_bys(self):
        """ Return array of identifiedBy values if exist, Empty list otherwise """
        return self._agent_identified_by

    @identified_bys.setter
    def identified_bys(self, identified_bys):
        """ Sets identifiedBy values """
        if identified_bys:
            self._body['agent']['identifiedBy'] = identified_bys

    def update_name_part(self, contrib):
        for key in ["givenName", "familyName", "lifeSpan", "termsOfAddress"]:
            if contrib.agent.get(key):
                self._body["agent"][key] = contrib.agent[key]
            else:
                self._body["agent"].pop(key, None)


def safe_concat(first, second, separator=' '):
    if first and second:
        return first + separator + second
    elif first:
        return first
    elif second:
        return second
    else:
        return None


class HasSeries:
    """Abstract hasSeries format and API to access its properties
    Populated by Publication.has_series or IsPartOf.has_series"""

    """Match ratios for various isPartOf fields, see SequenceMatcher """
    STRING_MATCH_HASSERIES_MAIN_TITLE = 0.9

    def __init__(self, body):
        self._body = body

    def __eq__(self, has_series):
        """ Two has series is equal if it has same ISSN and IssueNumber or same maintitle """
        same_identified_by = (self.has_same_issn(has_series) and self.has_same_issue_number(has_series))
        same_main_title = self.has_same_main_title(has_series)
        return same_identified_by or same_main_title

    @property
    def body(self):
        """Return raw body data"""
        return self._body

    @property
    def main_title(self):
        """Return value for hasTitle[?(@.@type=="Title")].mainTitle, None if not exist """
        main_title_array = self.body.get('hasTitle', [])
        for m_t in main_title_array:
            if isinstance(m_t, dict) and m_t.get('@type') == 'Title':
                return m_t.get('mainTitle')
        return None

    @property
    def issn(self):
        """Return value for identifiedBy[?(@.@type=="ISSN")].value, None if not exist """
        issn_array = self.body.get('identifiedBy', [])
        for i in issn_array:
            if isinstance(i, dict) and i.get('@type') == 'ISSN':
                return i.get('value')
        return None

    @property
    def issue_number(self):
        """Return value for hasTitle[?(@.@type=="Title")].partNumber, None if not exist """
        issn_array = self.body.get('hasTitle', [])
        for i in issn_array:
            if isinstance(i, dict) and i.get('@type') == 'Title':
                return i.get('partNumber')
        return None

    @property
    def issns(self):
        """Return values for identifiedBy[?(@.@type=="ISSN")].value, Empty array if not exist """
        return get_ids(self.body, 'identifiedBy', 'ISSN')

    def add_issns(self, is_part_of):
        """ Adds ISSN from is_part_of if not already exist, if it does then adds 'qualifier' if not set.
        Also appends 'meta' from is_part_of.
        """
        for new_issn in is_part_of.issns:
            new_issn_dict = _get_identified_by_dict(is_part_of.body, 'ISSN', new_issn)
            if new_issn in self.issns:
                self_issns_dict = _get_identified_by_dict(self.body, 'ISSN', new_issn)
                if new_issn_dict.get('qualifier') and not self_issns_dict.get('qualifier'):
                    self_issns_dict.update({'qualifier': new_issn_dict.get('qualifier')})
            else:
                try:
                    self.body['identifiedBy'].append(new_issn_dict)
                except KeyError:
                    self.body.update({'identifiedBy': [new_issn_dict]})
        if is_part_of.body.get("meta"):
            if not self.body.get("meta"):
                self.body["meta"] = []
            self.body["meta"].append(is_part_of.body.get("meta"))

    def has_same_main_title(self, has_series):
        """True if is_part_of has the same main title"""
        return compare_text(self.main_title, has_series.main_title, self.STRING_MATCH_HASSERIES_MAIN_TITLE)

    def has_same_issn(self, has_series):
        if empty_string(self.issn) or empty_string(has_series.issn):
            return False
        return self.issn == has_series.issn

    def has_same_issue_number(self, has_series):
        if empty_string(self.issue_number) or empty_string(has_series.issue_number):
            return False
        return self.issue_number == has_series.issue_number


class ElectronicLocator:
    """Abstract electronicLocator format and API to access its properties
    Populated by electronicLocator by Publications.electronic_locators"""
    TYPE = '@type'
    URI = 'uri'
    HAS_NOTE = 'hasNote'

    def __init__(self, body):
        self._body = body

    def __eq__(self, electronic_locator):
        """ Two electronic_locator is equal if it has same @type and uri """
        same_type = self.type == electronic_locator.type
        same_uri = self.uri == electronic_locator.uri
        return same_type and same_uri

    @property
    def body(self):
        """Return raw body data"""
        return self._body

    @property
    def type(self):
        """Return @type value"""
        return self.body.get(self.TYPE)

    @property
    def uri(self):
        """Return uri value"""
        return self.body.get(self.URI)

    @property
    def notes(self):
        """Return @hasNote array"""
        return self.body.get(self.HAS_NOTE, [])

    def add_notes(self, new_notes):
        for note in new_notes:
            if note not in self.notes:
                self.notes.append(note)


class IsPartOf:
    """Abstract isPartOf format and API to access its properties
    Populated by isPartOf by Publications.is_part_of"""

    """Match ratios for various isPartOf fields, see SequenceMatcher """
    STRING_MATCH_ISPARTOF_MAIN_TITLE = 0.8
    STRING_MATCH_ISPARTOF_SUB_TITLE = 0.8

    def __init__(self, body):
        self._body = body

    def __eq__(self, is_part_of):
        """ Two isPartOf is equal if one its identifier are the same (ISSN or ISBN) or
        and same maintitle, subtitle, volumenumber and issueNumber"""
        if self._body == is_part_of._body:
            return True

        same_issns = len(set(self.issns).intersection(is_part_of.issns)) > 0
        if same_issns:
            return True

        same_isbns = len(set(self.isbns).intersection(is_part_of.isbns)) > 0
        if same_isbns:
            return True

        same_main_title = self.has_same_main_title(is_part_of)
        same_sub_title = self.has_same_sub_title(is_part_of)
        same_volume_number = self.volume_number == is_part_of.volume_number
        same_issue_number = self.issue_number == is_part_of.issue_number
        return same_main_title and same_sub_title and same_volume_number and same_issue_number

    @property
    def body(self):
        """Return raw body data"""
        return self._body

    @property
    def main_title(self):
        """Return value for hasTitle[?(@.@type=="Title")].mainTitle, None if not exist """
        main_title_array = self.body.get('hasTitle', [])
        for m_t in main_title_array:
            if isinstance(m_t, dict) and m_t.get('@type') == 'Title':
                return m_t.get('mainTitle')
        return None

    @property
    def sub_title(self):
        """Return value for hasTitle[?(@.@type=="Title")].subtitle, None if not exist """
        main_title_array = self.body.get('hasTitle', [])
        for m_t in main_title_array:
            if isinstance(m_t, dict) and m_t.get('@type') == 'Title':
                return m_t.get('subtitle')
        return None

    @property
    def volume_number(self):
        """Return value for hasTitle[?(@.@type=="Title")].volumeNumber, None if not exist """
        volume_number_array = self.body.get('hasTitle', [])
        for v in volume_number_array:
            if isinstance(v, dict) and v.get('@type') == 'Title':
                return v.get('volumeNumber')
        return None

    @property
    def issue_number(self):
        """Return value for hasTitle[?(@.@type=="Title")].issueNumber, None if not exist """
        issue_number_array = self.body.get('hasTitle', [])
        for v in issue_number_array:
            if isinstance(v, dict) and v.get('@type') == 'Title':
                return v.get('issueNumber')

    @property
    def issns(self):
        """Return values for identifiedBy[?(@.@type=="ISSN")].value, Empty array if not exist """
        return get_ids(self.body, 'identifiedBy', 'ISSN')

    def add_issns(self, is_part_of):
        """ Adds ISSN from is_part_of if not already exist, if it does then adds 'qualifier' if not set.
        Also appends 'meta' from is_part_of.
        """
        for new_issn in is_part_of.issns:
            new_issn_dict = _get_identified_by_dict(is_part_of.body, 'ISSN', new_issn)
            if new_issn in self.issns:
                self_issns_dict = _get_identified_by_dict(self.body, 'ISSN', new_issn)
                if new_issn_dict.get('qualifier') and not self_issns_dict.get('qualifier'):
                    self_issns_dict.update({'qualifier': new_issn_dict.get('qualifier')})
            else:
                try:
                    self.body['identifiedBy'].append(new_issn_dict)
                except KeyError:
                    self.body.update({'identifiedBy': [new_issn_dict]})
        if is_part_of.body.get("meta"):
            if not self.body.get("meta"):
                self.body["meta"] = []
            
            meta = is_part_of.body.get("meta")
            if isinstance(meta, list):
                self.body["meta"] = meta
            else:
                self.body["meta"].append(meta)

    @property
    def isbns(self):
        """Return values for identifiedBy[?(@.@type=="ISBN")].value, Empty array if not exist """
        return get_ids(self.body, 'identifiedBy', 'ISBN')

    def add_isbns(self, is_part_of):
        """ Adds ISBN from is_part_of if not already exist, if it does then adds 'qualifier' if not set """
        for new_isbn in is_part_of.isbns:
            new_isbn_dict = _get_identified_by_dict(is_part_of.body, 'ISBN', new_isbn)
            if new_isbn in self.isbns:
                self_isbns_dict = _get_identified_by_dict(self.body, 'ISBN', new_isbn)
                if new_isbn_dict.get('qualifier') and not self_isbns_dict.get('qualifier'):
                    self_isbns_dict.update({'qualifier': new_isbn_dict.get('qualifier')})
            else:
                try:
                    self.body['identifiedBy'].append(new_isbn_dict)
                except KeyError:
                    self.body.update({'identifiedBy': [new_isbn_dict]})

    @property
    def has_series(self):
        """ Return array of IsPartOfHasSeries objects from hasSeries field """
        has_series = []
        has_series_json_array = self.body.get('hasSeries', [])
        if has_series_json_array is not None:
            for serie in has_series_json_array:
                has_series.append(IsPartOfHasSeries(serie))
        return has_series

    def add_series(self, is_part_of):
        new_has_series = is_part_of.has_series
        self_has_series = self.has_series
        for new_has_serie in new_has_series:
            if new_has_serie not in self_has_series:
                self_has_series.append(new_has_serie)
        if len(self_has_series) > 0:
            self.body['hasSeries'] = [has_serie.body for has_serie in self_has_series]

    def has_same_main_title(self, is_part_of):
        """True if is_part_of has the same main title"""
        # isPartOf w/o main title should never match
        if self.main_title is None and is_part_of.main_title is None:
            return False
        return compare_text(self.main_title, is_part_of.main_title, self.STRING_MATCH_ISPARTOF_MAIN_TITLE)

    def has_same_sub_title(self, is_part_of):
        """True if is_part_of has the same sub title"""
        # sub title is less common, so here we don't need to be as strict
        return compare_text(self.sub_title, is_part_of.sub_title, self.STRING_MATCH_ISPARTOF_SUB_TITLE)


class IsPartOfHasSeries(HasSeries):
    """ Two has series for isPartOf is equal if it has same ISSN or same maintitle """
    def __eq__(self, has_series):
        same_identified_by = self.has_same_issn(has_series)
        same_main_title = self.has_same_main_title(has_series)
        return same_identified_by or same_main_title


class PublicationInformation:
    """Representation of field "publication" and API to access its properties
    Populated by publication_information by Publications.publication_information"""

    def __init__(self, body):
        self._body = body

    @property
    def body(self):
        """Return raw body data"""
        return self._body

    @property
    def date(self):
        return self.body.get('date')

    @date.setter
    def date(self, date):
        """ Sets date from date string (YYYY) """
        self._body['date'] = date

    @property
    def agent(self):
        return self.body.get('agent')

    @agent.setter
    def agent(self, agent):
        """ Sets agent from agent dict """
        self._body['agent'] = agent

    @property
    def place(self):
        return self.body.get('place')

    @place.setter
    def place(self, place):
        """ Sets place from place dict """
        self._body['place'] = place


def _get_identified_by_dict(body, type, value):
    for id_by in body['identifiedBy']:
        if id_by['@type'] == type and id_by['value'] == value:
            return id_by
    return None
