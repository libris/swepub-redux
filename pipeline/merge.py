from audit import audit
from storage import commit_sqlite, get_cursor, open_existing_storage
from merger import PublicationMerger
from publication import Publication
from multiprocessing import Pool
import time
import json

def merge():
    # Set up batching
    batch = []
    tasks = []
    in_batch = 0

    with Pool(processes=16) as pool:

        # For each cluster, generate a union-record, containing as much information as possible
        # from the clusters elements.
        cursor = get_cursor()
        inner_cursor = get_cursor()
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
            batch.append(cluster_row)
            in_batch += 1

            if (len(batch) >= 64):
                while (len(tasks) >= 32):
                    time.sleep(0)
                    n = len(tasks)
                    i = n-1
                    while i > -1:
                        if tasks[i].ready():
                            #print("* CLEARING A PROCESS")
                            result = tasks[i].get()
                            write_results(result, inner_cursor)

                            del(tasks[i])
                        i -= 1
                tasks.append(pool.map_async(_handle, (batch,)))
                batch = []

        if len(batch) > 0:
            tasks.append(pool.map_async(_handle, (batch,)))
        for task in tasks:
            while not task.ready():
                time.sleep(0)
            result = task.get()
            write_results(result, inner_cursor)

def write_results(result, inner_cursor):
    for cluster in result[0]:
        cluster_id = cluster[0]
        merged_data = cluster[1]
        #print(f"really? {cluster_id} -> {isinstance(merged_data, str)} {merged_data} \n\n")
        inner_cursor.execute("""
        INSERT INTO finalized(cluster_id, data) VALUES(?, ?);
        """, (cluster_id, json.dumps(merged_data)))
    commit_sqlite()

def _handle(batch): # batch is a list of cluster rows
    results = []
    for cluster_row in batch:
        cluster_id = cluster_row[0]
        elements_json = cluster_row[1].split('\n')

        publications = []
        for element_json in elements_json:
            publications.append(Publication(json.loads(element_json)))

        merger = PublicationMerger()
        union_publication = merger.merge(publications)

        audit(union_publication.body)

        results.append( (cluster_id, union_publication.body) )
    return results


# For debugging
if __name__ == "__main__":
    open_existing_storage()
    merge()