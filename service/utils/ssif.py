def make_mappings(data):
    mappings = {}
    for term in data['@graph']:
        if term.get("owl:deprecated", "") == True or term.get("@type", "") != "Classification":
            continue

        if term.get("prefLabelByLang", {}).get("sv"):
            mappings[term["code"]] = {
                "eng": term["prefLabelByLang"]["en"],
                "swe": term["prefLabelByLang"]["sv"],
            }
            if "broader" in term:
                mappings[term["code"]]["broader"] = term['broader']['@id'].rsplit('/', 1)[-1]
            else:
                mappings[term["code"]]["broader"] = None
    return mappings


def build_tree_form(mappings):
    tree = {code: term.copy() for code, term in mappings.items()}

    for code, term in list(tree.items()):
        broader = term.get('broader')
        if broader:
            tree[broader].setdefault('subcategories', {})[code] = term

    for code in list(tree):
        if tree[code].pop('broader') is not None:
            del tree[code]

    return tree


def get_top_labels(tree):
    return {int(code): f"{code} {term['swe']}" for code, term in tree.items()}
