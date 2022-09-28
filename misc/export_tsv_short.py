# Quick script for dumping records to tsv, adjust as necessary
import sys
from os import path

import orjson
import cld3

from pipeline.storage import get_connection, dict_factory
from pipeline.publication import Publication

FILE_PATH = path.dirname(path.abspath(__file__))
DEFAULT_SWEPUB_DB = path.join(FILE_PATH, "../swepub.sqlite3")


def dump_tsv(target_language="en", number_of_records=10000, max_level=3):
    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        for row in cur.execute(f"SELECT data FROM finalized LIMIT {int(number_of_records)}", []):
            if row.get("data"):
                finalized = orjson.loads(row["data"])
                publication = Publication(finalized)

                title = publication.main_title or ""
                if publication.sub_title:
                    title = f"{title}: {publication.sub_title}"
                title = title.strip()
                #pub_ids = ";".join(finalized["_publication_ids"])
                #org_ids = ";".join(list(set(finalized["_publication_orgs"])))
                summary = publication.summary or ""
                summary = summary.strip()
                language = publication.language or ""

                ukas = list(filter(lambda x: len(x) <= int(max_level), publication.ukas(skip_autoclassified=True)))

                # Skip records with no classification
                if not ukas:
                    continue
                ukas_str = " ".join([f"<https://id.kb.se/term/uka/{s}>" for s in ukas])

                # Skip records with no abstract
                if not summary:
                    continue

                # Skip records with very short "abstracts" as these abstracts are typically useless
                # (e.g., "n/a", "Not available", ..)
                if len(summary) < 30:
                    continue

                # Skip records with abstract not in target language
                language_prediction = cld3.get_language(summary)
                if language_prediction.language != target_language or not language_prediction.is_reliable:
                    continue

                print(f"{summary.strip()}\t{ukas_str}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Specify language code (en or sv), number of records, and max classification level, e.g. en 10000 3")
        sys.exit(1)
    dump_tsv(sys.argv[1], sys.argv[2], sys.argv[3])
