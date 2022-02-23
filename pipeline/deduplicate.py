import orjson as json
import time
from multiprocessing import Pool
from storage import *
from util import *

"""Max length in characters to compare text"""
MAX_LENGTH_STRING_TO_COMPARE = 1000

"""Match ratios for various pubications fields, see SequenceMatcher """
STRING_MATCH_RATIO_MAIN_TITLE = 0.9
STRING_MATCH_RATIO_SUB_TITLE = 0.9
STRING_MATCH_RATIO_SUMMARY = 0.9

STRING_MATCH_PARTOF_MAIN_TITLE = 0.8

CONFERENCE_PAPER_GENREFORM = "https://id.kb.se/term/swepub/ConferencePaper"


def _has_same_main_title(a, b):
    """True if publication has the same main title"""
    return compare_text(get_main_title(a), get_main_title(b), STRING_MATCH_RATIO_MAIN_TITLE)


def _has_same_sub_title(a, b):
    """True if publication has the same sub title"""
    return compare_text(get_sub_title(a), get_sub_title(b), STRING_MATCH_RATIO_SUB_TITLE)


def _has_same_summary(a, b):
    """True if publication has the same summary"""
    return compare_text(get_summary(a), get_summary(b), STRING_MATCH_RATIO_SUMMARY)


def _partof_has_same_main_title(partof_a, partof_b):
    """True if part_of has the same main title"""
    # partOf w/o main title should never match
    if part_of_main_title(partof_a) is None and part_of_main_title(partof_b) is None:
        return False
    return compare_text(part_of_main_title(partof_a), part_of_main_title(partof_b), STRING_MATCH_PARTOF_MAIN_TITLE)


def _has_same_partof_main_title(a, b):
    """ Returns True if partOf has the same main title """
    if part_of_with_title(a) and part_of_with_title(b):
        return _has_same_main_title(part_of_with_title(a), part_of_with_title(b))
    else:
        return False


def _has_same_genre_form(a, b):
    """True if a and b have the same genreforms"""
    if genre_form(a) and genre_form(b):
        return set(genre_form(a)) == set(genre_form(b))
    return False


def _has_same_publication_date(a, b):
    """True if publication dates are the same by comparing the shortest date"""
    master_pub_date_str = get_publication_date(a)
    candidate_pub_date_str = get_publication_date(b)
    if empty_string(master_pub_date_str) or empty_string(candidate_pub_date_str):
        return False
    master_pub_date_str = master_pub_date_str.strip()
    candidate_pub_date_str = candidate_pub_date_str.strip()
    if len(master_pub_date_str) > len(candidate_pub_date_str):
        master_pub_date_str = master_pub_date_str[:len(candidate_pub_date_str)]
    elif len(master_pub_date_str) < len(candidate_pub_date_str):
        candidate_pub_date_str = candidate_pub_date_str[:len(master_pub_date_str)]
    return master_pub_date_str == candidate_pub_date_str


def _has_compatible_doi_set(a, b):
    l1 = get_identifiedby_ids(a, 'DOI')
    l2 = get_identifiedby_ids(b, 'DOI')

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

    with get_connection() as connection:
        cursor = connection.cursor()
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
        if _has_same_main_title(a, b) \
                and has_same_ids(a, b):
            #print(f'*** {b["@id"]} was (type 2) duplicate of {a["@id"]}')
            return True
        #print(f'*** {b["@id"]} was NOT (type 2) duplicate of {a["@id"]}')

        # 3.
        if _has_same_main_title(a, b) \
                and CONFERENCE_PAPER_GENREFORM not in genre_form(a) \
                and CONFERENCE_PAPER_GENREFORM not in genre_form(b) \
                and _has_same_sub_title(a, b) \
                and _has_same_summary(a, b) \
                and _has_same_publication_date(a, b) \
                and _has_same_genre_form(a, b):
            return True

        # 4.
        if _has_same_main_title(a, b) \
                and (CONFERENCE_PAPER_GENREFORM in genre_form(a) or CONFERENCE_PAPER_GENREFORM in genre_form(b)) \
                and _has_same_sub_title(a, b) \
                and _has_same_summary(a, b) \
                and _has_same_publication_date(a, b) \
                and _has_same_partof_main_title(a, b):
            return True

    return False


# Generate clusters of publications, based on some shared piece of data
# (a title or an ID). Sharing this information is only enough to be considered
# a "candidate". To actually be clustered, one must also pass the
# _is_close_enough(a, b) test.
# This function _will_ generate overlapping clusters (pairs really).
def _generate_clusters():
    next_cluster_id = 0

    # Set up batching
    batch = []
    tasks = []

    with Pool(processes=16) as pool:

        with get_connection() as connection:
            cursor = connection.cursor()
            inner_cursor = connection.cursor()
            for candidatelist_row in cursor.execute("""
            SELECT
                group_concat(converted.id, "\n")
            FROM
                clusteringidentifiers
            LEFT JOIN
                converted ON clusteringidentifiers.converted_id = converted.id
            WHERE
                converted.deleted = 0
            GROUP BY
                clusteringidentifiers.identifier;
            """):
                candidates = candidatelist_row[0].split('\n')
                if len(candidates) > 1:
                    #print(json.dumps(candidates))
                    batch.append(candidates)

                    if (len(batch) >= 32):
                        while (len(tasks) >= 32):
                            time.sleep(0)
                            n = len(tasks)
                            i = n-1
                            while i > -1:
                                if tasks[i].ready():
                                    result = tasks[i].get()
                                    write_detected_duplicate_pairs(result, inner_cursor, next_cluster_id)
                                    next_cluster_id += len(result[0])
                                    del(tasks[i])
                                i -= 1
                        tasks.append(pool.map_async(_check_candidate_groups, (batch,)))
                        batch = []
                connection.commit()

            if len(batch) > 0:
                tasks.append(pool.map_async(_check_candidate_groups, (batch,)))
            for task in tasks:
                while not task.ready():
                    time.sleep(0)
                result = task.get()
                write_detected_duplicate_pairs(result, inner_cursor, next_cluster_id)
                next_cluster_id += len(result[0])
            connection.commit()

    return next_cluster_id


def _check_candidate_groups(batch):
    pairs = []
    for candidate_list in batch:
        for a in candidate_list:
            for b in candidate_list:
                if a != b and _is_close_enough(a, b):
                    pairs.append( (a,b) )
    return pairs


def write_detected_duplicate_pairs(result, inner_cursor, next_cluster_id):
    for pair in result[0]:
        inner_cursor.execute("""
        INSERT INTO cluster(cluster_id, converted_id) VALUES(?, ?);
        """, (next_cluster_id, pair[0]))
        inner_cursor.execute("""
        INSERT INTO cluster(cluster_id, converted_id) VALUES(?, ?);
        """, (next_cluster_id, pair[1]))
        next_cluster_id += 1


# Join any clusters that have one or more common publications.
def _join_overlapping_clusters(next_cluster_id):
    with get_connection() as connection:
        cursor = connection.cursor()
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

                #print(f"-----\nNow considering merging: {clusters}")

                cluster_a = clusters.pop()

                while len(clusters) > 0:
                    cluster_b = clusters.pop()

                    #print(f"  To be merged: {cluster_a} into {cluster_b}")

                    # Replace cluster_a and cluster_b with where ever their contents are now
                    while cluster_a in merged_into:
                        cluster_a = merged_into[cluster_a]
                    while cluster_b in merged_into:
                        cluster_b = merged_into[cluster_b]

                    #print(f"  After following history: {cluster_a} into {cluster_b}")

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

                    #print(f"Merged cluster {cluster_a} into {cluster_b}")

                    cluster_a = cluster_b

                #print("\n")

                connection.commit()
    
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
        connection.commit()

        # Add single member clusters for solitary publications (those that are not part of any other clusters)
        cursor.execute("""
        SELECT
            id
        FROM
            converted
        WHERE
            id NOT IN (
                SELECT DISTINCT
                    converted_id
                FROM
                    cluster
            )
            AND deleted = 0
        """)
        rows = cursor.fetchall() # This is necessary in order to allow modification of the table while iterating
        for solitary_row in rows:
            solitary_converted_id = solitary_row[0]
            inner_cursor = connection.cursor()
            inner_cursor.execute("""
            INSERT INTO cluster(cluster_id, converted_id) VALUES(?, ?);
            """, (next_cluster_id, solitary_converted_id))
            next_cluster_id += 1
        connection.commit()


def deduplicate():
    # The job of the "deduplication" is to correctly populate the "cluster"-table.
    # That table (the clusters) will then form the basis for the resulting swepub
    # records, which are merged manifestations of each cluster.
    next_cluster_id = _generate_clusters()
    _join_overlapping_clusters(next_cluster_id)

            
# For debugging
if __name__ == "__main__":
    deduplicate()
