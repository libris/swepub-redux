from storage import commit_sqlite, get_cursor, open_existing_storage
import json

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
            pass
            #master = self._merge_contribution(master, candidate)
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