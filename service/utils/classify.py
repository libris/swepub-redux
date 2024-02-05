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
        "@type": "Classification",
        "@id": f"https://id.kb.se/term/ssif/{code}",
        "inScheme": {"@id": "https://id.kb.se/term/ssif"},
        "code": code,
        "prefLabelByLang": {lang: categories.get(code, {}).get(lang)},
        "_topic_tree": [
            categories.get(code[:x], {}).get(lang) for x in category_level[len(code)]
        ],
    }
