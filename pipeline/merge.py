from storage import *
from publicationmerger import PublicationMerger
from publication import Publication
from multiprocessing import Pool
import time
import orjson as json

def merge():
    # Set up batching
    batch = []
    tasks = []

    with Pool(processes=16) as pool:

        # For each cluster, generate a union-record, containing as much information as possible
        # from the clusters elements.
        with get_connection() as connection:
            cursor = connection.cursor()
            inner_cursor = connection.cursor()
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

                if (len(batch) >= 64):
                    while (len(tasks) >= 32):
                        time.sleep(1)
                        n = len(tasks)
                        i = n-1
                        while i > -1:
                            if tasks[i].ready():
                                result = tasks[i].get()
                                write_results(result, inner_cursor, connection)

                                del(tasks[i])
                            i -= 1
                    tasks.append(pool.map_async(_handle, (batch,)))
                    batch = []

            if len(batch) > 0:
                tasks.append(pool.map_async(_handle, (batch,)))
            for task in tasks:
                while not task.ready():
                    time.sleep(1)
                result = task.get()
                write_results(result, inner_cursor, connection)

def write_results(result, inner_cursor, connection):
    for cluster in result[0]:
        cluster_id = cluster[0]
        merged_data = cluster[1]
        inner_cursor.execute("""
        INSERT INTO finalized(cluster_id, oai_id, data) VALUES(?, ?, ?);
        """, (cluster_id, merged_data['@id'], json.dumps(merged_data)))
    connection.commit()

def _handle(batch): # batch is a list of cluster rows
    results = []
    for cluster_row in batch:
        cluster_id = cluster_row[0]
        elements_json = cluster_row[1].split('\n')

        publications = []
        for element_json in elements_json:
            publications.append(Publication(json.loads(element_json)))

        merger = PublicationMerger()
        union_publication, publication_ids, publication_orgs = merger.merge(publications)

        union_publication.body['_publication_ids'] = publication_ids
        union_publication.body['_publication_orgs'] = publication_orgs

        results.append( (cluster_id, union_publication.body ) )
    return results


# For debugging
if __name__ == "__main__":
    merge()