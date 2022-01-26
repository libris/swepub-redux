import json                                                                                                                                                                             
from jsonpath_rw import jsonpath, parse

def update_at_path(root, path, new_value):
    basepath, key = path.rsplit('.', 1)
    found = parse(basepath).find(root)
    parent_object = found[0].value
    #print(f"Replacing {parent_object[key]} with {new_value} at {path}")
    parent_object[key] = new_value

class UnicodeAsciiTranslator:
    def __init__(self):
        pass

    def __getitem__(self, item):
        if item < 128:
            raise LookupError
        if item == ord(u'\u2044'):
            return '/'
        if item == ord(u'\u2013'):
            return '-'
        return None

def unicode_translate(input_string):
    return input_string.translate(UnicodeAsciiTranslator())

def make_event(type, field, path, code, result):
    return {"type": type, "field": field, "path": str(path), "code": code, "result" : result}