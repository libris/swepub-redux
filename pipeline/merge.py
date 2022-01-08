from audit import audit
from storage import commit_sqlite, get_cursor, open_existing_storage
from merger import PublicationMerger
from publication import Publication
import json

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

        publications = []
        for element_json in elements_json:
            publications.append(Publication(json.loads(element_json)))

        merger = PublicationMerger()
        union_publication = merger.merge(publications)

        audit(union_publication.body)

        # Write the now merged base element to storage
        inner_cursor = get_cursor()
        inner_cursor.execute("""
        INSERT INTO finalized(cluster_id, data) VALUES(?, ?);
        """, (cluster_id, json.dumps(union_publication.body)))
    commit_sqlite()

# For debugging
if __name__ == "__main__":
    open_existing_storage()
    merge()