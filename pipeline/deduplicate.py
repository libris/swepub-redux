import os
import json
import re

from storage import get_cursor, open_existing_storage

def deduplicate():
    cursor = get_cursor()
    for row in cursor.execute("""
    SELECT
        maintitle.maintitle, group_concat(converted.id)
    FROM
        maintitle
    LEFT JOIN
        converted ON maintitle.converted_id = converted.id
    GROUP BY
        maintitle.maintitle;
    """):
        print(row)                

# For debugging
if __name__ == "__main__":    
    open_existing_storage()
    deduplicate()
