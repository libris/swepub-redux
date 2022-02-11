from storage import *
from multiprocessing import Pool
from bibframesource import BibframeSource
import time
import json


def generate_search_tables():
    # Set up batching
    batch = []
    tasks = []

    with Pool(processes=16) as pool:
        with get_connection() as connection:
            cursor = connection.cursor()
            inner_cursor = connection.cursor()
            for cluster_row in cursor.execute("""
            SELECT
                finalized.id, finalized.cluster_id, finalized.data, group_concat(converted.source) AS sources
            FROM
                finalized
            LEFT JOIN
                cluster ON cluster.cluster_id=finalized.cluster_id
            LEFT JOIN
                converted ON converted.id=cluster.converted_id
            GROUP BY
                converted.source, finalized.id
            """):
                batch.append(cluster_row)

                if (len(batch) >= 64):
                    while (len(tasks) >= 32):
                        time.sleep(0)
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
                    time.sleep(0)
                result = task.get()
                write_results(result, inner_cursor, connection)


def write_results(result, inner_cursor, connection):
    for meta in result[0]:
        finalized_id = meta['finalized_id']
        inner_cursor.execute("""
        INSERT INTO search_single(
            finalized_id, year, content_marking, publication_status, swedish_list, open_access
        ) VALUES(
        ?, ?, ?, ?, ?, ?
        )
        """, (
        meta['finalized_id'],
        meta['publication_year'],
        meta['content_marking'],
        meta['publication_status'],
        meta['swedish_list'],
        meta['open_access']
        ))

        for doi in meta['doi']:
            inner_cursor.execute("INSERT INTO search_doi (finalized_id, value) VALUES (?, ?)", (finalized_id, doi))

        for gf in meta['genre_forms']:
            inner_cursor.execute("INSERT INTO search_genre_form (finalized_id, value) VALUES (?, ?)", (finalized_id, gf))

        for subject in meta['subjects']:
            inner_cursor.execute("INSERT INTO search_subject (finalized_id, value) VALUES (?, ?)", (finalized_id, subject))

        inner_cursor.execute("INSERT INTO search_fulltext (rowid, title, keywords) VALUES (?, ?, ?)", (
                    finalized_id,
                    meta['title'],
                    meta['keywords']
        ))

        for creator in meta['creators']:
            inner_cursor.execute("""
                INSERT INTO search_creator(
                finalized_id, orcid, family_name, given_name, local_id, local_id_by
                ) VALUES(
                ?, ?, ?, ?, ?, ?
                )
                """, (
                finalized_id,
                creator.get("ORCID", None),
                creator.get("familyName", None),
                creator.get("givenName", None),
                creator.get("localId", None),
                creator.get("localIdBy", None)
            ))

        for source in meta['sources']:
            inner_cursor.execute("INSERT INTO search_org (finalized_id, value) VALUES (?, ?)",
                                (finalized_id, source))

    connection.commit()


def _handle(batch): # batch is a list of finalized rows
    results = []
    for finalized_row in batch:
        finalized_id = finalized_row[0]
        cluster_id = finalized_row[1]
        doc = BibframeSource(json.loads(finalized_row[2]))
        sources = set(finalized_row[3].split(","))

        meta = {
            'finalized_id': finalized_id,
            'cluster_id': cluster_id,
            'publication_year': doc.publication_year,
            'content_marking': doc.content_marking,
            'publication_status': get_publication_status(doc),
            'swedish_list': doc.is_swedishlist,
            'open_access': doc.open_access,
            'doi': doc.DOI,
            'genre_forms': doc.output_types,
            'subjects': [],
            'title': doc.title,
            'keywords': " ".join(doc.keywords),
            'creators': [],
            'sources': sources
        }

        for subject in [item for sublist in doc.uka_subjects.values() for item in sublist]:
            meta['subjects'].append(subject)

        for creator in doc.creators:
            meta['creators'].append({
                'ORCID': creator.get("ORCID", None),
                'familyName': creator.get("familyName", None),
                'givenName': creator.get("givenName", None),
                'localId': creator.get("localId", None),
                'localIdBy': creator.get("localIdBy", None)
            })

        results.append(meta)
    return results


def get_publication_status(doc):
    ps = doc.publication_status
    if ps == "https://id.kb.se/term/swepub/Published":
        return "published"
    elif ps == "https://id.kb.se/term/swepub/EpubAheadOfPrintOnlineFirst":
        return "epub"
    elif ps in ["https://id.kb.se/term/swepub/Submitted",
                "https://id.kb.se/term/swepub/Accepted",
                "https://id.kb.se/term/swepub/InPress"]:
        return "submitted"
    return None


def is_swedish_list(pub):
    return "https://id.kb.se/term/swepub/swedishlist/peer-reviewed" in pub.genre_form


# For debugging
if __name__ == "__main__":
    open_existing_storage()
    generate_search_tables()
