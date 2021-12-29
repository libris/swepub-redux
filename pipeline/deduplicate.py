import os
import json
import re
import sqlite3
import random # TEMP!

from storage import commit_sqlite, get_cursor, open_existing_storage

# Are publications 'a' and 'b' similiar enough to justify clustering them?
# 'a' and 'b' are row IDs into the 'converted' table.
def _is_close_enough(a, b):
    return bool(random.getrandbits(1))

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

            # Pre-place the first candidate in a cluster of its own.
            clusters = [[0]] # A list of clusters, each cluster a list of record ids
            unclustered_indices = [*range(1, len(candidates))] # All but first

            while len(unclustered_indices) > 0:

                progress = False
        
                try:
                    for cluster in clusters:
                        for candidate_index in unclustered_indices:
                            for in_cluster_index in cluster:
                                if _is_close_enough(candidates[in_cluster_index], candidates[candidate_index]):
                                    cluster.append(candidate_index)
                                    unclustered_indices.remove(candidate_index)
                                    progress = True
                                    raise "Python bullshit" # Goto? break-to-label? Anything but this? Really Python...
                except Exception as e:
                    pass

                
                # If no more records could be placed in an existing cluster, create a new one
                if not progress:
                    clusters.append([unclustered_indices.pop()])

            print(json.dumps(clusters))

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
