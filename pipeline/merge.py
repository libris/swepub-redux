from audit import audit
from storage import commit_sqlite, get_cursor, open_existing_storage
from merger import PublicationMerger
from publication import Publication
from multiprocessing import Process, Queue
import time
import json

def merge():
    # Set up batching
    batch = []
    processes = []
    in_batch = 0
    queue = Queue()

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
            while (len(processes) >= 16):
                print("** WHAT?!")
                time.sleep(0)
                n = len(processes)
                i = n-1
                while i > -1:
                    if not processes[i].is_alive():
                        print("* CLEARING A PROCESS")
                        processes[i].join()
                        del processes[i]
                    i -= 1
            p = Process(target=handle, args=(batch, queue))
            p.start()
            processes.append( p )
            batch = []
        
        ##
        #while not queue.empty():
        print("Getting from Q!")
        try:
            (cluster_id, body) = queue.get(False)
            inner_cursor.execute("""
            INSERT INTO finalized(cluster_id, data) VALUES(?, ?);
            """, (cluster_id, json.dumps(body)))
        except Exception as e:
            pass
        print("  Getting from Q out!")
        ##

    p = Process(target=handle, args=(batch, queue))
    p.start()
    processes.append( p )

    ##
    #while not queue.empty():
    #    (cluster_id, body) = queue.get()
    #    inner_cursor.execute("""
    #    INSERT INTO finalized(cluster_id, data) VALUES(?, ?);
    #    """, (cluster_id, json.dumps(body)))
    ##
    for p in processes:
        p.join()
    
    commit_sqlite()

def handle(batch, queue): # batch is a list of cluster rows
    for cluster_row in batch:
        cluster_id = cluster_row[0]
        elements_json = cluster_row[1].split('\n')

        publications = []
        for element_json in elements_json:
            publications.append(Publication(json.loads(element_json)))

        merger = PublicationMerger()
        union_publication = merger.merge(publications)

        audit(union_publication.body)

        print("Putting into Q!")
        queue.put( (cluster_id, union_publication.body) )
        print("  Putting into Q out!")
    print("Batch done!")


# For debugging
if __name__ == "__main__":
    open_existing_storage()
    merge()