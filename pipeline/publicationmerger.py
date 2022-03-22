import copy
from collections import OrderedDict

from pipeline.publication import Contribution, Publication


GENRE_FORMS_TO_MERGE = ["https://id.kb.se/term/swepub/ArtisticWork"]


class PublicationMerger:
    def merge(self, publications):
        """Create a master publication by merging a list of publications."""
        master = self._get_master(publications)
        publication_ids = []
        publication_orgs = []
        for pub in publications:
            publication_ids.append(pub.id)
            publication_orgs.append(pub.source_org)
            master = self._merge(master, pub)
        return master, publication_ids, publication_orgs

    @staticmethod
    def _get_master(publications):
        """Return the publication with most elements."""
        if not publications:
            return None
        master = max(publications, key=lambda pub: pub.elements_size)
        return Publication(copy.deepcopy(master.body))

    def _merge(self, master, candidate):
        """Merge master and candidate publication"""
        if master is None:
            return candidate
        if candidate is None:
            return master
        if master == candidate:
            return master
        master = self._merge_contribution(master, candidate)
        master = self._merge_has_notes(master, candidate)
        master = self._merge_genre_forms(master, candidate)
        master = self._merge_subjects(master, candidate)
        master = self._merge_has_series(master, candidate)
        master = self._merge_identifiedby_ids(master, candidate)
        master = self._merge_indirectly_identifiedby_ids(master, candidate)
        master = self._merge_electronic_locators(master, candidate)
        master = self._merge_part_of(master, candidate)
        master = self._merge_publication_information(master, candidate)
        master = self._merge_usage_and_access_policy(master, candidate)
        return master

    @staticmethod
    def _merge_contribution(master, candidate):
        """If same contributions exist in both keep masters unless candidate has kb.se affiliation and master do not
        Otherwise add candidate contributions
        """
        master_contribs = OrderedDict()
        for contrib in master.contributions:
            if contrib.agent_name:
                master_contribs[contrib.agent_name] = contrib
            else:
                master_contribs[id(contrib)] = contrib

        candidate_contribs = OrderedDict()
        for contrib in candidate.contributions:
            if contrib.agent_name:
                candidate_contribs[contrib.agent_name] = contrib
            else:
                candidate_contribs[id(contrib)] = contrib

        master_names = set(master_contribs.keys())
        candidate_names = set(candidate_contribs.keys())
        overlapping = master_names & candidate_names
        new_contribs = candidate_names - overlapping

        for contrib_name in overlapping:

            if _should_replace_affiliation(
                master_contribs[contrib_name], candidate_contribs[contrib_name]
            ):
                master_contribs[contrib_name].affiliations = candidate_contribs[
                    contrib_name
                ].affiliations
            else:
                master_contribs[contrib_name].affiliations = _merge_contrib_affiliations(
                    master_contribs[contrib_name].affiliations,
                    candidate_contribs[contrib_name].affiliations,
                )
            master_contribs[contrib_name].identified_bys = _merge_contrib_identified_by(
                master_contribs[contrib_name].identified_bys,
                candidate_contribs[contrib_name].identified_bys,
            )

        for contrib_name in new_contribs:
            master_contribs[contrib_name] = candidate_contribs[contrib_name]
        master.contributions = list(master_contribs.values())
        return master

    @staticmethod
    def _merge_has_notes(master, candidate):
        """Merge hasNotes by keeping publicationstatus and creator_count from master if it exists,
        otherwise try to get from candidate. Merge new notes from candidate.
        """
        if master.publication_status is None and candidate.publication_status is not None:
            master.publication_status = candidate.publication_status
        if master.has_worse_publication_status_ranking(candidate):
            master.publication_status = candidate.publication_status
        if master.creator_count is None and candidate.creator_count is not None:
            master.creator_count = candidate.creator_count
        master.add_notes(candidate.notes)
        return master

    def _merge_genre_forms(self, master, candidate):
        """Merge genreform if both has GENRE_FORMS_TO_MERGE, currently artisticwork"""
        if self._should_merge_genre_form(master) and self._should_merge_genre_form(candidate):
            master.add_genre_form(candidate.genre_form)
        return master

    @staticmethod
    def _merge_has_series(master, candidate):
        """Merge has series if different ISSN/IssueNumber or different maintitle"""
        master.add_series(candidate)
        return master

    def _merge_subjects(self, master, candidate):
        """Merge subjects if code or prefLabel is new"""
        master_subjects = master.subjects
        candidate_subjects = candidate.subjects
        for cs in candidate_subjects:
            if not self._subject_preflabel_exist_in_master(
                master_subjects, cs
            ) or not self._subject_code_exist_in_master(master_subjects, cs):
                master_subjects.append(cs)
        master.subjects = master_subjects
        return master

    def _merge_identifiedby_ids(self, master, candidate):
        """Merge identifiedbyIds if its ISSN/ISBN or URI and do not exist in master"""
        master_identifiedby_ids = master.identifiedby_ids
        candidate_identifiedby_ids = candidate.identifiedby_ids
        for identifier in candidate_identifiedby_ids:
            if self._id_allowed_to_be_added(master_identifiedby_ids, identifier):
                master_identifiedby_ids.append(identifier)
        master.identifiedby_ids = master_identifiedby_ids
        return master

    def _merge_indirectly_identifiedby_ids(self, master, candidate):
        """Merge indirectlyIdentifiedbyIds if its ISSN/ISBN or URI and do not exist in master"""
        master_indirectly_identifiedby_ids = master.indirectly_identifiedby_ids
        candidate_indirectly_identifiedby_ids = candidate.indirectly_identifiedby_ids
        for identifier in candidate_indirectly_identifiedby_ids:
            if self._id_allowed_to_be_added(master_indirectly_identifiedby_ids, identifier):
                master_indirectly_identifiedby_ids.append(identifier)
        master.indirectly_identifiedby_ids = master_indirectly_identifiedby_ids
        return master

    @staticmethod
    def _merge_electronic_locators(master, candidate):
        """Merge electronicLocator if new, if exist then merge only notes from candidate"""
        master_electronic_locators = master.electronic_locators
        candidate_electronic_locators = candidate.electronic_locators
        for e in candidate_electronic_locators:
            if e not in master_electronic_locators:
                master_electronic_locators.append(e)
            else:
                index = master_electronic_locators.index(e)
                master_electronic_locators[index].add_notes(e.notes)
        master.electronic_locators = master_electronic_locators
        return master

    @staticmethod
    def _merge_part_of(master, candidate):
        """Merge partOf.hasSeries if same identifier or
        (same partOf.hasTitle.mainTitle/subtitle/volumeNumber/issuenumber)."""
        master_part_ofs = master.part_of
        candidate_parts_of = candidate.part_of
        for c_p in candidate_parts_of:
            if c_p not in master_part_ofs:
                master_part_ofs.append(c_p)
            else:
                index = master_part_ofs.index(c_p)
                master_part_of = master_part_ofs[index]
                master_part_of.add_issns(c_p)
                master_part_of.add_isbns(c_p)
                master_part_of.add_series(c_p)
        master.part_of = master_part_ofs
        return master

    @staticmethod
    def _merge_publication_information(master, candidate):
        master_publication_information = master.publication_information
        candidate_publication_information = candidate.publication_information

        if not candidate.publication_information:
            return master

        if not master_publication_information and candidate.publication_information:
            master_publication_information = candidate_publication_information

        if not master_publication_information.agent and candidate.publication_information.agent:
            master_publication_information.agent = candidate_publication_information.agent

        if not master_publication_information.place and candidate.publication_information.place:
            master_publication_information.place = candidate_publication_information.place

        master.publication_information = master_publication_information
        return master

    @staticmethod
    def _merge_usage_and_access_policy(master, candidate):
        if not candidate.usage_and_access_policy:
            return master

        if not master.usage_and_access_policy and candidate.usage_and_access_policy:
            master.usage_and_access_policy = candidate.usage_and_access_policy
            return master

        (
            m_access_policies,
            m_embargoes,
            m_links,
            m_others,
        ) = master.usage_and_access_policy_by_type
        (
            c_access_policies,
            c_embargoes,
            c_links,
            c_others,
        ) = candidate.usage_and_access_policy_by_type

        access_policies = []
        if m_access_policies and not c_access_policies:
            access_policies = m_access_policies
        elif c_access_policies and not m_access_policies:
            access_policies = c_access_policies
        else:
            # There can be more than one access policy in a publication.
            # Since we don't know anything about the order between
            # publications, we just stick swith default list order
            # and compare policies at the same index. `gratis` trumps
            # `restricted` (and everything else).
            if len(m_access_policies) < len(c_access_policies):
                shortest = m_access_policies
                longest = c_access_policies
            else:
                shortest = c_access_policies
                longest = m_access_policies
            for i in range(len(shortest)):
                item = m_access_policies[i]
                m_label = m_access_policies[i].get("label")
                c_label = c_access_policies[i].get("label")
                if m_label != "gratis" and c_label == "gratis":
                    item = c_access_policies[i]
                access_policies.insert(i, item)
            # Add any trailing policies without touching them
            access_policies.extend(longest[len(shortest):])

        embargoes = m_embargoes
        if not embargoes and c_embargoes:
            embargoes = c_embargoes

        # Quadratic, but these lists *should* never contain more than a few
        # elements.
        links = m_links
        for link in c_links:
            if link not in links:
                links.append(link)

        # Quadratic, but these lists *should* never contain more than a few
        # elements.
        others = m_others
        for other in c_others:
            if other not in others:
                others.append(other)

        master.usage_and_access_policy = access_policies + embargoes + links + others
        return master

    @staticmethod
    def _should_merge_genre_form(publication):
        for genre_forms_to_merge in GENRE_FORMS_TO_MERGE:
            if genre_forms_to_merge in publication.genre_form:
                return True
        return False

    @staticmethod
    def _subject_preflabel_exist_in_master(master_subjects, cs):
        return any(ms.get("prefLabel", None) == cs.get("prefLabel") for ms in master_subjects)

    @staticmethod
    def _subject_code_exist_in_master(master_subjects, cs):
        return any(
            ms.get("code", None) == cs.get("code")
            and ms.get("language", None) == cs.get("language")
            for ms in master_subjects
        )

    @staticmethod
    def _id_allowed_to_be_added(master_ids, allowed_id):
        """ID is allowed to be added if its ISSN/ISBN, URI or does not already exist in master_ids"""
        id_type = allowed_id["@type"]
        # flake8: noqa W504
        return allowed_id not in master_ids and (
            id_type == "ISSN"
            or id_type == "ISBN"
            or id_type == "URI"
            or len(list(filter(lambda x: (x["@type"] == id_type), master_ids))) == 0
        )


def _should_replace_affiliation(master_contrib, candidate_contrib):
    is_better_affil = has_kb_se_affiliation(candidate_contrib) and not has_kb_se_affiliation(
        master_contrib
    )
    no_master_affils = has_affiliations(candidate_contrib) and not has_affiliations(master_contrib)
    return is_better_affil or no_master_affils


def has_kb_se_affiliation(affiliations):
    if not affiliations:
        return False
    if isinstance(affiliations, Contribution):
        return has_kb_se_affiliation(affiliations.affiliations)
    for affiliation in affiliations:
        if affiliation.get("@type") == "Organization":
            for id_by in affiliation.get("identifiedBy", []):
                if (
                    id_by.get("@type", "") == "URI"
                    and id_by.get("source", {}).get("@type", "") == "Source"
                    and id_by.get("source", {}).get("code", "") == "kb.se"
                ):
                    return True
        nested_affiliations = affiliation.get("hasAffiliation", [])
        if len(nested_affiliations) > 0:
            return has_kb_se_affiliation(nested_affiliations)
    return False


def has_affiliations(affiliations):
    if isinstance(affiliations, Contribution):
        return has_affiliations(affiliations.affiliations)
    if affiliations and len(affiliations) > 0:
        return True
    return False


def _merge_contrib_identified_by(master_contrib_identified_bys, candidate_contrib_identified_bys):
    candidate_contrib_orcid_identified_bys = [
        x for x in candidate_contrib_identified_bys if x.get("@type") == "ORCID"
    ]
    for candidate_contrib_orcid_identified_by in candidate_contrib_orcid_identified_bys:
        if candidate_contrib_orcid_identified_by not in master_contrib_identified_bys:
            master_contrib_identified_bys.append(candidate_contrib_orcid_identified_by)
    return master_contrib_identified_bys


def _merge_contrib_affiliations(master_contrib_affiliations, canidate_contrib_affiliations):
    for candidate_contrib_affiliation in canidate_contrib_affiliations:
        if candidate_contrib_affiliation not in master_contrib_affiliations:
            master_contrib_affiliations.append(candidate_contrib_affiliation)
    return master_contrib_affiliations
