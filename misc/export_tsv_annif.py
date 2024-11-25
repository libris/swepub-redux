import sys

import orjson
from simplemma.langdetect import lang_detector

from pipeline.storage import get_connection, dict_factory
from pipeline.publication import Publication
from pipeline.util import get_title_by_language, get_summary_by_language, SSIF_BASE


def dump_tsv(target_language="en", number_of_records=10000, min_level=1, max_level=5):
    limit_sql = ""
    if int(number_of_records) > 0:
        limit_sql = f"LIMIT {int(number_of_records)}"

    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        count = 0
        # We could do ORDER BY RANDOM() but it'd be very slow. Instead, for production,
        # dump everything (number_of_records = 0) with create_tsv_sets.sh, which will
        # run `shuf` after everything has been written. Then you can just get whatever
        # number of lines you need.
        for row in cur.execute(f"SELECT data FROM converted {limit_sql}", []):
            if row.get("data"):
                finalized = orjson.loads(row["data"])
                publication = Publication(finalized)

                # Get SSIF codes, filtered by min/max level, and skip records with
                # no classification in the desired levels. For example, with
                # min_level 3 max_level 5, records with only 1-level classification
                # would be skipped.
                ssifs = list(
                    filter(
                        lambda x: len(x) >= int(min_level) and len(x) <= int(max_level),
                        publication.ssifs(skip_autoclassified=True),
                    )
                )
                # Skip records with no classification
                if not ssifs:
                    continue

                title = get_title_by_language(publication, target_language)

                # Some records have summaries (abstracts) tagged with a language, most (?)
                # do not. First try to get a language-specific summary. If that fails, try to
                # get the untagged one.
                summary = get_summary_by_language(publication, target_language)

                if not summary:
                    summary = publication.summary or ""

                summary = " ".join((summary or "")[:5000].split()).strip()
                # Remove suspiciously short abstracts (e.g. "N/A", "[no abstract]", ...)
                if len(summary) < 50:
                    summary = ""

                # Remove summary if summary not in target language. We check all summaries
                # (even the language-tagged ones) because we don't trust input.
                predicted_lang, lang_score = lang_detector(summary, lang=("sv", "en"))[0]
                if (
                    predicted_lang != target_language
                    or lang_score < 0.5
                ):
                    summary = ""

                # If we don't have a good summary nor a good title, skip the record
                if len(summary) < 50 and len(title) < 40:
                    continue

                # E.g. if record has a subject like "305", ensure it also has "3"
                expanded_ssif = set(ssifs)
                for ssif in ssifs:
                    if len(ssif) == 3:
                        expanded_ssif.add(ssif[:1])
                    if len(ssif) == 5:
                        expanded_ssif.add(ssif[:1])
                        expanded_ssif.add(ssif[:3])
                ssif_str = " ".join(
                    [f"<{SSIF_BASE}{s}>" for s in expanded_ssif]
                )

                # Get non-SSIF keywords in the target language
                if target_language == "en":
                    language_id = "https://id.kb.se/language/eng"
                elif target_language == "sv":
                    language_id = "https://id.kb.se/language/swe"
                keywords = " ".join(publication.keywords(langtag=language_id))

                print(f"{title} {summary} {keywords}\t{ssif_str}")
                count += 1
                if count >= int(number_of_records) and int(number_of_records) > 0:
                    break


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Specify language code (en or sv), number of records, and min and max classification level, e.g. en 10000 1 3"
        )
        sys.exit(1)
    dump_tsv(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
