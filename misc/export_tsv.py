# Quick script for dumping records to tsv, adjust as necessary

from os import path

import orjson

from pipeline.storage import get_connection, dict_factory
from pipeline.publication import Publication

FILE_PATH = path.dirname(path.abspath(__file__))
DEFAULT_SWEPUB_DB = path.join(FILE_PATH, "../swepub.sqlite3")


def dump_tsv():
    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        print(f"publication_ids\ttitle\tabstract\tlanguage\torganization_ids\tuka_codes")
        for row in cur.execute(f"SELECT data FROM finalized", []):
            if row.get("data"):
                finalized = orjson.loads(row["data"])
                publication = Publication(finalized)

                title = publication.main_title
                if publication.sub_title:
                    title = f"{title}: {publication.sub_title}"
                pub_ids = ";".join(finalized["_publication_ids"])
                org_ids = ";".join(list(set(finalized["_publication_orgs"])))
                summary = publication.summary or ""
                language = publication.language or ""
                ukas = ";".join(publication.ukas())
                print(f"{pub_ids}\t{title}\t{summary}\t{language}\t{org_ids}\t{ukas}")


if __name__ == "__main__":
    dump_tsv()
