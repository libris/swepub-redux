import json                                                                                                                                                                             
from jsonpath_rw import jsonpath, parse

def update_at_path(root, path, new_value):
    basepath, key = path.rsplit('.', 1)
    found = parse(basepath).find(root)
    parent_object = found[0].value
    parent_object[key] = new_value
    #print(f"found {parent_object} after which {key} might give us the value?")