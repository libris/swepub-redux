#from utils import compare_text, empty_string, split_title_subtitle_first_colon

from difflib import SequenceMatcher

"""Max length in characters to compare text"""
MAX_LENGTH_STRING_TO_COMPARE = 1000


def compare_text(master_text, candidate_text, match_ratio):
    if empty_string(master_text) and empty_string(candidate_text):
        return True
    if empty_string(master_text) or empty_string(candidate_text):
        return False
    master_text = master_text[0:MAX_LENGTH_STRING_TO_COMPARE]
    candidate_text = candidate_text[0:MAX_LENGTH_STRING_TO_COMPARE]
    master_text = master_text.lower()
    candidate_text = candidate_text.lower()
    sequence_matcher = SequenceMatcher(a=master_text,
                                       b=candidate_text)
    sequence_matcher_ratio = sequence_matcher.quick_ratio()
    return sequence_matcher_ratio >= match_ratio


def empty_string(s):
    if s and isinstance(s, str):
        if not s.strip():
            return True
        else:
            return False
    return True


def split_title_subtitle_first_colon(title):
    try:
        splited = title.split(':', 1)
        maintitle = splited[0]
        subtitle = None
        if len(splited) == 2:
            subtitle = splited[1]
            subtitle = subtitle.strip()
        return maintitle, subtitle
    except AttributeError:
        return title, None



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
        return self.body['@id']

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
        """Return value for instanceOf.hasTitle[?(@.@type=="Title")].mainTitle if exist and there are no subtitle.
        If subtitle exist then return value is splited with colon and first string is returned,
        i.e 'main:sub' returns main.
        None otherwise """
        has_title_array = self.body.get('instanceOf', {}).get('hasTitle', [])
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
        """Return value for instanceOf.hasTitle[?(@.@type=="Title")].subtitle if exist,
        if it does not exist then value of instanceOf.hasTitle[?(@.@type=="Title")].mainTitle is splited
        with colon and second string is returned, i.e 'main:sub' returns sub.
        None otherwise """
        sub_title_array = self.body.get('instanceOf', {}).get('hasTitle', [])
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
    def summary(self):
        """ Return value for instanceOf.summary[?(@.@type=="Summary")].label if exist, None otherwise """
        summary_array = self.body.get('instanceOf', {}).get('summary', [])
        for s in summary_array:
            if isinstance(s, dict) and s.get('@type') == 'Summary':
                return s.get('label')
        return None

    @property
    def publication_date(self):
        """ Return value for publication[?(@.@type=="Publication")].date if exist, None otherwise """
        publication_information = self.publication_information
        if publication_information:
            return publication_information.date
        return None

    @property
    def publication_information(self):
        """ Return first occurrence of PublicationInformation from publication field"""
        # TODO: Remove check for provisionActivity (see https://jira.kb.se/browse/SWEPUB2-718)
        if "publication" not in self.body and "provisionActivity" in self.body:
            provision_activity_array = self.body.get('provisionActivity', [])
            publication_array = [p for p in provision_activity_array if p.get('@type') == 'Publication']
        else:
            publication_array = self.body.get('publication', [])
        for p in publication_array:
            if isinstance(p, dict) and p.get('@type') == 'Publication':
                return PublicationInformation(p)
        return None

    @publication_information.setter
    def publication_information(self, publication_information):
        """ Sets array for publication_information from array of PublicationInformation objects """
        self.body['publication'] = [publication_information.body]
        # TODO: Remove check for provisionActivity (see https://jira.kb.se/browse/SWEPUB2-718)
        provision_activity_array = self.body.get('provisionActivity', [])
        provision_activity_array = [p for p in provision_activity_array if p.get('@type') != 'Publication']
        self.body['provisionActivity'] = provision_activity_array

    @property
    def usage_and_access_policy(self):
        """Return a list of usage and access policies or None if unset"""
        return self.body.get("usageAndAccessPolicy", None)

    @usage_and_access_policy.setter
    def usage_and_access_policy(self, policies):
        """Sets usage and access policies to supplied list"""
        self.body["usageAndAccessPolicy"] = policies

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

        return (access_policies, embargoes, links, others)

    @property
    def genre_form(self):
        """ Return array of values from instanceOf.genreForm.[*].@id """
        genre_forms = []
        genre_form_array = self.body.get('instanceOf', {}).get('genreForm', [])
        for g_f in genre_form_array:
            if isinstance(g_f, dict):
                genre_forms.append(g_f.get('@id'))
        return [gf for gf in genre_forms if gf]

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
        self.body['instanceOf']['contribution'] = [c.body for c in contributions]

    @property
    def publication_status(self):
        """ Return value for instanceOf.hasNote[?(@.@type=="PublicationStatus")].@id if exist, None otherwise """
        publication_date_array = self.body.get('instanceOf', {}).get('hasNote', [])
        for p_d in publication_date_array:
            if isinstance(p_d, dict) and p_d.get('@type') == 'PublicationStatus':
                return p_d.get('@id')
        return None

    @publication_status.setter
    def publication_status(self, new_status):
        """ Sets status value in instanceOf.hasNote[?(@.@type=="PublicationStatus")].@id """
        i = 0
        for n in self.body.get('instanceOf', {}).get('hasNote', []):
            if n['@type'] == 'PublicationStatus':
                self.body['instanceOf']['hasNote'][i]['@id'] = new_status
                break
            else:
                i += 1

    @property
    def creator_count(self):
        """ Return value for instanceOf.[*].hasNote[?(@.@type=="CreatorCount")].label """
        creator_count_array = self.body.get('instanceOf', {}).get('hasNote', [])
        for c_c in creator_count_array:
            if isinstance(c_c, dict) and c_c.get('@type') == 'CreatorCount':
                return c_c.get('label')
        return None

    @creator_count.setter
    def creator_count(self, new_creator_count):
        """ Sets status value in instanceOf.[*].hasNote[?(@.@type=="CreatorCount")].label """
        i = 0
        for n in self.body.get('instanceOf', {}).get('hasNote', []):
            if n['@type'] == 'CreatorCount':
                self.body['instanceOf']['hasNote'][i]['label'] = new_creator_count
                break
            else:
                i += 1

    @property
    def notes(self):
        """ Return array of notes from instanceOf.[*].hasNote[?(@.@type=="Note")].label """
        notes = []
        notes_array = self.body.get('instanceOf', {}).get('hasNote', [])
        for n in notes_array:
            if isinstance(n, dict) and n.get('@type') == 'Note':
                notes.append(n.get('label'))

        return [n for n in notes if n]

    def add_notes(self, new_notes):
        """ Sets array of notes for instanceOf.[*].hasNote[?(@.@type=="Note")].label """
        new_notes = list(set(new_notes) - set(self.notes))
        for new_note in new_notes:
            self.body['instanceOf']['hasNote'].append({'@type': 'Note', 'label': new_note})

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
        self.body['instanceOf']['subject'] = subjects

    @property
    def has_series(self):
        """ Return array of HasSeries objects from hasSeries """
        has_series_objects = []
        has_series_json_array = self.body.get('hasSeries', [])
        for serie in has_series_json_array:
            if isinstance(serie, dict):
                has_series_objects.append(HasSeries(serie))
        return has_series_objects

    def add_series(self, part_of):
        new_has_series = part_of.has_series
        self_has_series = self.has_series
        for new_has_serie in new_has_series:
            if new_has_serie not in self_has_series:
                self_has_series.append(new_has_serie)
        if len(self_has_series) > 0:
            self.body['hasSeries'] = [has_serie.body for has_serie in self_has_series]

    @property
    def electronic_locators(self):
        """ Return array of ElectronicLocator objects from electronicLocator field """
        electronic_locators = []
        electronic_locators_json_array = self.body.get('electronicLocator', [])
        if electronic_locators_json_array is not None:
            for e in electronic_locators_json_array:
                if isinstance(e, dict):
                    electronic_locators.append(ElectronicLocator(e))
        return electronic_locators

    @electronic_locators.setter
    def electronic_locators(self, electronic_locators):
        """ Sets array for electronicLocator field from array of ElectronicLocator objects """
        self.body['electronicLocator'] = [e.body for e in electronic_locators]

    @property
    def part_of(self):
        """ Return array of PartOf objetcs from partOf """
        part_of = []
        part_of_json_array = self.body.get('partOf', [])
        if part_of_json_array is not None:
            for p in part_of_json_array:
                if isinstance(p, dict):
                    part_of.append(PartOf(p))
        return part_of

    @part_of.setter
    def part_of(self, part_of):
        """ Sets array for partOf from array of PartOf objects """
        self.body['partOf'] = [part.body for part in part_of]

    @property
    def part_of_with_title(self):
        """ Return partOf object that has @type Title, None otherwise"""
        part_of_with_title = [p for p in self.part_of if p.main_title]
        if len(part_of_with_title) > 0:
            return part_of_with_title[0]
        else:
            return None

    @property
    def identifiedby_ids(self):
        """Return array of items in identifiedBy"""
        return self.get_identifiedby_ids()

    @identifiedby_ids.setter
    def identifiedby_ids(self, identifiedby_ids):
        """Sets identifiedBy array, ex identifiedby_ids= [{'@type': 'DOI', 'value': 'DOI_1'}] """
        self.body['identifiedBy'] = identifiedby_ids

    @property
    def indirectly_identifiedby_ids(self):
        """Return array of items in indirectlyIdentifiedBy"""
        return self.get_indirectly_identifiedby_ids()

    @indirectly_identifiedby_ids.setter
    def indirectly_identifiedby_ids(self, indirectly_identifiedby_ids):
        """Sets indirectlyIdentifiedBy array, ex indirectly_identifiedby_ids= [{'@type': 'DOI', 'value': 'DOI_1'}] """
        self.body['indirectlyIdentifiedBy'] = indirectly_identifiedby_ids

    def get_identifiedby_ids(self, identifier=''):
        """Return either identifiedBy ids values if identifier is set otherwise whole identifiedBy array """
        return _get_ids(self.body, 'identifiedBy', identifier)

    def get_indirectly_identifiedby_ids(self, identifier=''):
        """Return either indirectlyIdentifiedBy ids values if identifier is set
        otherwise whole indirectlyIdentifiedBy array """
        return _get_ids(self.body, 'indirectlyIdentifiedBy', identifier)

    def has_same_main_title(self, publication):
        """True if publication has the same main title"""
        return compare_text(self.main_title, publication.main_title, self.STRING_MATCH_RATIO_MAIN_TITLE)

    def has_same_sub_title(self, publication):
        """True if publication has the same sub title"""
        return compare_text(self.sub_title, publication.sub_title, self.STRING_MATCH_RATIO_SUB_TITLE)

    def has_same_summary(self, publication):
        """True if publication has the same summary"""
        return compare_text(self.summary, publication.summary, self.STRING_MATCH_RATIO_SUMMARY)

    def has_same_partof_main_title(self, publication):
        """ Returns True if partOf has the same main title """
        if self.part_of_with_title and publication.part_of_with_title:
            return self.part_of_with_title.has_same_main_title(publication.part_of_with_title)
        else:
            return False

    def has_same_genre_form(self, publication):
        """True if publication has all the genreform the same"""
        if self.genre_form and publication.genre_form:
            return set(self.genre_form) == set(publication.genre_form)
        return False

    def has_same_publication_date(self, publication):
        """True if publication dates are the same by comparing the shortest date"""
        master_pub_date_str = self.publication_date
        candidate_pub_date_str = publication.publication_date
        if empty_string(master_pub_date_str) or empty_string(candidate_pub_date_str):
            return False
        master_pub_date_str = master_pub_date_str.strip()
        candidate_pub_date_str = candidate_pub_date_str.strip()
        if len(master_pub_date_str) > len(candidate_pub_date_str):
            master_pub_date_str = master_pub_date_str[:len(candidate_pub_date_str)]
        elif len(master_pub_date_str) < len(candidate_pub_date_str):
            candidate_pub_date_str = candidate_pub_date_str[:len(master_pub_date_str)]
        return master_pub_date_str == candidate_pub_date_str

    def has_same_ids(self, publication):
        """ True if one of ids DOI, PMID, ISI, ScopusID and ISBN are the same for identifiedBy
        or if ISBN id are the same for indirectlyIdentifiedBy"""
        if self._same_ids(self.get_identifiedby_ids('DOI'), publication.get_identifiedby_ids('DOI')):
            return True
        if self._same_ids(self.get_identifiedby_ids('PMID'), publication.get_identifiedby_ids('PMID')):
            return True
        if self._same_ids(self.get_identifiedby_ids('ISI'), publication.get_identifiedby_ids('ISI')):
            return True
        if self._same_ids(self.get_identifiedby_ids('ScopusID'),
                          publication.get_identifiedby_ids('ScopusID')):
            return True
        if self._same_ids(self.get_identifiedby_ids('ISBN'), publication.get_identifiedby_ids('ISBN')):
            return True
        if self._same_ids(self.get_indirectly_identifiedby_ids('ISBN'),
                          publication.get_indirectly_identifiedby_ids('ISBN')):
            return True
        return False

    def has_compatible_doi_set(self, publication):
        l1 = self.get_identifiedby_ids('DOI')
        l2 = publication.get_identifiedby_ids('DOI')

        # If either set is empty, they're compatible
        if (not l1) or (not l2):
            return True

        l1.sort()
        l2.sort()
        if l1 == l2:
            return True
        return False

    @staticmethod
    def _same_ids(master_ids, candidate_ids):
        if len(master_ids) == 0 or len(candidate_ids) == 0:
            return False
        return set(master_ids) == set(candidate_ids)

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
    def affiliations(self):
        """ Return hasAffiliation values if exist, Empty list otherwise """
        return self.body.get('hasAffiliation', [])

    @affiliations.setter
    def affiliations(self, affiliations):
        """ Sets hasAffiliation values """
        self.body['hasAffiliation'] = affiliations

    @property
    def identified_bys(self):
        """ Return array of identifiedBy values if exist, Empty list otherwise """
        return self._agent_identified_by

    @identified_bys.setter
    def identified_bys(self, identified_bys):
        """ Sets identifiedBy values """
        self.body['agent']['identifiedBy'] = identified_bys


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
    Populated by Publication.has_series or PartOf.has_series"""

    """Match ratios for various partOf fields, see SequenceMatcher """
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

    def has_same_main_title(self, has_series):
        """True if part_of has the same main title"""
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


class PartOf:
    """Abstract partOf format and API to access its properties
    Populated by partOf by Publications.part_of"""

    """Match ratios for various partOf fields, see SequenceMatcher """
    STRING_MATCH_PARTOF_MAIN_TITLE = 0.8
    STRING_MATCH_PARTOF_SUB_TITLE = 0.8

    def __init__(self, body):
        self._body = body

    def __eq__(self, part_of):
        """ Two partOf is equal if one its identifier are the same (ISSN or ISBN) or
        and same maintitle, subtitle, volumenumber and issueNumber"""
        if self._body == part_of._body:
            return True

        same_issns = len(set(self.issns).intersection(part_of.issns)) > 0
        if same_issns:
            return True

        same_isbns = len(set(self.isbns).intersection(part_of.isbns)) > 0
        if same_isbns:
            return True

        same_main_title = self.has_same_main_title(part_of)
        same_sub_title = self.has_same_sub_title(part_of)
        same_volume_number = self.volume_number == part_of.volume_number
        same_issue_number = self.issue_number == part_of.issue_number
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
        return _get_ids(self.body, 'identifiedBy', 'ISSN')

    def add_issns(self, part_of):
        """ Adds ISSN from part_of if not already exist, if it does then adds 'qualifier' if not set """
        for new_issn in part_of.issns:
            new_issn_dict = _get_identified_by_dict(part_of.body, 'ISSN', new_issn)
            if new_issn in self.issns:
                self_issns_dict = _get_identified_by_dict(self.body, 'ISSN', new_issn)
                if new_issn_dict.get('qualifier') and not self_issns_dict.get('qualifier'):
                    self_issns_dict.update({'qualifier': new_issn_dict.get('qualifier')})
            else:
                try:
                    self.body['identifiedBy'].append(new_issn_dict)
                except KeyError:
                    self.body.update({'identifiedBy': [new_issn_dict]})

    @property
    def isbns(self):
        """Return values for identifiedBy[?(@.@type=="ISBN")].value, Empty array if not exist """
        return _get_ids(self.body, 'identifiedBy', 'ISBN')

    def add_isbns(self, part_of):
        """ Adds ISBN from part_of if not already exist, if it does then adds 'qualifier' if not set """
        for new_isbn in part_of.isbns:
            new_isbn_dict = _get_identified_by_dict(part_of.body, 'ISBN', new_isbn)
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
        """ Return array of PartOfHasSeries objects from hasSeries field """
        has_series = []
        has_series_json_array = self.body.get('hasSeries', [])
        if has_series_json_array is not None:
            for serie in has_series_json_array:
                has_series.append(PartOfHasSeries(serie))
        return has_series

    def add_series(self, part_of):
        new_has_series = part_of.has_series
        self_has_series = self.has_series
        for new_has_serie in new_has_series:
            if new_has_serie not in self_has_series:
                self_has_series.append(new_has_serie)
        if len(self_has_series) > 0:
            self.body['hasSeries'] = [has_serie.body for has_serie in self_has_series]

    def has_same_main_title(self, part_of):
        """True if part_of has the same main title"""
        # partOf w/o main title should never match
        if self.main_title is None and part_of.main_title is None:
            return False
        return compare_text(self.main_title, part_of.main_title, self.STRING_MATCH_PARTOF_MAIN_TITLE)

    def has_same_sub_title(self, part_of):
        """True if part_of has the same sub title"""
        # sub title is less common, so here we don't need to be as strict
        return compare_text(self.sub_title, part_of.sub_title, self.STRING_MATCH_PARTOF_SUB_TITLE)


class PartOfHasSeries(HasSeries):
    """ Two has series for partOf is equal if it has same ISSN or same maintitle """
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

    @property
    def agent(self):
        return self.body.get('agent')

    @agent.setter
    def agent(self, agent):
        """ Sets agent from agent dict """
        self.body['agent'] = agent

    @property
    def place(self):
        return self.body.get('place')

    @place.setter
    def place(self, place):
        """ Sets place from place dict """
        self.body['place'] = place


def _get_ids(body, path, type):
    if type:
        ids = []
        ids_array = body.get(path, [])
        for id in ids_array:
            if isinstance(id, dict) and id.get('@type') == type:
                ids.append(id.get('value'))
        return [id for id in ids if id]
    else:
        if body.get(path):
            return body[path]
    return []


def _get_identified_by_dict(body, type, value):
    for id_by in body['identifiedBy']:
        if id_by['@type'] == type and id_by['value'] == value:
            return id_by
    return None
