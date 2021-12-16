import re
from stdnum.isbn import compact
from util import update_at_path
from log import log_for_OAI_id
#from .base_enricher import BaseEnricher

# flake8: noqa W504
isbn_regex = re.compile(
    '(?<![-./0-9])' +  # Check that not preceded by specific characters
    '(97[89][-]?)?' +  # Optional prefix for ISBN13
    '([0-9]+[-]?){3}' +  # Accept three middle fields with varying lengths
    '([0-9xX])' +  # Find control number
    '(?:(?![-0-9]))'  # Make sure the code isnt followed by a number or hyphen
)

def recover_isbn(isbn, body, path, id):
    answ = isbn_regex.finditer(isbn)
    res = []
    for pattern in answ:
        p = compact(pattern.group())
        #print(f"is this an ISBN ?? {p}  /  {pattern.group()}")    
        if len(p) == 10 or len(p) == 13:
            res.append(pattern.group())
    
    if not res:
        return
    
    if res[0] != isbn:
        update_at_path(body, path, res[0])
        log_for_OAI_id(id, 'ISBN enrichment: recovery')
        #field.update_value(
        #    new_value=res[0], code='recovery')

    for value in res[1:]:
        #update_at_path(body, path, "WOPWOP")
        log_for_OAI_id(id, '?? ISBN enrichment: split / Not sure what to do!')
        #actions.append(DuplicateFieldAction(
        #    code='split'.format(self.type), new=value, path=field.path, field_type=self.type
        #))
        #field.add_creation_event(old=old_value, new=value, code='split')
    