def make_mappings(data):
    return {
        term['code']: {
            'eng': term['prefLabelByLang']['en'],
            'swe': term['prefLabelByLang']['sv'],
            'broader': term['broader']['@id'].rsplit('/', 1)[-1]
            if 'broader' in term
            else None,
        }
        for term in data['@graph']
    }


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
