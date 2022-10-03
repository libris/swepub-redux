import os
import sys
from pathlib import Path
import json

import cld3

from pipeline.convert import convert
from pipeline.modsstylesheet import ModsStylesheet
from pipeline.publication import Publication

XML_PATH="./_xml"
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
SOURCE_FILE = os.path.join(FILE_PATH, "../resources/sources.json")


#def eligible_for_autoclassification(publication):
#    # 1. Publication year >= 2012. 2010 According to some? Old swepub uses 2012
#    if publication.year is None or int(publication.year) < 2012:  
#        return False
#    # 2. Swe/eng abstract (with a length that's not suspiciously small)
#    summary = publication.get_english_summary() or publication.get_swedish_summary()
#    if not summary or len(summary) < 30:
#        return False
#    # 3. Publication status == (Published || None)
#    if (
#        publication.publication_status is not None
#        and publication.publication_status != "https://id.kb.se/term/swepub/Published"
#    ):
#        return False
#    # 4. No 3-level/5-level classification
#    if publication.is_classified:
#        return False
#    return True


def eligible_for_training(publication):
    # 0. Publication with no title
    title = publication.title or ""
    if not title.strip():
        return False

    # 1. Publication year >= 2012. 2010 According to some? Old swepub uses 2012
    if publication.year is None or int(publication.year) < 2012:  
        return False
    # 2. Swe/eng abstract (with a length that's not suspiciously small)
    summary = publication.get_english_summary() or publication.get_swedish_summary() or ""
    if not summary or len(summary) < 30:
        return False
    # 3. Publication status == (Published || None)
    if (
        publication.publication_status is not None
        and publication.publication_status != "https://id.kb.se/term/swepub/Published"
    ):
        return False
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit()
    target_language = sys.argv[1]

    sources = json.load(open(SOURCE_FILE))

    for directory in [directory for directory in Path(XML_PATH).glob("*") if directory.is_dir()]:
        code = directory.name
        url = sources[code]["sets"][0]["url"]
        stylesheet = ModsStylesheet(code, url)

        for file_path in [file_path for file_path in directory.glob("*.xml") if file_path.is_file()]:
            with open(file_path, "r") as f:
                transformed_xml = stylesheet.apply(f.read())
                converted = convert(transformed_xml)
                publication = Publication(converted)

                if publication.year is None or int(publication.year) < 2012:  
                    continue

                title = publication.main_title or ""
                if publication.sub_title:
                    title = f"{title} {publication.sub_title}"
                title = title.strip()
                summary = publication.summary or ""
                summary = summary[:5000].strip()

                if not eligible_for_training(publication):
                    continue

                # Skip records with very short "abstracts" as these abstracts are typically useless
                # (e.g., "n/a", "Not available", ..)
                #if len(summary) < 30:
                #    continue

                ukas = publication.ukas()
                if not ukas:
                    continue
                expanded_ukas = set(ukas)

                for uka in ukas:
                    if len(uka) == 3:
                        expanded_ukas.add(uka[:1])
                    if len(uka) == 5:
                        expanded_ukas.add(uka[:3])
                        expanded_ukas.add(uka[:1])

                ukas_str = " ".join([f"<https://id.kb.se/term/uka/{s}>" for s in expanded_ukas])

                # Skip records with title not in target language
                language_prediction_title = cld3.get_language(title)
                if language_prediction_title.language != target_language or not language_prediction_title.is_reliable:
                    continue

                # Skip records with abstract not in target language
                language_prediction_abstract = cld3.get_language(summary)
                if language_prediction_abstract.language != target_language or not language_prediction_abstract.is_reliable:
                    continue

                # Get non-UKA keywords in the target language
                if target_language == "en":
                    language_id = "https://id.kb.se/language/eng"
                elif target_language == "sv":
                    language_id = "https://id.kb.se/language/swe"
                keywords = " ".join(publication.keywords(language=language_id))

                title_and_summary = f"{title} {summary}"
                string_to_use = f"{title_and_summary} {keywords}"
                print(f"{string_to_use.strip()}\t{ukas_str}")
