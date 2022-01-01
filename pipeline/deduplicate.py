#import os
import json
#import re
#import sqlite3
from difflib import SequenceMatcher
from storage import commit_sqlite, get_cursor, open_existing_storage

"""Max length in characters to compare text"""
MAX_LENGTH_STRING_TO_COMPARE = 1000

"""Match ratios for various pubications fields, see SequenceMatcher """
STRING_MATCH_RATIO_MAIN_TITLE = 0.9
STRING_MATCH_RATIO_SUB_TITLE = 0.9
STRING_MATCH_RATIO_SUMMARY = 0.9

def _compare_text(master_text, candidate_text, match_ratio):
    if _empty_string(master_text) and _empty_string(candidate_text):
        return True
    if _empty_string(master_text) or _empty_string(candidate_text):
        return False
    master_text = master_text[0:MAX_LENGTH_STRING_TO_COMPARE]
    candidate_text = candidate_text[0:MAX_LENGTH_STRING_TO_COMPARE]
    master_text = master_text.lower()
    candidate_text = candidate_text.lower()
    sequence_matcher = SequenceMatcher(a=master_text,
                                       b=candidate_text)
    sequence_matcher_ratio = sequence_matcher.quick_ratio()
    return sequence_matcher_ratio >= match_ratio


def _empty_string(s):
    if s:
        if not s.strip():
            return True
        else:
            return False
    return True


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

def _split_title_subtitle_first_colon(title):
    try:
        parts = title.split(':', 1)
        maintitle = parts[0]
        subtitle = None
        if len(parts) == 2:
            subtitle = parts[1]
            subtitle = subtitle.strip()
        return maintitle, subtitle
    except AttributeError:
        return title, None


def _main_title(body):
    """Return value of instanceOf.hasTitle[?(@.@type=="Title")].mainTitle if it exists and
    there is no subtitle.
    If a subtitle exist then the return value is split at the first colon and the first string
    is returned,
    i.e 'main:sub' returns main.
    None otherwise """
    has_title_array = body.get('instanceOf', {}).get('hasTitle', [])
    for h_t in has_title_array:
        if isinstance(h_t, dict) and h_t.get('@type') == 'Title':
            main_title_raw = h_t.get('mainTitle')
            sub_title_raw = h_t.get('subtitle')
            break
    if not _empty_string(sub_title_raw):
        return main_title_raw
    main_title, sub_title = _split_title_subtitle_first_colon(main_title_raw)
    if not _empty_string(main_title):
        return main_title
    else:
        return None

def _sub_title(self):
    """Return value for instanceOf.hasTitle[?(@.@type=="Title")].subtitle if it exists,
    if it does not exist then the value of instanceOf.hasTitle[?(@.@type=="Title")].mainTitle
    is split at the first colon and the second string is returned, i.e 'main:sub' returns sub.
    None otherwise """
    sub_title_array = self.body.get('instanceOf', {}).get('hasTitle', [])
    for h_t in sub_title_array:
        if isinstance(h_t, dict) and h_t.get('@type') == 'Title' and h_t.get('subtitle'):
            return h_t.get('subtitle')
        else:
            main_title_raw = h_t.get('mainTitle')
            break
    main_title, sub_title = _split_title_subtitle_first_colon(main_title_raw)
    if not _empty_string(sub_title):
        return sub_title
    else:
        return None

def _same_ids(master_ids, candidate_ids):
    if len(master_ids) == 0 or len(candidate_ids) == 0:
        return False
    return set(master_ids) == set(candidate_ids)

def _get_identifiedby_ids(body, identifier=''):
    """Return either identifiedBy ids values if identifier is set otherwise whole identifiedBy array """
    return _get_ids(body, 'identifiedBy', identifier)

def _get_indirectly_identifiedby_ids(body, identifier=''):
    """Return either indirectlyIdentifiedBy ids values if identifier is set
    otherwise whole indirectlyIdentifiedBy array """
    return _get_ids(body, 'indirectlyIdentifiedBy', identifier)

def _has_same_main_title(a, b):
    """True if publication has the same main title"""
    return _compare_text(_main_title(a), _main_title(b), STRING_MATCH_RATIO_MAIN_TITLE)

#def _has_same_sub_title(self, publication):
#    """True if publication has the same sub title"""
#    return compare_text(self.sub_title, publication.sub_title, self.STRING_MATCH_RATIO_SUB_TITLE)

#def _has_same_summary(self, publication):
#    """True if publication has the same summary"""
#    return compare_text(self.summary, publication.summary, self.STRING_MATCH_RATIO_SUMMARY)

#def _has_same_partof_main_title(self, publication):
#    """ Returns True if partOf has the same main title """
#    if self.part_of_with_title and publication.part_of_with_title:
#        return self.part_of_with_title.has_same_main_title(publication.part_of_with_title)
#    else:
#        return False

#def _has_same_genre_form(self, publication):
#    """True if publication has all the genreform the same"""
#    if self.genre_form and publication.genre_form:
#        return set(self.genre_form) == set(publication.genre_form)
#    return False

#def _has_same_publication_date(self, publication):
#    """True if publication dates are the same by comparing the shortest date"""
#    master_pub_date_str = self.publication_date
#    candidate_pub_date_str = publication.publication_date
#    if empty_string(master_pub_date_str) or empty_string(candidate_pub_date_str):
#        return False
#    master_pub_date_str = master_pub_date_str.strip()
#    candidate_pub_date_str = candidate_pub_date_str.strip()
#    if len(master_pub_date_str) > len(candidate_pub_date_str):
#        master_pub_date_str = master_pub_date_str[:len(candidate_pub_date_str)]
#    elif len(master_pub_date_str) < len(candidate_pub_date_str):
#        candidate_pub_date_str = candidate_pub_date_str[:len(master_pub_date_str)]
#    return master_pub_date_str == candidate_pub_date_str

def _has_same_ids(a, b):
    """ True if one of ids DOI, PMID, ISI, ScopusID and ISBN are the same for identifiedBy
    or if ISBN id are the same for indirectlyIdentifiedBy"""
    if _same_ids(_get_identifiedby_ids(a, 'DOI'), _get_identifiedby_ids(b, 'DOI')):
        return True
    if _same_ids(_get_identifiedby_ids(a, 'PMID'), _get_identifiedby_ids(b, 'PMID')):
        return True
    if _same_ids(_get_identifiedby_ids(a, 'ISI'), _get_identifiedby_ids(b, 'ISI')):
        return True
    if _same_ids(_get_identifiedby_ids(a, 'ScopusID'), _get_identifiedby_ids(b, 'ScopusID')):
        return True
    if _same_ids(_get_identifiedby_ids(a, 'ISBN'), _get_identifiedby_ids(b, 'ISBN')):
        return True
    if _same_ids(_get_indirectly_identifiedby_ids(a, 'ISBN'), _get_indirectly_identifiedby_ids(b, 'ISBN')):
        return True
    return False

def _has_compatible_doi_set(a, b):
    l1 = _get_identifiedby_ids(a, 'DOI')
    l2 = _get_identifiedby_ids(b, 'DOI')

    # If either set is empty, they're compatible
    if (not l1) or (not l2):
        return True

    l1.sort()
    l2.sort()
    if l1 == l2:
        return True
    return False

# Are publications 'a' and 'b' similiar enough to justify clustering them?
# 'a' and 'b' are row IDs into the 'converted' table.
def _is_close_enough(a_rowid, b_rowid):
    """Two publications are duplicates if they have (
    1. Have the same (oai) id
        _or_
    2. Same title and one of directly identified ids (DOI, PMID, ISI, ScopusID, ISBN)
        or indirectly identified ISBN
        _or_
    3. None are conferancepaper -> Same title, subtitle, summary, publication date and genreform
        _or_
    4. One or both are conferancepaper -> Same title, subtitle, summary, publication date and partof.maintitle )
        _and_
    5. Their respective sets of DOIs (if any) are compatible
    """

    cursor = get_cursor()
    cursor.execute("""
    SELECT
        data
    FROM
        converted
    WHERE
        rowid = ? OR rowid = ?;
    """, (a_rowid, b_rowid))
    candidate_rows = cursor.fetchall() # Will give exactly 2 rows, per definition
    a = json.loads(candidate_rows[0][0])
    b = json.loads(candidate_rows[1][0])

    # 5.
    if not _has_compatible_doi_set(a, b):
        return False

    # 1. # THIS IS POINTLESS, CANT HAPPEN ANYMORE
    if a["@id"] == b["@id"]:
        return True

    # 2.
    #print(f'*** {b["@id"]} now to be checked for duplicity (2) with {a["@id"]}')
    #if _has_same_main_title(a, b) \
    #        and a.has_same_ids(b):
        #print(f'*** {b["@id"]} was (type 2) duplicate of {a["@id"]}')
    #    return True
    #print(f'*** {b["@id"]} was NOT (type 2) duplicate of {a["@id"]}')

    # 3.
    #if a.has_same_main_title(b) \
    #        and CONFERENCE_PAPER_GENREFORM not in a.genre_form \
    #        and CONFERENCE_PAPER_GENREFORM not in b.genre_form \
    #        and a.has_same_sub_title(b) \
    #        and a.has_same_summary(b) \
    #        and a.has_same_publication_date(b) \
    #        and a.has_same_genre_form(b):
    #    return True

    # 4.
    #if a.has_same_main_title(b) \
    #        and (CONFERENCE_PAPER_GENREFORM in a.genre_form or CONFERENCE_PAPER_GENREFORM in b.genre_form) \
    #        and a.has_same_sub_title(b) \
    #        and a.has_same_summary(b) \
    #        and a.has_same_publication_date(b) \
    #        and a.has_same_partof_main_title(b):
    #    return True

    return False

# Generate clusters of publications, based on some shared piece of data
# (a title or an ID). Sharing this information is only enough to be considered
# a "candidate". To actually be clustered, one must also pass the
# _is_close_enough(a, b) test.
# This function _will_ generate overlapping clusters.
def _generate_clusters():
    next_cluster_id = 0

    cursor = get_cursor()
    for candidatelist_row in cursor.execute("""
    SELECT
        group_concat(converted.id, "\n")
    FROM
        clusteringidentifiers
    LEFT JOIN
        converted ON clusteringidentifiers.converted_id = converted.id
    GROUP BY
        clusteringidentifiers.identifier;
    """):
        candidates = candidatelist_row[0].split('\n')
        if len(candidates) > 1:
            #print(json.dumps(candidates))
            print(f"Will now check candidate list of size: {len(candidates)}")

            # Pre-place the first candidate in a cluster of its own.
            clusters = [[0]] # A list of clusters, each cluster a list of record ids
            unclustered_indices = [*range(1, len(candidates))] # All but first

            while len(unclustered_indices) > 0:

                progress = False

                # candidate_index and in_cluster_index are both integer indexes into the "candidates" list.
                # The "candidates" list in turn, contains rowids to the actual records.
        
                try:
                    for cluster in clusters:
                        for candidate_index in unclustered_indices:
                            for in_cluster_index in cluster:
                                if in_cluster_index != candidate_index and \
                                _is_close_enough(candidates[in_cluster_index], candidates[candidate_index]):
                                    cluster.append(candidate_index)
                                    unclustered_indices.remove(candidate_index)
                                    progress = True
                                    raise "Python bullshit" # Goto? break-to-label? Anything but this? Really Python...
                except Exception as e:
                    pass

                
                # If no more records could be placed in an existing cluster, create a new one
                if not progress:
                    clusters.append([unclustered_indices.pop()])

            #print(json.dumps(clusters))

            inner_cursor = get_cursor()
            for cluster in clusters:
                for publication in cluster:
                    inner_cursor.execute("""
                    INSERT INTO cluster(cluster_id, converted_id) VALUES(?, ?);
                    """, (next_cluster_id, candidates[publication]))
                next_cluster_id += 1
            commit_sqlite()

# Join any clusters that have one or more common publications.
def _join_overlapping_clusters():
    cursor = get_cursor()
    cursor.execute("""
    SELECT
        count(cluster_id), group_concat(cluster_id, "\n")
    FROM
        cluster
    GROUP BY
        converted_id;
    """)
    rows = cursor.fetchall() # This is necessary in order to allow modification of the table while iterating

    # Holds information on already merged clusters, so for example 1 -> 2 means cluster 1 no longer exists,
    # but it's publications are now in 2 instead.
    merged_into = {}

    for cluster_row in rows:
        cluster_count = cluster_row[0]
        if cluster_count > 1:
            clusters = cluster_row[1].split('\n')

            print(f"-----\nNow considering merging: {clusters}")

            cluster_a = clusters.pop()

            while len(clusters) > 0:
                cluster_b = clusters.pop()

                print(f"  To be merged: {cluster_a} into {cluster_b}")

                # Replace cluster_a and cluster_b with where ever their contents are now
                while cluster_a in merged_into:
                    cluster_a = merged_into[cluster_a]
                while cluster_b in merged_into:
                    cluster_b = merged_into[cluster_b]

                print(f"  After following history: {cluster_a} into {cluster_b}")

                if cluster_a == cluster_b:
                    continue

                # Merge cluster_a into cluster_b
                cursor.execute("""
                UPDATE
                    cluster
                SET
                    cluster_id = ?
                WHERE
                    cluster_id = ?;
                """, (cluster_b, cluster_a))
                merged_into[cluster_a] = cluster_b

                print(f"Merged cluster {cluster_a} into {cluster_b}")

                cluster_a = cluster_b

            print("\n")

            commit_sqlite()
    
    # Given two clusters (A,B,C) and (B,C,D) which have now been joined, there will now be duplicate
    # rows for B and C. These must (should) be cleared:
    cursor.execute("""
    DELETE FROM
        cluster
    WHERE
        rowid NOT IN
        (
            SELECT
                MIN(rowid)
            FROM
                cluster
            GROUP BY
                cluster_id, converted_id
        );
    """)
    commit_sqlite()




def deduplicate():
    _generate_clusters()
    _join_overlapping_clusters()

            

# For debugging
if __name__ == "__main__":    
    open_existing_storage()
    deduplicate()
