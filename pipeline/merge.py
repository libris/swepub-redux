from typing import Dict
from storage import commit_sqlite, get_cursor, open_existing_storage
from collections import OrderedDict
import json

def _safe_concat(first, second, separator=' '):
    if first and second:
        return first + separator + second
    elif first:
        return first
    elif second:
        return second
    else:
        return None

def _contrib_agent_name(contrib):
    """Return agent.name as comma-separated string if exist, otherwise agent_given_name + ' ' + agent_family_name"""
    _agent_name = contrib.get('agent', {}).get('name', None)

    if _agent_name and len(_agent_name) > 0:
        if isinstance(_agent_name, list):
            return ', '.join(_agent_name)
        return _agent_name
    else:
        return _safe_concat(contrib.get('agent', {}).get('familyName', None), contrib.get('agent', {}).get('givenName', None))

def _has_affiliations(affiliations):
    if isinstance(affiliations, Dict) and 'hasAffiliation' in affiliations:
        return _has_affiliations(affiliations.get('hasAffiliation'))
    if affiliations and len(affiliations) > 0:
        return True
    return False

def _has_kb_se_affiliation(affiliations):
    if not affiliations:
        return False
    if isinstance(affiliations, Dict) and 'hasAffiliation' in affiliations:
        return _has_kb_se_affiliation(affiliations.get('hasAffiliation'))
    for affiliation in affiliations:
        if affiliation.get("@type") == "Organization":
            for id_by in affiliation.get("identifiedBy", []):
                if id_by.get("@type", "") == "URI" \
                        and id_by.get("source", {}).get("@type", "") == "Source" \
                        and id_by.get("source", {}).get("code", "") == "kb.se":
                    return True
        nested_affiliations = affiliation.get("hasAffiliation", [])
        if len(nested_affiliations) > 0:
            return _has_kb_se_affiliation(nested_affiliations)
    return False

def _should_replace_affiliation(base_contrib, candidate_contrib):
    is_better_affil = _has_kb_se_affiliation(candidate_contrib) and not _has_kb_se_affiliation(base_contrib)
    no_master_affils = _has_affiliations(candidate_contrib) and not _has_affiliations(base_contrib)
    return is_better_affil or no_master_affils

def _merge_contrib_identified_by(master_contrib_identified_bys, candidate_contrib_identified_bys):
    candidate_contrib_orcid_identified_bys = \
        [x for x in candidate_contrib_identified_bys if x.get('@type') == 'ORCID']
    for candidate_contrib_orcid_identified_by in candidate_contrib_orcid_identified_bys:
        if candidate_contrib_orcid_identified_by not in master_contrib_identified_bys:
            master_contrib_identified_bys.append(candidate_contrib_orcid_identified_by)
    return master_contrib_identified_bys


def _merge_contrib_affiliations(master_contrib_affiliations, canidate_contrib_affiliations):
    for candidate_contrib_affiliation in canidate_contrib_affiliations:
        if candidate_contrib_affiliation not in master_contrib_affiliations:
            master_contrib_affiliations.append(candidate_contrib_affiliation)
    return master_contrib_affiliations

def _merge_contribution(base, candidate):
    """ If same contributions exist in both, keep bases's unless candidate has kb.se affiliation and base does not.
    Otherwise add candidate contributions
    """
    base_contribs = OrderedDict()
    for contrib in base.get('contribution', []):
        _agent_name = _contrib_agent_name(contrib)
        if _agent_name:
            base_contribs[_agent_name] = contrib
        else:
            base_contribs[id(contrib)] = contrib

    candidate_contribs = OrderedDict()
    for contrib in candidate.get('contribution', []):
        _agent_name = _contrib_agent_name(contrib)
        if _agent_name:
            candidate_contribs[_agent_name] = contrib
        else:
            candidate_contribs[id(contrib)] = contrib

    master_names = set(base_contribs.keys())
    candidate_names = set(candidate_contribs.keys())
    overlapping = master_names & candidate_names
    new_contribs = candidate_names - overlapping

    for contrib_name in overlapping:

        if _should_replace_affiliation(base_contribs[contrib_name], candidate_contribs[contrib_name]):
            base_contribs[contrib_name]['hasAffiliation'] = candidate_contribs[contrib_name]['hasAffiliation']
        else:
            base_contribs[contrib_name]['hasAffiliation'] = \
                _merge_contrib_affiliations(base_contribs[contrib_name]['hasAffiliation'],
                                            candidate_contribs[contrib_name]['hasAffiliation'])
        base_contribs[contrib_name]['identifiedBy'] = \
            _merge_contrib_identified_by(base_contribs[contrib_name]['identifiedBy'],
                                            candidate_contribs[contrib_name]['identifiedBy'])

    for contrib_name in new_contribs:
        base_contribs[contrib_name] = candidate_contribs[contrib_name]
    base['contribution'] = list(base_contribs.values())

def _element_size(body):
    size = 0
    if 'instanceOf' in body:
        size = sum(len(x) for x in body['instanceOf'].values())
    return size

def merge():
    # For each cluster, generate a union-record, containing as much information as possible
    # from the clusters elements.
    cursor = get_cursor()
    for cluster_row in cursor.execute("""
    SELECT
        cluster_id, group_concat(converted.data, "\n")
    FROM
        cluster
    LEFT JOIN
        converted ON converted.id = cluster.converted_id
    GROUP BY
        cluster_id;
    """):
        cluster_id = cluster_row[0]
        elements_json = cluster_row[1].split('\n')

        # First select the "largest" of the elements, to serve as a base, then
        # merge information into this base from the other elements.
        other_elements = []
        base_element = None
        base_element_size = 0
        for element_json in elements_json:
            element = json.loads(element_json)
            size = _element_size(element)
            if size > base_element_size:
                base_element_size = size
                if base_element is not None:
                    other_elements.append(base_element)
                base_element = element
            else:
                other_elements.append(element)

        #print(f"Selected base element: {base_element}")

        for element in other_elements:
            _merge_contribution(base_element, element) # NEEDS SPECIAL TESTING! CONVERSION WAS MESSY!
            #master = self._merge_has_notes(master, candidate)
            #master = self._merge_genre_forms(master, candidate)
            #master = self._merge_subjects(master, candidate)
            #master = self._merge_has_series(master, candidate)
            #master = self._merge_identifiedby_ids(master, candidate)
            #master = self._merge_indirectly_identifiedby_ids(master, candidate)
            #master = self._merge_electronic_locators(master, candidate)
            #master = self._merge_part_of(master, candidate)
            #master = self._merge_publication_information(master, candidate)
            #master = self._merge_usage_and_access_policy(master, candidate)
        
        # TODO: "VALIDATION" HERE!

        # Write the now merged base element to storage
        inner_cursor = get_cursor()
        inner_cursor.execute("""
        INSERT INTO finalized(cluster_id, data) VALUES(?, ?);
        """, (cluster_id, json.dumps(base_element)))
    commit_sqlite()

# For debugging
if __name__ == "__main__":
    open_existing_storage()
    merge()