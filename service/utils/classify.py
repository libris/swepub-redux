def enrich_subject(subjects, categories):
    ret = []
    for code, score in subjects:
        r = {
            "score": score,
            "swe": create_subject(code, "swe", categories),
            "eng": create_subject(code, "eng", categories),
        }
        ret += [r]
    return ret


def create_subject(code, lang, categories):
    category_level = {1: (1,), 3: (1, 3), 5: (1, 3, 5)}

    return {
        "@type": "Topic",
        "@id": "https://id.kb.se/term/uka/{}".format(code),
        "inScheme": {
            "@id": "https://id.kb.se/term/uka/",
            "@type": "ConceptScheme",
            "code": "uka.se",
        },
        "code": code,
        "prefLabel": categories.get(code, {}).get(lang),
        "language": {
            "@type": "Language",
            "@id": f"https://id.kb.se/language/{lang}",
            "code": lang,
        },
        "_topic_tree": [
            categories.get(code[:x], {}).get(lang) for x in category_level[len(code)]
        ],
    }
