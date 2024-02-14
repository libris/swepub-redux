import json
from pathlib import Path

ID = '@id'
ANNOTATION = '@annotation'

LD_CACHE_FILES = [
    Path(__file__).parent / "../resources/ssif.jsonld",
]

_item_map = {}

for ldfile in LD_CACHE_FILES:
    with ldfile.open() as f:
        for item in json.load(f)['@graph']:
                _item_map[item[ID]] = item


def get_description(id):
    return _item_map.get(id)


def embellish(item, relations=["broader"]):
    if not isinstance(item, dict) or ID not in item:
        return item

    return _embellish(_item_map, item, relations)


def _embellish(item_map, item, relations):
    described = item_map.get(item.get(ID))
    if not described:
        return item

    embellished = described.copy()

    for rel in relations:
        if rel in embellished:
            value = embellished[rel]
            if isinstance(value, list):
                embellished[rel] = [_embellish(v) for v in values]
            elif isinstance(value, dict):
                embellished[rel] = _embellish(item_map, value, relations)

    annot = item.get(ANNOTATION)
    if annot:
        embellished[ANNOTATION] = annot

    return embellished


if __name__ == '__main__':
    import sys

    for arg in sys.argv[1:]:
        print(json.dumps(embellish({ID: arg}), indent=2, ensure_ascii=False))
