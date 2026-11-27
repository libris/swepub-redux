import json

from pipeline.libris import clean
from pipeline.util import SSIF_BASE


def _term(code, broader=None, **extra):
    term = {
        "@id": f"{SSIF_BASE}{code}",
        "@type": "Classification",
        "inScheme": {"@id": SSIF_BASE.rstrip("/")},
        "code": code,
        "prefLabelByLang": {"sv": f"sv {code}", "en": f"en {code}"},
        **extra,
    }
    if broader:
        term["broader"] = broader
    return term


def test_clean_replaces_ssif_definitions_with_links_for_all_levels():
    top = _term("1")
    mid = _term("106", broader=top)
    record = {
        "@context": "whatever",
        "instanceOf": {
            "classification": [
                _term("10616", broader=mid),
                _term("10615", broader=_term("106", broader=_term("1"))),
                _term("203", broader=_term("2"),
                      **{"@annotation": {"assigner": {"@id": "https://id.kb.se/generator/swepub-classifier"}}}),
                {"@type": "Classification", "code": "xyz", "prefLabel": "Not SSIF"},
            ]
        },
    }

    cleaned = json.loads(clean("oai:test:1", json.dumps(record)))

    assert "@context" not in cleaned
    assert cleaned["@id"] == "https://swepub.kb.se/bib/swepub:oai:test:1"
    assert cleaned["instanceOf"]["classification"] == [
        {"@id": f"{SSIF_BASE}10616"},
        {"@id": f"{SSIF_BASE}106"},
        {"@id": f"{SSIF_BASE}1"},
        {"@id": f"{SSIF_BASE}10615"},
        {"@id": f"{SSIF_BASE}203"},
        {"@id": f"{SSIF_BASE}2"},
        {"@type": "Classification", "code": "xyz", "prefLabel": "Not SSIF"},
    ]


def test_clean_without_classification():
    record = {"instanceOf": {"@type": "Text"}}
    cleaned = json.loads(clean("x", json.dumps(record)))
    assert "classification" not in cleaned["instanceOf"]
