import re
from enum import Enum

from dateutil.parser import parse as dateutil_parse
from jsonpath_rw_ext import parse
from datetime import date, datetime


def _create_title_string(title_dict):
    main_title = title_dict.get("mainTitle", "")
    sub_title = title_dict.get("subtitle")
    if sub_title and len(sub_title) > 0:
        title_string = f"{main_title}: {sub_title}"
    else:
        title_string = main_title
    return title_string

def _add_id_to_person(person, agent, id_type, id_label):
    id = None
    id_by_list = agent.get("identifiedBy", [])
    for id_by in id_by_list:
        if id_by.get("@type", "") == id_type:
            id = id_by.get("value")
            break
    person.update({id_label: id})
    return person


def _add_id_by_code_to_person(person, agent, id_type, id_by_code_label):
    id_by_code = None
    id_by_list = agent.get("identifiedBy", [])
    for id_by_part in id_by_list:
        if id_by_part.get("@type", "") == id_type:
            source = id_by_part.get("source", None)
            if source is not None and source.get("@type", "") == "Source":
                id_by_code = source.get("code")
                break
    person.update({id_by_code_label: id_by_code})
    return person


class Level(Enum):
    PEERREVIEWED = 'https://id.kb.se/term/swepub/swedishlist/peer-reviewed'
    NONPEERREVIEWED = 'https://id.kb.se/term/swepub/swedishlist/non-peer-reviewed'


class BibframeSource:
    OUTPUT_TYPES_AUT_CRE = [
        "https://id.kb.se/term/swepub/publication/book",
        "https://id.kb.se/term/swepub/publication/book-chapter",
        "https://id.kb.se/term/swepub/publication/foreword-afterword",
        "https://id.kb.se/term/swepub/publication/report-chapter",
        "https://id.kb.se/term/swepub/publication/encyclopedia-entry",
        "https://id.kb.se/term/swepub/publication/review-article",
        "https://id.kb.se/term/swepub/publication/doctoral-thesis",
        "https://id.kb.se/term/swepub/publication/licentiate-thesis",
        "https://id.kb.se/term/swepub/publication/book-review",
        "https://id.kb.se/term/swepub/publication/journal-article",
        "https://id.kb.se/term/swepub/publication/magazine-article",
        "https://id.kb.se/term/swepub/publication/newspaper-article",
        "https://id.kb.se/term/swepub/publication/editorial-letter",
        "https://id.kb.se/term/swepub/conference/poster",
        "https://id.kb.se/term/swepub/conference/paper",
        "https://id.kb.se/term/swepub/conference/other",
        "https://id.kb.se/term/swepub/intellectual-property",
        "https://id.kb.se/term/swepub/intellectual-property/patent",
        "https://id.kb.se/term/swepub/intellectual-property/other",
        "https://id.kb.se/term/swepub/artistic-work/artistic-thesis",
        "https://id.kb.se/term/swepub/publication/critical-edition",
        "https://id.kb.se/term/swepub/publication/working-paper",
        "https://id.kb.se/term/swepub/publication/preprint",
        "https://id.kb.se/term/swepub/publication/other",
        "https://id.kb.se/term/swepub/other",
        "https://id.kb.se/term/swepub/other/data-set",
        "https://id.kb.se/term/swepub/other/software",
        "https://id.kb.se/term/swepub/artistic-work/original-creative-work",  # Also in OUTPUT_TYPES_CONSIDER_OTHER_TYPE
    ]

    # Output types for which role 'edt' is to be considered a creator.
    OUTPUT_TYPES_EDT = [
        "https://id.kb.se/term/swepub/publication/edited-book",
        "https://id.kb.se/term/swepub/conference/proceeding",
        "https://id.kb.se/term/swepub/publication/journal-issue",
    ]

    # Output types for which to consider other output type (if present).
    OUTPUT_TYPES_CONSIDER_OTHER_TYPE = [
        "https://id.kb.se/term/swepub/artistic-work/original-creative-work",  # Also in CREATORS_AUT_CRE
        "https://id.kb.se/term/swepub/artistic-work",  # Also in OUTPUT_TYPES_NOT_SPECIFIED
    ]

    # For these, if only 'edt' is present then 'edt' should be considered the creator role.
    # Else 'aut' and 'cre' should be the creator roles.
    OUTPUT_TYPES_CREATOR_NOT_SPECIFIED = [
        "https://id.kb.se/term/swepub/publication/report",
        "https://id.kb.se/term/swepub/conference",
        "https://id.kb.se/term/swepub/artistic-work",  # Also in OUTPUT_TYPES_CONSIDER_OTHER_TYPE
        "https://id.kb.se/term/swepub/publication",
    ]

    AUT_CREATOR = "http://id.loc.gov/vocabulary/relators/aut"
    CRE_CREATOR = "http://id.loc.gov/vocabulary/relators/cre"
    EDT_CREATOR = "http://id.loc.gov/vocabulary/relators/edt"
    ALL_CREATOR_IDS = [AUT_CREATOR, CRE_CREATOR, EDT_CREATOR]

    RAW_SUBJECT_PATH = 'instanceOf.subject[?(@.@type=="Topic")]'
    SUBJECT_PATH = parse(RAW_SUBJECT_PATH)

    def __init__(self, bibframe_source={}):
        self._source = bibframe_source

    @property
    def bibframe_source(self):
        return self._source

    @property
    def record_id(self):
        return self._source.get("@id")

    @property
    def source_org(self):
        """Returns org code from publication"""
        return self._source.get("meta", {}).get("assigner", {}).get("label")

    @property
    def publication_year(self):
        publications = self._source.get("publication", [])
        for publication in publications:
            if publication.get("@type", "").lower() == "publication":
                return publication.get("date")
        return None

    @property
    def output_types(self):
        genre_forms = self._source.get("instanceOf", {}).get("genreForm")
        svep_url = 'https://id.kb.se/term/swepub/svep/'
        swedish_list_url = 'https://id.kb.se/term/swepub/swedishlist'
        # Example output types: https://id.kb.se/term/swepub/publication/journal-article
        # or https://id.kb.se/term/swepub/publication
        output_type_re = r'^https://id\.kb\.se/term/swepub/[a-z_\-]+/*[a-z_\-]*$'
        output_types = []
        if genre_forms:
            for genre_form in genre_forms:
                id = genre_form.get("@id", "")
                if id.strip().startswith(svep_url) or id.strip().startswith(swedish_list_url):
                    continue
                m = re.match(output_type_re, id)
                if m is None:
                    continue
                output_types.append(m.group(0))
        return output_types

    @property
    def publication_status(self):
        notes = self._source.get("instanceOf", {}).get("hasNote", [])
        for note in notes:
            if note.get("@type", "") == "PublicationStatus":
                return note.get("@id")
        return None

    @property
    def content_marking(self):
        svep_url = 'https://id.kb.se/term/swepub/svep/'
        genreForm = self._source.get("instanceOf", {}).get("genreForm", [])
        for gf in genreForm:
            gf_id = gf.get("@id", "")
            if gf_id.strip().startswith(svep_url):
                prefix_len = len(svep_url)
                total_len = len(gf_id)
                return gf_id[prefix_len:total_len + 1]
        return None

    @property
    def creator_count(self):
        notes = self._source.get("instanceOf", {}).get("hasNote", [])
        for note in notes:
            if note.get("@type", "") == "CreatorCount":
                try:
                    creator_count = int(note.get("label", "").strip())
                    return creator_count
                except (TypeError, ValueError):
                    return None
        return None

    @property
    def creators(self):
        creator_list = []
        creator_id_list = self._get_creator_ids_based_on_output_type()

        include_every_part = True
        # include all subparts as default,
        # if include_all
        # or if 'creators' has been chosen but no subfields have been chosen
        #if self.include_all or all(field not in self._chosen_fields for field in CREATOR_FIELDS):
        #    include_every_part = True

        contributors = self._source.get("instanceOf", {}).get("contribution", [])

        for contrib in contributors:
            if contrib.get("agent", {}).get("@type", "") == "Person":
                roles = contrib.get("role", [])
                for role in roles:
                    if role.get("@id", "") in creator_id_list:
                        person = dict()
                        person.update({"givenName": contrib.get("agent", {}).get("givenName")})
                        person.update({"familyName": contrib.get("agent", {}).get("familyName")})
                        person = _add_id_to_person(person, contrib.get("agent", {}), "Local", "localId")
                        person = _add_id_by_code_to_person(person, contrib.get("agent", {}), "Local", "localIdBy")
                        person = _add_id_to_person(person, contrib.get("agent", {}), "ORCID", "ORCID")
                        # if include_every_part or "affiliation" in self._chosen_fields:
                        #     person = self._add_affiliation_to_person_recursive(person,
                        #                                                        contrib.get("hasAffiliation", []))
                        # if include_every_part or "freetext_affiliations" in self._chosen_fields:
                        #     person = self._add_freetext_affiliation_to_person(person, contrib.get("hasAffiliation", []))
                        creator_list.append(person)
                        break
        return creator_list

    def _get_creator_ids_based_on_output_type(self):
        """Returns a list of creator ids based on output type(s).
        Possible creator ids can be seen in  ALL_CREATOR_IDS.

        See lists of output types for mapping between output type and creator ids.
        """
        adjusted_creator_id_list = set()

        output_types = []

        # First try to use only output types not in OUTPUT_TYPES_CONSIDER_OTHER_TYPE.
        for output_type in self.output_types:
            if output_type not in self.OUTPUT_TYPES_CONSIDER_OTHER_TYPE:
                output_types.append(output_type)

        # Only existing output type might be in OUTPUT_TYPES_CONSIDER_OTHER_TYPE.
        if len(output_types) < 1:
            output_types = self.output_types

        # Add creator ids based on output type.
        for output_type in output_types:
            if output_type in self.OUTPUT_TYPES_AUT_CRE:
                adjusted_creator_id_list.update([self.AUT_CREATOR, self.CRE_CREATOR])
            elif output_type in self.OUTPUT_TYPES_EDT:
                adjusted_creator_id_list.add(self.EDT_CREATOR)

        if len(adjusted_creator_id_list) > 0:
            return list(adjusted_creator_id_list)
        else:
            # No creator ids found based on output type.
            return self._get_creator_ids_for_not_specified()

    def _get_creator_ids_for_not_specified(self):
        """Returns a list of creator ids based on existing creator ids (roles)
        in this publication.

        If only 'edt' exists that creator id will be returned, else 'aut' and 'cre'.
        """
        creator_types_present = set()

        contributors = self._source.get("instanceOf", {}).get("contribution", [])
        for contrib in contributors:
            if contrib.get("agent", {}).get("@type", "") == "Person":
                roles = contrib.get("role", [])
                for role in roles:
                    role_id = role.get("@id", None)
                    if role_id is not None:
                        creator_types_present.add(role_id)

        if len(creator_types_present) == 1 and self.EDT_CREATOR in creator_types_present:
            return [self.EDT_CREATOR]
        else:
            return [self.AUT_CREATOR, self.CRE_CREATOR]

    @property
    def title(self):
        titles = self._source.get("instanceOf", {}).get("hasTitle", [])
        for title in titles:
            if title.get("@type", "") == "Title":
                return _create_title_string(title)

    @property
    def open_access(self):
        """Returns true if publication is open access
        We check if there is an AccessPolicy with a value of 'gratis or an
        electronicLocator with a note 'free', or 'free/<date>' if date has
        passed."""
        free_note_re = r'^free(/[0-9]{4}\-[0-9]{2}\-[0-9]{2})*$'
        # Embargoes are more important than AccessPolicies
        if self._is_embargoed():
            return False
        ua_policies = self._source.get("usageAndAccessPolicy", [])
        for policy in ua_policies:
            if policy.get("@type", "") == "AccessPolicy":
                label = policy.get("label", "")
                if "gratis" in label:
                    return True
                elif "restricted" in label:
                    return False
        electronic_locators = self._source.get("electronicLocator", [])
        for electronic_locator in electronic_locators:
            if electronic_locator.get("@type", "") == "MediaObject" and len(
                    electronic_locator.get("uri", "")) > 0:
                ua_policies = electronic_locator.get("usageAndAccessPolicy", [])
                for policy in ua_policies:
                    ua_id = policy.get("@id", "")
                    if ua_id == 'https://id.kb.se/policy/oa/gratis':
                        return True
                    elif ua_id == 'https://id.kb.se/policy/oa/restricted':
                        return False

            if electronic_locator.get("@type", "") == "Resource" and len(
                    electronic_locator.get("uri", "")) > 0:
                for note in electronic_locator.get("hasNote", []):
                    label = note.get("label", "")
                    m = re.match(free_note_re, label)
                    if m is None:
                        continue
                    if m.group(0):
                        if len(m.group(0).split("/")) > 1:
                            free_from = m.group(0).split("/")[1]
                            if free_from and len(free_from) > 1:
                                try:
                                    free_from_date = dateutil_parse(free_from).date()
                                except ValueError:
                                    continue
                            now_date = datetime.now().date()
                            if now_date >= free_from_date:
                                return True
                        else:
                            # ok, if note without date, eg "free"
                            return True
        return False

    @property
    def ssif_1(self):
        SUBJECT_PREFIX = 'https://id.kb.se/term/uka/'
        for code in self.subject_codes:
            if not code.startswith(SUBJECT_PREFIX):
                continue
            short = code[len(SUBJECT_PREFIX):]
            if len(short) == 1:
                return short
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
    def level(self):
        """Return the publication's level according to the Swedish List."""
        if ('instanceOf' not in self._source
                or 'genreForm' not in self._source['instanceOf']):
            return None

        for gform in self._source['instanceOf']['genreForm']:
            # Peer-reviewed always trumps non-peer-reviewed
            if '@id' in gform and gform['@id'] == Level.PEERREVIEWED.value:
                return Level.PEERREVIEWED

            if '@id' in gform and gform['@id'] == Level.NONPEERREVIEWED.value:
                return Level.NONPEERREVIEWED
        return None

    @property
    def subjects(self):
        """Return a list of all subjects."""
        subjects = self.SUBJECT_PATH.find(self._source)
        return [subj.value for subj in subjects if subj.value]

    @property
    def subject_codes(self):
        """Return a list of all subject identifiers."""
        return [subj['@id'] for subj in self.subjects if '@id' in subj]

    @property
    def is_swedishlist(self):
        # instanceOf.genreForm.@id": "https://id.kb.se/term/swepub/swedishlist/peer-reviewed"
        for gf in self._source.get("instanceOf", {}).get("genreForm", []):
            if gf.get("@id", "") == 'https://id.kb.se/term/swepub/swedishlist/peer-reviewed':
                return True
        return False

    @property
    def uka_subjects(self):
        subjects = dict()
        should_include_one_digit_topics = True
        should_include_three_digit_topics = True
        should_include_five_digit_topics = True

        # if (self.include_all or "oneDigitTopics" in self._chosen_fields
        #         or "subjects" in self._chosen_fields):  # noqa: W503
        #     should_include_one_digit_topics = True
        #
        # if (self.include_all or "threeDigitTopics" in self._chosen_fields
        #         or "subjects" in self._chosen_fields):  # noqa: W503
        #     should_include_three_digit_topics = True
        #
        # if (self.include_all or "fiveDigitTopics" in self._chosen_fields
        #         or "subjects" in self._chosen_fields):  # noqa: W503
        #     should_include_five_digit_topics = True

        if should_include_one_digit_topics:
            subjects.update({"oneDigitTopics": []})
        if should_include_three_digit_topics:
            subjects.update({"threeDigitTopics": []})
        if should_include_five_digit_topics:
            subjects.update({"fiveDigitTopics": []})

        for subject in self._source.get("instanceOf", {}).get("subject", []):
            if subject.get("inScheme", {}).get("code", "") == "uka.se" and \
                    subject.get("@type", "") == "Topic":
                subject_code = subject.get("code", "").strip()
                if len(subject_code) == 1:
                    if should_include_one_digit_topics:
                        if subject_code not in subjects["oneDigitTopics"]:
                            subjects["oneDigitTopics"].append(subject_code)
                            continue
                if len(subject_code) == 3:
                    if should_include_three_digit_topics:
                        if subject_code not in subjects["threeDigitTopics"]:
                            subjects["threeDigitTopics"].append(subject_code)
                            continue
                if len(subject_code) == 5:
                    if should_include_five_digit_topics:
                        if subject_code not in subjects["fiveDigitTopics"]:
                            subjects["fiveDigitTopics"].append(subject_code)
        return subjects

    @property
    def keywords(self):
        subj_list = []
        subjects = self._source.get("instanceOf", {}).get("subject", [])
        for subject in subjects:
            pref_label = subject.get("prefLabel")
            if pref_label:
                subj_list.append(pref_label)
        return subj_list

    @property
    def doi(self):
        doi_list = []
        ids = self._source.get("identifiedBy", [])
        for id in ids:
            if id.get("@type", "") == "DOI":
                doi_list.append(id.get("value"))
        part_ofs = self._source.get("partOf", [])
        for part_of in part_ofs:
            ids = part_of.get("identifiedBy", [])
            for id in ids:
                if id.get("@type", "") == "DOI":
                    doi_list.append(id.get("value"))
        return doi_list

    def _is_embargoed(self):
        ua_policies = self._source.get("usageAndAccessPolicy", [])
        for policy in ua_policies:
            if policy.get("@type", "") != "Embargo":
                continue
            end_date = policy.get("endDate")
            if end_date is None:
                return True
            try:
                parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                # Embargo is lifted the day after end date
                if parsed_end_date >= date.today():
                    return True
                else:
                    return False
            except ValueError:
                print(f"Invalid `endDate` {end_date} for Embargo on {self.record_id}")
                # If we can't parse the date, we count the embargo as invalid
                return False
        return False
