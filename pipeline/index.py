import re
import orjson as json

from pipeline.bibframesource import BibframeSource
from pipeline.storage import get_connection, checkpoint, SQL_SCHEMA_FILE

OUTPUT_TYPE_PREFIX = "https://id.kb.se/term/swepub/output/"
SEARCH_FIELDS = ["familyName", "givenName", "localId", "localIdBy", "ORCID", "classifications"]


def _search_table_indexes():
    with open(SQL_SCHEMA_FILE) as f:
        return re.findall(r"^CREATE INDEX (\w+) ON (search_\w+.*);$", f.read(), re.MULTILINE)

def generate_search_tables():
    with get_connection() as connection:
        cursor = connection.cursor()
        second_cursor = connection.cursor()
        third_cursor = connection.cursor()
        counter = 0
        limit = 25000

        # We have lots of indexes which makes insertion a lot slower, so we drop them now and recreate them afterwards.
        indexes = _search_table_indexes()
        for name, _ in indexes:
            cursor.execute(f"DROP INDEX IF EXISTS {name}")
        connection.commit()

        last_id = 0
        while True:
            # Necessary for WAL file not to grow too big
            connection.commit()
            checkpoint()
            rows_in_page = 0
            for row in second_cursor.execute("SELECT id, cluster_id, data FROM finalized WHERE id > ? ORDER BY id LIMIT ?", (last_id, limit),):
                rows_in_page += 1
                finalized_id = row[0]
                last_id = finalized_id
                cluster_id = row[1]
                doc = BibframeSource(json.loads(row[2]), SEARCH_FIELDS)

                third_cursor.execute(
                    """
                    INSERT INTO search_single(
                    finalized_id, year, content_marking, publication_status, swedish_list, open_access, autoclassified, doaj
                    ) VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        finalized_id,
                        doc.publication_just_the_year,
                        doc.content_marking,
                        get_publication_status(doc),
                        doc.is_swedishlist,
                        doc.open_access,
                        doc.autoclassified,
                        doc.DOAJ
                    ),
                )

                for doi in doc.DOI:
                    third_cursor.execute(
                        "INSERT INTO search_doi (finalized_id, value) VALUES (?, ?)",
                        (finalized_id, doi),
                    )

                for gf in doc.output_types:
                    if gf.startswith(OUTPUT_TYPE_PREFIX):
                        gf_shortened = gf[len(OUTPUT_TYPE_PREFIX) :]
                    else:
                        gf_shortened = gf
                    third_cursor.execute(
                        "INSERT INTO search_category (finalized_id, value) VALUES (?, ?)",
                        (finalized_id, gf_shortened),
                    )

                for subject in [item for sublist in doc.ssif_subjects.values() for item in sublist]:
                    third_cursor.execute(
                        "INSERT INTO search_subject (finalized_id, value) VALUES (?, ?)",
                        (finalized_id, subject),
                    )

                third_cursor.execute(
                    "INSERT INTO search_fulltext (finalized_id, title, keywords) VALUES (?, ?, ?)",
                    (finalized_id, doc.title, " ".join(doc.keywords)),
                )

                for creator in doc.creators:
                    third_cursor.execute(
                        """
                        INSERT INTO search_creator(
                        finalized_id, orcid, family_name, given_name, local_id, local_id_by
                        ) VALUES(
                        ?, ?, ?, ?, ?, ?
                        )
                        """,
                        (
                            finalized_id,
                            creator.get("ORCID", None),
                            creator.get("familyName", None),
                            creator.get("givenName", None),
                            creator.get("localId", None),
                            creator.get("localIdBy", None),
                        ),
                    )

                # Get org code from candidate/duplicate publications. No need to go through the actual documents,
                # because we've already put the code in the `converted` table.
                third_cursor.execute(
                    "SELECT co.source FROM converted co JOIN cluster cl ON co.id=cl.converted_id WHERE cl.cluster_id = ?",
                    (cluster_id,),
                )
                sources = third_cursor.fetchall()
                for source in set([item for sublist in sources for item in sublist]):
                    third_cursor.execute(
                        "INSERT INTO search_org (finalized_id, value) VALUES (?, ?)",
                        (finalized_id, source),
                    )
                counter += 1
                if counter % 5000 == 0:
                    connection.commit()
            if rows_in_page < limit:
                break
        connection.commit()

        for name, definition in indexes:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {definition}")
        connection.commit()


def get_publication_status(doc):
    ps = doc.publication_status
    if ps == "https://id.kb.se/term/swepub/Published":
        return "published"
    elif ps == "https://id.kb.se/term/swepub/EpubAheadOfPrintOnlineFirst":
        return "epub"
    elif ps in [
        "https://id.kb.se/term/swepub/Submitted",
        "https://id.kb.se/term/swepub/Accepted",
        "https://id.kb.se/term/swepub/InPress",
    ]:
        return "submitted"
    elif ps == "https://id.kb.se/term/swepub/Retracted":
        return "retracted"
    return None


def is_swedish_list(pub):
    return "https://id.kb.se/term/swepub/swedishlist/peer-reviewed" in pub.category


# For debugging
if __name__ == "__main__":
    generate_search_tables()
