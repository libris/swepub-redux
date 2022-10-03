# Quick script for dumping records to tsv, adjust as necessary
import sys
from os import path

import orjson
import cld3

from pipeline.storage import get_connection, dict_factory
from pipeline.publication import Publication

FILE_PATH = path.dirname(path.abspath(__file__))
DEFAULT_SWEPUB_DB = path.join(FILE_PATH, "../swepub.sqlite3")


def dump_tsv(target_language="en", number_of_records=10000, min_level=1, max_level=5):
    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        for row in cur.execute(f"SELECT data FROM finalized LIMIT {int(number_of_records)}", []):
            if row.get("data"):
                finalized = orjson.loads(row["data"])
                publication = Publication(finalized)

                # Skip records with no 3 or 5 level classification
                #if not publication.is_classified(skip_autoclassified=True):
                #   continue

                title = publication.main_title or ""
                if publication.sub_title:
                    title = f"{title} {publication.sub_title}"
                title = title.strip()
                #pub_ids = ";".join(finalized["_publication_ids"])
                #org_ids = ";".join(list(set(finalized["_publication_orgs"])))
                summary = (publication.summary or "")[:5000].strip()
                # Remove suspiciously short abstracts (e.g. "N/A", "[no abstract]", ...)
                if len(summary) < 30:
                    summary = ""
                #language = publication.language or ""

                ukas = list(filter(lambda x: len(x) >= int(min_level) and len(x) <= int(max_level), publication.ukas(skip_autoclassified=True)))
                # Skip records with no classification
                if not ukas:
                    continue

                # If record has a subject like "305", ensure it also has "3"
                expanded_ukas = set(ukas)
                for uka in ukas:
                    if len(uka) == 3:
                        expanded_ukas.add(uka[:1])
                    if len(uka) == 5:
                        expanded_ukas.add(uka[:1])
                        expanded_ukas.add(uka[:3])

                ukas_str = " ".join([f"<https://id.kb.se/term/uka/{s}>" for s in expanded_ukas])

                if target_language == "en":
                    language_id = "https://id.kb.se/language/eng"
                elif target_language == "sv":
                    language_id = "https://id.kb.se/language/swe"

                # Get non-UKA keywords in the target language
                keywords = " ".join(publication.keywords(language=language_id))

                title_and_summary = f"{title} {summary}"

                #print(publication.subjects)

                # Skip records with title not in target language
                language_prediction_title = cld3.get_language(title_and_summary)
                if not language_prediction_title or language_prediction_title.language != target_language or not language_prediction_title.is_reliable:
                    continue

                # Skip records with abstract not in target language
                language_prediction_abstract = cld3.get_language(title_and_summary)
                if not language_prediction_abstract or language_prediction_abstract.language != target_language or not language_prediction_abstract.is_reliable:
                    continue

                string_to_use = f"{title_and_summary} {keywords}"

                print(f"{string_to_use.strip()}\t{ukas_str}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Specify language code (en or sv), number of records, and min and max classification level, e.g. en 10000 1 3")
        sys.exit(1)
    dump_tsv(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
