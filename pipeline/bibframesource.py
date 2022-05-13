import re
from enum import Enum
from datetime import date, datetime
from dateutil.parser import parse as dateutil_parse

from pipeline.util import Level


CREATOR_FIELDS = [
    "familyName",
    "givenName",
    "localId",
    "localIdBy",
    "ORCID",
    "affiliation",
    "freetext_affiliations",
]
SUBJECT_FIELDS = ["oneDigitTopics", "threeDigitTopics", "fiveDigitTopics"]


def _create_title_string(title_dict):
    main_title = title_dict.get("mainTitle", "")
    sub_title = title_dict.get("subtitle")
    if sub_title and len(sub_title) > 0:
        title_string = f"{main_title}: {sub_title}"
    else:
        title_string = main_title
    return title_string


def _get_ids_from_dict(root_dict, label, id_type):
    result_list = []
    id_list = root_dict.get(label, [])
    for id_dict in id_list:
        if id_dict.get("@type", "") == id_type:
            result_list.append(id_dict.get("value"))
    return result_list


def _get_root_dict_ids(root_dict, label, id_type):
    id_list = []
    dict_list = root_dict.get(label, [])
    for d in dict_list:
        id_list.extend(_get_ids_from_dict(root_dict=d, label="identifiedBy", id_type=id_type))
        id_list.extend(
            _get_ids_from_dict(root_dict=d, label="indirectlyIdentifiedBy", id_type=id_type)
        )
    return id_list


def _add_id_to_person(person, agent, id_type, id_label):
    person_id = None
    id_by_list = agent.get("identifiedBy", [])
    for id_by in id_by_list:
        if id_by.get("@type", "") == id_type:
            person_id = id_by.get("value")
            break
    person.update({id_label: person_id})
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


class BibframeSource:
    """A class representing the Bibframe source"""

    # Output types for which role 'aut' and 'cre' is to be considered a creator.
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

    def __init__(self, bibframe_source=None, fields=None):
        if fields is None:
            fields = []
        if bibframe_source is None:
            bibframe_source = {}
        self._bibframe_master = bibframe_source
        self._bibframe_publication_ids = bibframe_source.get("_publication_ids", [])
        self._bibframe_publication_orgs = bibframe_source.get("_publication_orgs", [])
        self._bibframe_publications = [bibframe_source]
        self._chosen_fields = fields
        if len(fields) == 0:
            self._include_all = True
        else:
            self._include_all = False

    @property
    def bibframe_master(self):
        return self._bibframe_master

    @property
    def bibframe_publications(self):
        return self._bibframe_publications

    @property
    def include_all(self):
        return self._include_all

    @property
    def record_id(self):
        return self.bibframe_master.get("@id")

    @property
    def duplicate_ids(self):
        return self._bibframe_publication_ids

    @property
    def PMID(self):
        return self._get_instance_identifier(id_type="PMID")

    @property
    def scopus_id(self):
        return self._get_instance_identifier(id_type="ScopusID")

    @property
    def source_org(self):
        """Returns org code from all candidate/duplicate publications"""
        return self._bibframe_publication_orgs

    @property
    def source_org_master(self):
        """Returns org code from master publication"""
        return self._bibframe_master.get("meta", {}).get("assigner", {}).get("label")

    @property
    def publication_count(self):
        """Returns the number of merged publications."""
        return len(self._bibframe_publication_ids)

    @property
    def publication_year(self):
        publications = self.bibframe_master.get("publication", [])
        for publication in publications:
            if publication.get("@type", "").lower() == "publication":
                return publication.get("date")
        return None

    # Some records have a publication "year" of e.g. 2020-03-25, which is accepted,
    # but for some purposes we need just the year.
    @property
    def publication_just_the_year(self):
        publications = self.bibframe_master.get("publication", [])
        for publication in publications:
            if publication.get("@type", "").lower() == "publication":
                try:
                    return int(publication.get("date")[:4])
                except ValueError:
                    return publication.get("date")[:4]
        return None

    @property
    def output_types(self):
        genre_forms = self.bibframe_master.get("instanceOf", {}).get("genreForm")
        svep_url = "https://id.kb.se/term/swepub/svep/"
        swedish_list_url = "https://id.kb.se/term/swepub/swedishlist"
        # Example output types: https://id.kb.se/term/swepub/publication/journal-article
        # or https://id.kb.se/term/swepub/publication
        output_type_re = r"^https://id\.kb\.se/term/swepub/[a-z_\-]+/*[a-z_\-]*$"
        output_types = []
        if genre_forms:
            for genre_form in genre_forms:
                gf_id = genre_form.get("@id", "")
                if gf_id.strip().startswith(svep_url) or gf_id.strip().startswith(swedish_list_url):
                    continue
                m = re.match(output_type_re, gf_id)
                if m is None:
                    continue
                output_types.append(m.group(0))
        return output_types

    @property
    def publication_status(self):
        notes = self.bibframe_master.get("instanceOf", {}).get("hasNote", [])
        for note in notes:
            if note.get("@type", "") == "PublicationStatus":
                return note.get("@id")
        return None

    @property
    def content_marking(self):
        svep_url = "https://id.kb.se/term/swepub/svep/"
        genre_form = self.bibframe_master.get("instanceOf", {}).get("genreForm", [])
        for gf in genre_form:
            gf_id = gf.get("@id", "")
            if gf_id.strip().startswith(svep_url):
                prefix_len = len(svep_url)
                total_len = len(gf_id)
                return gf_id[prefix_len : total_len + 1]
        return None

    @property
    def creator_count(self):
        notes = self.bibframe_master.get("instanceOf", {}).get("hasNote", [])
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

        include_every_part = False
        # include all subparts as default,
        # if include_all
        # or if 'creators' has been chosen but no subfields have been chosen
        if self.include_all or all(field not in self._chosen_fields for field in CREATOR_FIELDS):
            include_every_part = True

        contributors = self.bibframe_master.get("instanceOf", {}).get("contribution", [])

        for contrib in contributors:
            if contrib.get("agent", {}).get("@type", "") == "Person":
                roles = contrib.get("role", [])
                for role in roles:
                    if role.get("@id", "") in creator_id_list:
                        person = dict()
                        if include_every_part or "givenName" in self._chosen_fields:
                            person.update({"givenName": contrib.get("agent", {}).get("givenName")})
                        if include_every_part or "familyName" in self._chosen_fields:
                            person.update(
                                {"familyName": contrib.get("agent", {}).get("familyName")}
                            )
                        if include_every_part or "localId" in self._chosen_fields:
                            person = _add_id_to_person(
                                person, contrib.get("agent", {}), "Local", "localId"
                            )
                        if include_every_part or "localIdBy" in self._chosen_fields:
                            person = _add_id_by_code_to_person(
                                person, contrib.get("agent", {}), "Local", "localIdBy"
                            )
                        if include_every_part or "ORCID" in self._chosen_fields:
                            person = _add_id_to_person(
                                person, contrib.get("agent", {}), "ORCID", "ORCID"
                            )
                        if include_every_part or "affiliation" in self._chosen_fields:
                            person = self._add_affiliation_to_person_recursive(
                                person, contrib.get("hasAffiliation", [])
                            )
                        if include_every_part or "freetext_affiliations" in self._chosen_fields:
                            person = self._add_freetext_affiliation_to_person(
                                person, contrib.get("hasAffiliation", [])
                            )
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

        contributors = self.bibframe_master.get("instanceOf", {}).get("contribution", [])
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
        titles = self.bibframe_master.get("instanceOf", {}).get("hasTitle", [])
        for title in titles:
            if title.get("@type", "") == "Title":
                return _create_title_string(title)
        return None

    @property
    def publication_type(self):
        genre_forms = self.bibframe_master.get("instanceOf", {}).get("genreForm", [])
        # Example publication type: https://id.kb.se/term/swepub/JournalArticle
        # Publication types don't contain another slash after swepub/
        pub_type_re = r"^https://id\.kb\.se/term/swepub/[A-Z]{1}[a-zA-Z_\-]+$"
        for genre_form in genre_forms:
            gf_id = genre_form.get("@id")
            m = re.match(pub_type_re, gf_id)
            if m is None:
                continue
            return m.group(0)
        return None

    def _add_affiliation_to_person_recursive(self, person, affiliations):
        if person.get("affiliation") is None:
            person.update({"affiliation": None})

        for affiliation in affiliations:
            if affiliation.get("@type", "") == "Organization":
                for id_by in affiliation.get("identifiedBy", []):
                    if (
                        id_by.get("@type", "") == "URI"
                        and id_by.get("source", {}).get("@type", "") == "Source"
                        and id_by.get("source", {}).get("code", "") == "kb.se"
                    ):
                        uri_value = id_by.get("value")
                        person["affiliation"] = uri_value
                        return person

            # check if there are nested affiliations
            nested_affiliations = affiliation.get("hasAffiliation", [])
            if nested_affiliations is not None and len(nested_affiliations) > 0:
                person = self._add_affiliation_to_person_recursive(person, nested_affiliations)

        return person

    def _add_freetext_affiliation_to_person(self, person, affiliations):
        if person.get("freetext_affiliations") is None:
            person.update({"freetext_affiliations": None})

        freetext_affils = []
        for affiliation in affiliations:
            affil_tree = self._get_freetext_affiliations(affiliation)
            if affil_tree:
                freetext_affils.append(affil_tree)
        if freetext_affils:
            person["freetext_affiliations"] = freetext_affils
        return person

    def _get_freetext_affiliations(self, affiliation):
        if affiliation.get("@type", "") != "Organization":
            return None

        nested_affils = []
        affil_name = affiliation.get("name")
        if affil_name:
            nested_affils.append(affil_name)
        sub_affils = affiliation.get("hasAffiliation", [])
        for sub_affil in sub_affils:
            subsub_affils = self._get_freetext_affiliations(sub_affil)
            if subsub_affils:
                nested_affils.extend(subsub_affils)
        return nested_affils

    @property
    def open_access(self):
        """Returns true if publication is open access
        We check if there is an AccessPolicy with a value of 'gratis or an
        electronicLocator with a note 'free', or 'free/<date>' if date has
        passed."""
        free_note_re = r"^free(/[0-9]{4}\-[0-9]{2}\-[0-9]{2})*$"
        # Embargoes are more important than AccessPolicies
        if self._is_embargoed():
            return False
        ua_policies = self.bibframe_master.get("usageAndAccessPolicy", [])
        for policy in ua_policies:
            if policy.get("@type", "") == "AccessPolicy":
                label = policy.get("label", "")
                if "gratis" in label:
                    return True
                elif "restricted" in label:
                    return False
        electronic_locators = self.bibframe_master.get("electronicLocator", [])
        for electronic_locator in electronic_locators:
            if (
                electronic_locator.get("@type", "") == "MediaObject"
                and len(electronic_locator.get("uri", "")) > 0
            ):
                ua_policies = electronic_locator.get("usageAndAccessPolicy", [])
                for policy in ua_policies:
                    ua_id = policy.get("@id", "")
                    if ua_id == "https://id.kb.se/policy/oa/gratis":
                        return True
                    elif ua_id == "https://id.kb.se/policy/oa/restricted":
                        return False

            if (
                electronic_locator.get("@type", "") == "Resource"
                and len(electronic_locator.get("uri", "")) > 0
            ):
                for note in electronic_locator.get("hasNote", []):
                    label = note.get("label", "")
                    m = re.match(free_note_re, label)
                    if m is None:
                        continue
                    if m.group(0):
                        if len(m.group(0).split("/")) > 1:
                            free_from = m.group(0).split("/")[1]
                            free_from_date = None
                            if free_from and len(free_from) > 1:
                                try:
                                    free_from_date = dateutil_parse(free_from).date()
                                except ValueError:
                                    continue
                            now_date = datetime.now().date()
                            if free_from_date and now_date >= free_from_date:
                                return True
                        else:
                            # ok, if note without date, eg "free"
                            return True
        return False

    @property
    def open_access_version(self):
        for electronic_locator in self.bibframe_master.get("electronicLocator", []):
            for note in electronic_locator.get("hasNote", []):
                if note.get("@id", "") in [
                    "https://id.kb.se/term/swepub/Submitted",
                    "https://id.kb.se/term/swepub/Accepted",
                    "https://id.kb.se/term/swepub/Published"
                ]:
                    return note.get("@id")
        return None

    @property
    def DOAJ(self):
        for status in self.bibframe_master.get("instanceOf", {}).get("status", []):
            if status.get("@id", "") == "https://id.kb.se/term/swepub/journal-is-in-doaj":
                return True
        return False

    def _is_embargoed(self):
        ua_policies = self.bibframe_master.get("usageAndAccessPolicy", [])
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

    @property
    def electronic_locator(self):
        electronic_locators = self.bibframe_master.get("electronicLocator", [])
        for electronic_locator in electronic_locators:
            if (
                electronic_locator.get("@type", "") == "Resource"
                and len(electronic_locator.get("uri", "")) > 0
            ):
                return electronic_locator.get("uri")
        return None

    @property
    def archive_URI(self):
        for id_by in self.bibframe_master.get("identifiedBy", []):
            if id_by.get("@type", "") == "URI" and len(id_by.get("value", "")) > 0:
                return id_by.get("value")
        return None

    @property
    def publication_channel(self):
        project_genreforms = [
            "https://id.kb.se/term/swepub/project",
            "https://id.kb.se/term/swepub/programme",
            "https://id.kb.se/term/swepub/grantAgreement",
            "https://id.kb.se/term/swepub/initiative",
        ]
        part_ofs = self.bibframe_master.get("partOf", [])
        for part_of in part_ofs:
            part_of_type = part_of.get("@type")
            if part_of_type and part_of_type == "Dataset":
                continue
            genreforms = part_of.get("genreForm", [])
            found_blacklisted_gf = False
            for gf in genreforms:
                gf_id = gf.get("@id")
                if gf_id and gf_id in project_genreforms:
                    found_blacklisted_gf = True
            if found_blacklisted_gf:
                continue
            for title in part_of.get("hasTitle", []):
                if title.get("@type", "") == "Title":
                    return _create_title_string(title)
        return None

    @property
    def publisher(self):
        for publication in self.bibframe_master.get("publication", []):
            if publication.get("@type", "") == "Publication":
                if publication.get("agent", {}).get("@type", "") == "Agent":
                    return publication.get("agent", {}).get("label")
        return None

    @property
    def summary(self):
        summaries = self.bibframe_master.get("instanceOf", {}).get("summary", [])
        for summary in summaries:
            if summary.get("@type", "") == "Summary":
                return summary.get("label")
        return None

    @property
    def swedish_list(self):
        swedish_list_url = "https://id.kb.se/term/swepub/swedishlist/"
        genreForm = self.bibframe_master.get("instanceOf", {}).get("genreForm", [])
        for gf in genreForm:
            gf_id = gf.get("@id", "").strip()
            if gf_id.startswith(swedish_list_url):
                return gf_id
        return None

    @property
    def uka_subjects(self):

        subjects = dict()
        should_include_one_digit_topics = False
        should_include_three_digit_topics = False
        should_include_five_digit_topics = False

        if (
            self.include_all
            or "oneDigitTopics" in self._chosen_fields
            or "subjects" in self._chosen_fields
        ):  # noqa: W503
            should_include_one_digit_topics = True

        if (
            self.include_all
            or "threeDigitTopics" in self._chosen_fields
            or "subjects" in self._chosen_fields
        ):  # noqa: W503
            should_include_three_digit_topics = True

        if (
            self.include_all
            or "fiveDigitTopics" in self._chosen_fields
            or "subjects" in self._chosen_fields
        ):  # noqa: W503
            should_include_five_digit_topics = True

        if should_include_one_digit_topics:
            subjects.update({"oneDigitTopics": []})
        if should_include_three_digit_topics:
            subjects.update({"threeDigitTopics": []})
        if should_include_five_digit_topics:
            subjects.update({"fiveDigitTopics": []})

        for subject in self.bibframe_master.get("instanceOf", {}).get("subject", []):
            if (
                subject.get("inScheme", {}).get("code", "") == "uka.se"
                and subject.get("@type", "") == "Topic"
            ):
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
        subjects = self.bibframe_master.get("instanceOf", {}).get("subject", [])
        for subject in subjects:
            pref_label = subject.get("prefLabel")
            if pref_label:
                subj_list.append(pref_label)
        return subj_list

    @property
    def languages(self):
        """Return all languages specified in master publication."""
        result = []
        langs = self.bibframe_master.get("instanceOf", {}).get("language", [])
        for lang in langs:
            if "@type" in lang and lang["@type"] == "Language":
                if "code" in lang:
                    result.append(lang["code"])
        return result

    def _get_instance_identifier(self, id_type):
        ids = self.bibframe_master.get("identifiedBy", [])
        for identifiedby_id in ids:
            if identifiedby_id.get("@type", "") == id_type:
                return identifiedby_id.get("value")
        return None

    def _get_instance_indirect_identifier(self, identifier_type):
        inids = self.bibframe_master.get("indirectlyIdentifiedBy", [])
        for in_id in inids:
            if in_id.get("@type", "") == identifier_type:
                return in_id.get("value")
        return None

    @property
    def ISI(self):
        return self._get_instance_identifier(id_type="ISI")

    @property
    def DOI(self):
        doi_list = []
        ids = self.bibframe_master.get("identifiedBy", [])
        for identifier in ids:
            if identifier.get("@type", "") == "DOI":
                doi_list.append(identifier.get("value"))
        part_ofs = self.bibframe_master.get("partOf", [])
        for part_of in part_ofs:
            ids = part_of.get("identifiedBy", [])
            for identifier in ids:
                if identifier.get("@type", "") == "DOI":
                    doi_list.append(identifier.get("value"))
        return doi_list

    @property
    def ISSN(self):
        return self._get_ISSN_or_ISBN(id_type="ISSN")

    @property
    def ISBN(self):
        return self._get_ISSN_or_ISBN(id_type="ISBN")

    def _get_ISSN_or_ISBN(self, id_type):
        id_list = []
        id_list.extend(
            _get_root_dict_ids(root_dict=self.bibframe_master, label="partOf", id_type=id_type)
        )
        for part_of in self.bibframe_master.get("partOf", []):
            id_list.extend(
                _get_root_dict_ids(root_dict=part_of, label="hasSeries", id_type=id_type)
            )
        id_list.extend(
            _get_root_dict_ids(root_dict=self.bibframe_master, label="hasSeries", id_type=id_type)
        )
        id_list.extend(
            _get_ids_from_dict(
                root_dict=self.bibframe_master, label="identifiedBy", id_type=id_type
            )
        )
        id_list.extend(
            _get_ids_from_dict(
                root_dict=self.bibframe_master, label="indirectlyIdentifiedBy", id_type=id_type
            )
        )
        return id_list

    @property
    def series_title(self):
        serials = self.bibframe_master.get("hasSeries", [])
        for part_of in self.bibframe_master.get("partOf", []):
            for serial in part_of.get("hasSeries", []):
                serials.append(serial)
        for serial in serials:
            titles = serial.get("hasTitle", [])
            for title in titles:
                if title.get("@type", "") == "Title":
                    return _create_title_string(title)
        return None

    @property
    def series(self):
        _series = []
        serials = self.bibframe_master.get("hasSeries", [])

        for part_of in self.bibframe_master.get("partOf", []):
            for serial in part_of.get("hasSeries", []):
                serials.append(serial)

        for serial in serials:
            obj = {}
            if serial.get("hasTitle", None):
                obj["hasTitle"] = serial.get("hasTitle")
            if serial.get("identifiedBy", None):
                obj["identifiedBy"] = serial.get("identifiedBy")
            if obj:
                _series.append(obj)

        return _series or None

    @property
    def level(self):
        """Return the publication's level according to the Swedish List."""
        if (
            "instanceOf" not in self._bibframe_master
            or "genreForm" not in self._bibframe_master["instanceOf"]
        ):
            return None

        for gform in self._bibframe_master["instanceOf"]["genreForm"]:
            # Peer-reviewed always trumps non-peer-reviewed
            if "@id" in gform and gform["@id"] == str(Level.PEERREVIEWED):
                return Level.PEERREVIEWED.value

            if "@id" in gform and gform["@id"] == str(Level.NONPEERREVIEWED):
                return Level.NONPEERREVIEWED.value
        return None

    @property
    def is_swedishlist(self):
        # instanceOf.genreForm.@id": "https://id.kb.se/term/swepub/swedishlist/peer-reviewed"
        for gf in self._bibframe_master.get("instanceOf", {}).get("genreForm", []):
            if gf.get("@id", "") == "https://id.kb.se/term/swepub/swedishlist/peer-reviewed":
                return True
        return False

    @property
    def ssif_1_codes(self):
        uka_subject_codes = []
        for subject in self.bibframe_master.get("instanceOf", {}).get("subject", []):
            if (
                subject.get("inScheme", {}).get("code", "") == "uka.se"
                and subject.get("@type", "") == "Topic"
            ):
                subject_code = subject.get("code", "").strip()
                if subject_code:
                    uka_subject_codes.append(subject_code[0])

        return list(set(uka_subject_codes))


    @property
    def autoclassified(self):
        for subject in self.bibframe_master.get("instanceOf", {}).get("subject", []):
            for note in subject.get("hasNote", []):
                if note.get("label", "") == "Autoclassified by Swepub":
                    return True
        return False
