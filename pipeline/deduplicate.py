import time
from multiprocessing import Pool

import orjson as json

from pipeline.storage import get_connection
from pipeline.util import *

"""Max length in characters to compare text"""
MAX_LENGTH_STRING_TO_COMPARE = 1000

"""Match ratios for various pubications fields, see SequenceMatcher """
STRING_MATCH_RATIO_MAIN_TITLE = 0.9
STRING_MATCH_RATIO_SUB_TITLE = 0.9
STRING_MATCH_RATIO_SUMMARY = 0.9

STRING_MATCH_PARTOF_MAIN_TITLE = 0.8

CONFERENCE_PAPER_GENREFORM = "https://id.kb.se/term/swepub/ConferencePaper"

known_poor_titles = {"Introduction", "Inledning", "Indledning", "Editorial", "Förord", "Preface",
"Introduktion", "Review of", "Foreword", "Recensioner", "Conclusion", "Efterord", "Reply",
"Book review", "Recension", "Conclusions", "Review", "Erratum", "Commentary", "Guest editorial",
"Untitled", "Erratum to", "Editorial Introduction", "Avslutning", "Corrigendum", "Afterword",
"Response", "Correction to", "Re", "Epilogue", "Från redaktionen", "Kommentar", "Vorwort",
"Epilog", "Recension av", "Letter", "In memoriam", "Correction", "Debatt", "[Not Available]",
"Aktuellt", "Letter to the Editor", "recension", "Discussion", "Slutord", "Note", "Invited",
"Comment on"}

def _has_same_main_title(a, b):
    """True if publication has the same main title"""
    return compare_text(get_main_title(a), get_main_title(b), STRING_MATCH_RATIO_MAIN_TITLE)


def _has_same_sub_title(a, b):
    """True if publication has the same sub title"""
    return compare_text(get_sub_title(a), get_sub_title(b), STRING_MATCH_RATIO_SUB_TITLE)

# Exepects a string containing one _word_ as input
def is_numeral(a):
    if a == "":
        return False
    latin_numbers = "IVXLCDM0123456789" # Latin and arabic numbers
    for c in a:
        if c not in latin_numbers:
            return False
    return True

def _has_similar_combined_title(a, b):
    combined_a = get_combined_title(a)
    combined_b = get_combined_title(b)
    if combined_a in known_poor_titles or combined_b in known_poor_titles:
        return False
    similarity = get_common_substring_factor(combined_a, combined_b)

    if similarity > 0.7:
        #print(f"{combined_a}\n{combined_b}\n\t{similarity}")

        # If the very last word of a is a number, require the same number at the end of b.
        if " " in combined_a and " " in combined_b:
            undesired_chars = dict.fromkeys(map(ord, '-–.!?'), "")
            last_word_a = combined_a[(combined_a.rfind(" ")+1):].translate(undesired_chars).rstrip()
            last_word_b = combined_b[(combined_b.rfind(" ")+1):].translate(undesired_chars).rstrip()
            if is_numeral(last_word_a) or is_numeral(last_word_b):
                if (last_word_a != last_word_b):
                    return False
        return True
    return False

def _has_same_summary(a, b):
    """True if publication has the same summary"""
    return compare_text(get_summary(a), get_summary(b), STRING_MATCH_RATIO_SUMMARY)

def _has_similar_summary(a, b):
    summary_a = get_summary(a)
    summary_b = get_summary(b)
    if bool(summary_a) != bool(summary_b):
        return False
    if not summary_a:
        return True # Both a and b lack a summary? Guess they match then..
    similarity = get_common_substring_factor(summary_a, summary_b, 3)

    if similarity > 0.6:
        #print(f"{summary_a}\n{summary_b}\n\t{similarity}")
        return True
    return False


def _partof_has_same_main_title(partof_a, partof_b):
    """True if part_of has the same main title"""
    # partOf w/o main title should never match
    if part_of_main_title(partof_a) is None and part_of_main_title(partof_b) is None:
        return False
    return compare_text(
        part_of_main_title(partof_a), part_of_main_title(partof_b), STRING_MATCH_PARTOF_MAIN_TITLE
    )


def _has_similar_partof_main_title(a, b):
    part_a = part_of_with_title(a)
    part_b = part_of_with_title(b)
    if not part_a or not part_b:
        return False
    part_title_a = part_of_main_title(part_a)
    part_title_b = part_of_main_title(part_b)
    if not part_title_a or not part_title_b:
        return False
    
    similarity = get_common_substring_factor(part_title_a, part_title_b)
    if similarity > 0.5:
        #print(f"{part_title_a}\n{part_title_b}\n\t{similarity}")
        return True
    return False


def _has_same_partof_main_title(a, b):
    """Returns True if partOf has the same main title"""
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
        master_pub_date_str = master_pub_date_str[: len(candidate_pub_date_str)]
    elif len(master_pub_date_str) < len(candidate_pub_date_str):
        candidate_pub_date_str = candidate_pub_date_str[: len(master_pub_date_str)]
    return master_pub_date_str == candidate_pub_date_str


def _has_compatible_doi_set(a, b):
    l1 = get_identifiedby_ids(a, "DOI")
    l2 = get_identifiedby_ids(b, "DOI")

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
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
        SELECT
            data
        FROM
            converted
        WHERE
            rowid = ? OR rowid = ?;
        """,
            (a_rowid, b_rowid),
        )
        candidate_rows = cursor.fetchall()  # Will give exactly 2 rows, per definition
        a = json.loads(candidate_rows[0][0])
        b = json.loads(candidate_rows[1][0])

        # 'a' and 'b' may not have different DOIs.
        if not _has_compatible_doi_set(a, b):
            return False

        
        # A similar title and _one_ shared ID of some sort qualifies
        if _has_similar_combined_title(a, b) and has_same_ids(a, b):
            return True

        if (
            _has_similar_combined_title(a, b)
            #and CONFERENCE_PAPER_GENREFORM not in genre_form(a)
            #and CONFERENCE_PAPER_GENREFORM not in genre_form(b)
            and _has_similar_summary(a, b)
            and _has_same_publication_date(a, b)
            #and _has_same_genre_form(a, b)
        ):
            return True

        # 4.
        # if (
        #     _has_similar_combined_title(a, b)
        #     and (
        #         CONFERENCE_PAPER_GENREFORM in genre_form(a)
        #         or CONFERENCE_PAPER_GENREFORM in genre_form(b)
        #     )
        #     and _has_similar_summary(a, b)
        #     and _has_same_publication_date(a, b)
        #     and _has_similar_partof_main_title(a, b)
        # ):
        #     return True

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
            for candidatelist_row in cursor.execute(
                """
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
            """
            ):
                candidates = candidatelist_row[0].split("\n")
                if len(candidates) > 1 and len(candidates) < 150:
                    batch.append(candidates)

                    if len(batch) >= 32:
                        while len(tasks) >= 32:
                            time.sleep(1)
                            n = len(tasks)
                            i = n - 1
                            while i > -1:
                                if tasks[i].ready():
                                    result = tasks[i].get()
                                    write_detected_duplicate_pairs(
                                        result, inner_cursor, next_cluster_id
                                    )
                                    next_cluster_id += len(result[0])
                                    del tasks[i]
                                i -= 1
                        tasks.append(pool.map_async(_check_candidate_groups, (batch,)))
                        batch = []
                connection.commit()

            if len(batch) > 0:
                tasks.append(pool.map_async(_check_candidate_groups, (batch,)))
            for task in tasks:
                while not task.ready():
                    time.sleep(1)
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
                    pairs.append((a, b))
    return pairs


def write_detected_duplicate_pairs(result, inner_cursor, next_cluster_id):
    for pair in result[0]:
        inner_cursor.execute(
            """
        INSERT INTO cluster(cluster_id, converted_id) VALUES(?, ?);
        """,
            (next_cluster_id, pair[0]),
        )
        inner_cursor.execute(
            """
        INSERT INTO cluster(cluster_id, converted_id) VALUES(?, ?);
        """,
            (next_cluster_id, pair[1]),
        )
        next_cluster_id += 1


# Join any clusters that have one or more common publications.
def _join_overlapping_clusters(next_cluster_id):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
        SELECT
            count(cluster_id), group_concat(cluster_id, "\n")
        FROM
            cluster
        GROUP BY
            converted_id;
        """
        )
        # This is necessary in order to allow modification of the table while iterating:
        rows = cursor.fetchall()

        # Holds information on already merged clusters, so for example 1 -> 2 means cluster 1 no longer exists,
        # but it's publications are now in 2 instead.
        merged_into = {}

        for cluster_row in rows:
            cluster_count = cluster_row[0]
            if cluster_count > 1:
                clusters = cluster_row[1].split("\n")

                # print(f"-----\nNow considering merging: {clusters}")

                cluster_a = clusters.pop()

                while len(clusters) > 0:
                    cluster_b = clusters.pop()

                    # print(f"  To be merged: {cluster_a} into {cluster_b}")

                    # Replace cluster_a and cluster_b with where ever their contents are now
                    while cluster_a in merged_into:
                        cluster_a = merged_into[cluster_a]
                    while cluster_b in merged_into:
                        cluster_b = merged_into[cluster_b]

                    # print(f"  After following history: {cluster_a} into {cluster_b}")

                    if cluster_a == cluster_b:
                        continue

                    # Merge cluster_a into cluster_b
                    cursor.execute(
                        """
                    UPDATE
                        cluster
                    SET
                        cluster_id = ?
                    WHERE
                        cluster_id = ?;
                    """,
                        (cluster_b, cluster_a),
                    )
                    merged_into[cluster_a] = cluster_b

                    # print(f"Merged cluster {cluster_a} into {cluster_b}")

                    cluster_a = cluster_b

                # print("\n")

                connection.commit()

        # Given two clusters (A,B,C) and (B,C,D) which have now been joined, there will now be duplicate
        # rows for B and C. These must (should) be cleared:
        cursor.execute(
            """
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
        """
        )
        connection.commit()

        # Add single member clusters for solitary publications (those that are not part of any other clusters)
        cursor.execute(
            """
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
        """
        )
        # This is necessary in order to allow modification of the table while iterating:
        rows = cursor.fetchall()
        for solitary_row in rows:
            solitary_converted_id = solitary_row[0]
            inner_cursor = connection.cursor()
            inner_cursor.execute(
                """
            INSERT INTO cluster(cluster_id, converted_id) VALUES(?, ?);
            """,
                (next_cluster_id, solitary_converted_id),
            )
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
