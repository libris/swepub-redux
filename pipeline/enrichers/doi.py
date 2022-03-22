import unicodedata
import sys

from pipeline.util import update_at_path, make_event

# See DOI validator in validator service for more info on these.
INVALID_DOI_UNICODE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp", "Zs"}

# List containing unicode code points as integers.
INVALID_DOI_UNICODE = list(
    (
        ord(c)
        for c in (chr(i) for i in range(sys.maxunicode))
        if unicodedata.category(c) in INVALID_DOI_UNICODE_CATEGORIES
    )
)

TRANSLATE_DICT = {character: None for character in INVALID_DOI_UNICODE}

# Replace fraction slash with regular slash, as in UnicodeAsciiTranslator used in BaseEnricher.
TRANSLATE_DICT[ord("\u2044")] = ord("/")

DOI_START = "10."
VALID_STARTS = (DOI_START, "https://doi.org/10.", "http://doi.org/10.")


def recover_doi(body, field):
    doi = field.value
    path = field.path

    initial = doi
    translated = doi.translate(TRANSLATE_DICT)
    if translated != doi:
        doi = translated
        update_at_path(body, path, doi)
        field.events.append(
            make_event(
                event_type="enrichment",
                code="recovery",
                initial_value=initial,
                value=doi,
                result="enriched",
            )
        )
        field.value = doi
        field.enrichment_status = "enriched"

    if doi.startswith(VALID_STARTS):
        return
    else:
        hit = doi.find(DOI_START)
        if hit != -1:
            if field.enrichment_status == "enriched":
                initial = field.value
            update_at_path(body, path, doi[hit:])
            field.events.append(
                make_event(
                    event_type="enrichment",
                    code="recovery",
                    value=doi[hit:],
                    initial_value=initial,
                    result="enriched",
                )
            )
            field.value = doi[hit:]
            field.enrichment_status = "enriched"

    if field.enrichment_status != "enriched":
        field.enrichment_status = "unsuccessful"
