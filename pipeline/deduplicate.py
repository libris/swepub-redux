import os
import json
import re

from storage import get_cursor, open_existing_storage

def deduplicate():
    cursor = get_cursor()
    for row in cursor.execute("""
    SELECT
        maintitle.maintitle, count(converted.oai_id)
    FROM
        maintitle
    LEFT JOIN
        converted ON maintitle.converted_id = converted.id
    GROUP BY
        maintitle.maintitle;
    """):
        print(row)

    # map from oai_id -> record, for all of swepub
    #records_by_id = {}

    # map words (found within each publications main title), to lists of oai_ids
    # of the records containing those words.
    #index = {}
    
    #for entry in os.scandir('./output/raw/'):
    #    if entry.is_file():
    #        with open(entry, "r") as f:
    #            for line in f.readlines():
    #                record = json.loads(line)

                    # The oai-id
    #                records_by_id[record["@id"]] = record

                    # For each word in the title
    #                for title in record["instanceOf"]["hasTitle"]:
    #                    for word in re.findall(r"\w+", title["mainTitle"]):
    #                        lowcaseword = str.lower(word)
    #                        if not lowcaseword in stopwords:
    #                            if not lowcaseword in index:
    #                                index[lowcaseword] = [] 
    #                            index[lowcaseword].append(record["@id"])

    #for oai_id, record in records_by_id.items():
    #    candidate_duplicates = [oai_id]

    #    for title in record["instanceOf"]["hasTitle"]:
    #        for word in re.findall(r"\w+", title["mainTitle"]):
    #            lowcaseword = str.lower(word)
    #            if not lowcaseword in stopwords:
    #                for candidate_id in index[lowcaseword]:
    #                    candidate_duplicates.append(candidate_id)

    #    if len(candidate_duplicates) > 1:
    #        print(f"check for dups: {len(candidate_duplicates)}")
                    

# TEMP
open_existing_storage()
deduplicate()
