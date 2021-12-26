import os
import json
import re
import random # TEMP!

from storage import get_cursor, open_existing_storage

# Are publications 'a' and 'b' similiar enough to justify clustering them?
def _is_close_enough(a, b):
    return bool(random.getrandbits(1))

def deduplicate():
    cursor = get_cursor()
    # Note that unescaped \n is illegal within json, therefore
    # splitting on it is safe to do.
    for candidatelist_row in cursor.execute("""
    SELECT
        group_concat(converted.data, "\n")
    FROM
        maintitle
    LEFT JOIN
        converted ON maintitle.converted_id = converted.id
    GROUP BY
        maintitle.maintitle;
    """):
        candidates = candidatelist_row[0].split('\n')
        if len(candidates) > 1:
            #print(json.dumps(candidates))

            # Pre-place the first candidate in a cluster of its own.
            clusters = [[0]] # A list of clusters, each cluster a list of records
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

            #inner_cursor = get_cursor()
            #inner_cursor.execute("SELECT data FROM converted LIMIT 1;")
            

# For debugging
if __name__ == "__main__":    
    open_existing_storage()
    deduplicate()
