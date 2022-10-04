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

        count = 0
        for row in cur.execute(f"SELECT data FROM finalized", []):
            if row.get("data"):
                finalized = orjson.loads(row["data"])
                publication = Publication(finalized)

                # Some records have summaries (abstracts) tagged with a language, most (?)
                # do not. First try to get a language-specific summary. If that fails, try to
                # get the untagged one.
                summary = ""
                if target_language == "en":
                    summary = publication.get_english_summary()
                if target_language == "sv":
                    summary = publication.get_swedish_summary()

                if not summary:
                    summary = publication.summary or ""

                summary = (summary or "")[:5000].strip()
                # Remove suspiciously short abstracts (e.g. "N/A", "[no abstract]", ...)
                if len(summary) < 50:
                    summary = ""

                title = publication.main_title or ""
                if publication.sub_title:
                    title = f"{title} {publication.sub_title}"
                title = title.strip()

                # Remove summary if summary not in target language. We check all summaries
                # (even the language-tagged ones) because we don't trust input.
                language_prediction_summary = cld3.get_language(summary)
                if not language_prediction_summary or language_prediction_summary.language != target_language or not language_prediction_summary.is_reliable:
                    summary = ""

                # Skip records with no 3 or 5 level classification
                #if not publication.is_classified(skip_autoclassified=True):
                #   continue

                # Remove title if title not in target language
                language_prediction_title = cld3.get_language(title)
                if not language_prediction_title or language_prediction_title.language != target_language or not language_prediction_title.is_reliable:
                    title = ""

                # If we don't have a good summary nor a good title, skip the record
                if len(summary) < 50 and len(title) < 40:
                    continue

                ukas = list(filter(lambda x: len(x) >= int(min_level) and len(x) <= int(max_level), publication.ukas(skip_autoclassified=True)))
                # Skip records with no classification
                if not ukas:
                    continue

                # E.g. if record has a subject like "305", ensure it also has "3"
                expanded_ukas = set(ukas)
                for uka in ukas:
                    if len(uka) == 3:
                        expanded_ukas.add(uka[:1])
                    if len(uka) == 5:
                        expanded_ukas.add(uka[:1])
                        expanded_ukas.add(uka[:3])
                ukas_str = " ".join([f"<https://id.kb.se/term/uka/{s}>" for s in expanded_ukas])

                # Get non-UKA keywords in the target language
                if target_language == "en":
                    language_id = "https://id.kb.se/language/eng"
                elif target_language == "sv":
                    language_id = "https://id.kb.se/language/swe"
                keywords = " ".join(publication.keywords(language=language_id))

                print(f"{title} {summary} {keywords}\t{ukas_str}")
                count += 1
                if count >= int(number_of_records):
                    break


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Specify language code (en or sv), number of records, and min and max classification level, e.g. en 10000 1 3")
        sys.exit(1)
    dump_tsv(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
