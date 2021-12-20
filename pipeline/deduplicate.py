import os

#from validate import PRECOMPILED_PATHS

#PATHS = 'instanceOf.hasTitle[*].mainTitle'

import itertools
from jsonpath_rw_ext import parse

def deduplicate():

    # Index oai_id and maintitle of every record in memory (swepub isn't large).
    # Essentially, this is a map of word (present within maintitle or oai_id)
    # to record. The record here is not the full record, but a file number and
    # line number where the record can be found.
    compiled_maintitle_path = parse('instanceOf.hasTitle[*].mainTitle')
    #compiled_maintitle_path = parse('instanceOf')
    #compiled_id_path = parse('@id') ??
    index = {}
    for entry in os.scandir('./output/raw/'):
        if entry.is_file():
            with open(entry, "r") as f:
                for line in f.readlines():
                    
                    #matches = itertools.chain.from_iterable(compiled_maintitle_path.find(line))
                    #for match in matches:
                    #    if match.value:
                    #        print(match.value)
                    print(compiled_maintitle_path.find(line))

# TEMP
deduplicate()