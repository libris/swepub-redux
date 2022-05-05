from aenum import Enum

from difflib import SequenceMatcher
from jsonpath_rw import parse
import re
import Levenshtein


class Validation(Enum):
    INVALID = 0
    VALID = 1
    PENDING = 2

    def __str__(self):
        return self.name.lower()

    def __int__(self):
        return self.value


class Enrichment(Enum):
    UNCHANGED = 0
    ENRICHED = 1
    UNSUCCESSFUL = 2

    def __str__(self):
        return self.name.lower()

    def __int__(self):
        return self.value


class Normalization(Enum):
    UNCHANGED = 0
    NORMALIZED = 1

    def __str__(self):
        return self.name.lower()

    def __int__(self):
        return self.value


class Level(Enum):
    _init_ = 'value string'

    NONE = None, ""
    NONPEERREVIEWED = 0, "https://id.kb.se/term/swepub/swedishlist/non-peer-reviewed"
    PEERREVIEWED = 1, "https://id.kb.se/term/swepub/swedishlist/peer-reviewed"

    def __int__(self):
        return self.value

    def __str__(self):
        return self.string


class FieldMeta:
    def __init__(self, path="", id_type="", value=None, validation_status=Validation.PENDING, normalization_status=Normalization.UNCHANGED, enrichment_status=Enrichment.UNCHANGED):
        self.id_type = id_type
        self.path = path
        self.initial_value = value
        self.value = value
        self.validation_status = validation_status
        self.enrichment_status = enrichment_status
        self.normalization_status = normalization_status
        self.events = []

    def is_enriched(self):
        return self.enrichment_status == Enrichment.ENRICHED


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def update_at_path(root, path, new_value):
    base_path, key = path.rsplit('.', 1)
    found = parse(base_path).find(root)
    parent_object = found[0].value
    #print(f"Replacing {parent_object[key]} with {new_value} at {path}")
    parent_object[key] = new_value

# Remove the value at path and clear any (now) empty containing structures for that value.
# _additionally_ clean min_prune_levels above it (even it they're not empty).
def remove_at_path(root, path, min_prune_level):
    _steps = path.split('.')
    steps = []
    stack = []
    current = root
    for step in _steps:
        if '[' in step:
            steps.append(int(step[1:-1]))
        else:
            steps.append(step)
    #print (f"steps: {steps}")

    for step in steps:
        stack.append(current)
        #print (f"*   Will now access {step} of {current}:")
        current = current[step]
    
    current = stack.pop()
    key = steps.pop()
    del current[key]

    prune_level = 0
    while stack:
        current = stack.pop()
        key = steps.pop()

        #print(f" * now considering deleting key {key} from obj: {current} if it is empty")
        if prune_level < min_prune_level or len(current[key]) == 0:
            #print(f"   now deleting key {key} from obj: {current}")
            del current[key]
        prune_level += 1

def add_sibling_at_path(root, path, type, value):
    base_path, _, _ = path.rsplit('.', 2)
    found = parse(base_path).find(root)
    found[0].value.append({"@type": type, "value": value})
    # Figure out and return the path for the new sibling (surely there is a better
    # way to do this...)
    return f"{base_path}.[{len(found[0].value) - 1}].value"


def get_at_path(root, path):
    if path == "":
        return root
    return parse(path).find(root)[0].value

# This is a heuristic, not an exact algorithm.
# The idea is to first find the longest substring (loosely defined) shared between both a and b.
# What is returned, a float within (0.0, 1.0), is then the length of that substring
# (in words) divided by the length of the longest input string (in words).
# Further: Words need not match exactly, a "short" edit distance is considered enough to match.
# Further yet: Starting in the "middle" and working your way out in search of a shared string
# is "cheating" in the sense the longest shared string might actually be in the beginning of
# a and the end of b, which we will then miss. However: This does not matter _to us_ because
# we are only interested in matchings that are more than a 50% match, and a shared substring
# _cannot_ exceed 50% of the original string without also overlapping in the middle. This makes
# the middle-out search "ok". And doing it this way is dramatically faster than traditional
# shared substring algorithms.
undesired_chars = dict.fromkeys(map(ord, '-–_,.;:’\'!?”“#\u00a0'), " ")
def get_common_substring_factor(a, b, allowed_misses = 0):
    a = a.translate(undesired_chars).lower()
    b = b.translate(undesired_chars).lower()

    # Turn strings into word lists
    a = re.findall(r"\w+", a)
    b = re.findall(r"\w+", b)

    # Make sure a is the shorter list
    if len(a) > len(b):
        tmp = b
        b = a
        a = tmp

    # Find the middlemost unique word of 'a' that also exists in 'b' (start_word)
    already_found = set()
    not_suitable = set()
    for word in a:
        if word in already_found or word not in b:
            not_suitable.add(word)
        else:
            already_found.add(word)
    a_filtered = [x for x in a if x not in not_suitable]
    if len(a_filtered) == 0: # Could not find a common word to start on
        return 0.0
    af_index = len(a_filtered) // 2
    start_word = a_filtered[af_index]

    # Find the index of start_word in a and b
    start_index_a = a.index(start_word)
    start_index_b = b.index(start_word)

    # Count substring length from start_word, backwards and forwards
    count = 1 # start_word itself is part of the shared substring and counts as 1
    
    # Check backwards
    ia = 0
    ib = 0
    misses = 0
    while start_index_a + ia > 0 and start_index_b + ib > 0: # Don't move beyond beginning of list
        ia -= 1
        ib -= 1
        if Levenshtein.distance(a[start_index_a + ia], b[start_index_b + ib]) < 4:
            count += 1
        # The two elif cases are here to counter words that are "särstavade", basically
        # try again with the next word added to the previous one
        elif start_index_a + ia > 0 and Levenshtein.distance(a[start_index_a + ia - 1] + a[start_index_a + ia], b[start_index_b + ib]) < 4:
            count += 1
            ia -= 1
        elif start_index_b + ib > 0 and Levenshtein.distance(a[start_index_a + ia], b[start_index_b + ib - 1] + b[start_index_b + ib]) < 4:
            count += 2 # We're eating two words out of B which is what we'll divide by in a second
            ib -= 1
        else:
            if misses > allowed_misses:
                break
            misses += 1
            ia -= 1

    # Check forwards
    ia = 0
    ib = 0
    misses = 0
    while start_index_a + ia < len(a)-1 and start_index_b + ib < len(b)-1: # Don't move beyond end of list
        ia += 1
        ib += 1
        if Levenshtein.distance(a[start_index_a + ia], b[start_index_b + ib]) < 4:
            count += 1
        # The two elif cases are here to counter words that are "särstavade", basically
        # try again with the next word added to the previous one
        elif start_index_a + ia < len(a) - 2 and Levenshtein.distance(a[start_index_a + ia] + a[start_index_a + ia + 1], b[start_index_b + ib]) < 4:
            count += 1
            ia += 1
        elif start_index_b + ib < len(b) - 2 and Levenshtein.distance(a[start_index_a + ia], b[start_index_b + ib] + b[start_index_b + ib + 1]) < 4:
            count += 2 # We're eating two words out of B which is what we'll divide by in a second
            ib += 1
        else:
            if misses > allowed_misses:
                break
            misses += 1
            ia -= 1
    
    return count / len(b)


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


def make_event(event_type=None, code=None, result=None, initial_value=None, value=None):
    result = {
        "type": event_type,
        "code": code,
        "result": result,
        "initial_value": initial_value,
        "value": value
    }

    return {k: v for k, v in result.items() if v is not None}


def make_audit_event(event_type=None, code=None, result=None, initial_value=None, value=None, name=None):
    return {
        "type": event_type,
        "code": code,
        "result": result,
        "initial_value": initial_value,
        "value": value,
        "name": name
    }


def split_title_subtitle_first_colon(title):
    try:
        parts = title.split(':', 1)
        maintitle = parts[0]
        subtitle = None
        if len(parts) == 2:
            subtitle = parts[1]
            subtitle = subtitle.strip()
        return maintitle, subtitle
    except AttributeError:
        return title, None


def empty_string(s):
    if s and isinstance(s, str):
        if not s.strip():
            return True
        else:
            return False
    return True


def compare_text(master_text, candidate_text, match_ratio, max_length_string_to_compare=1000):
    if empty_string(master_text) and empty_string(candidate_text):
        return True
    if empty_string(master_text) or empty_string(candidate_text):
        return False
    master_text = master_text[0:max_length_string_to_compare]
    candidate_text = candidate_text[0:max_length_string_to_compare]
    master_text = master_text.lower()
    candidate_text = candidate_text.lower()
    sequence_matcher = SequenceMatcher(a=master_text,
                                       b=candidate_text)
    sequence_matcher_ratio = sequence_matcher.quick_ratio()
    return sequence_matcher_ratio >= match_ratio

def get_combined_title(body):
    """Return the main title with and subtitle appended."""
    has_title_array = body.get('instanceOf', {}).get('hasTitle', [])
    for h_t in has_title_array:
        if isinstance(h_t, dict) and h_t.get('@type') == 'Title':
            main_title = h_t.get('mainTitle')
            sub_title = h_t.get('subtitle')
            combined = ""
            if not empty_string(main_title):
                combined = main_title
            if not empty_string(sub_title):
                combined += " " + sub_title
            return combined
    return ""

def get_main_title(body):
    """Return value of instanceOf.hasTitle[?(@.@type=="Title")].mainTitle if it exists and
    there is no subtitle.
    If a subtitle exist then the return value is split at the first colon and the first string
    is returned,
    i.e 'main:sub' returns main.
    None otherwise """
    has_title_array = body.get('instanceOf', {}).get('hasTitle', [])
    main_title_raw = None
    sub_title_raw = None
    for h_t in has_title_array:
        if isinstance(h_t, dict) and h_t.get('@type') == 'Title':
            main_title_raw = h_t.get('mainTitle')
            sub_title_raw = h_t.get('subtitle')
            break
    if not empty_string(sub_title_raw):
        return main_title_raw
    main_title, sub_title = split_title_subtitle_first_colon(main_title_raw)
    if not empty_string(main_title):
        return main_title
    else:
        return None


def get_sub_title(body):
    """Return value for instanceOf.hasTitle[?(@.@type=="Title")].subtitle if it exists,
    if it does not exist then the value of instanceOf.hasTitle[?(@.@type=="Title")].mainTitle
    is split at the first colon and the second string is returned, i.e 'main:sub' returns sub.
    None otherwise """
    sub_title_array = body.get('instanceOf', {}).get('hasTitle', [])
    main_title_raw = None
    for h_t in sub_title_array:
        if isinstance(h_t, dict) and h_t.get('@type') == 'Title' and h_t.get('subtitle'):
            return h_t.get('subtitle')
        else:
            main_title_raw = h_t.get('mainTitle')
            break
    main_title, sub_title = split_title_subtitle_first_colon(main_title_raw)
    if not empty_string(sub_title):
        return sub_title
    else:
        return None


def get_part_of(body):
    """ Return array of PartOf objects from partOf """
    part_of = []
    part_of_json_array = body.get('partOf', [])
    if part_of_json_array is not None:
        for p in part_of_json_array:
            if isinstance(p, dict):
                part_of.append(p)
    return part_of


def part_of_with_title(body):
    """ Return partOf object that has @type Title, None otherwise"""
    _part_of_with_title = [p for p in get_part_of(body) if part_of_main_title(p)]
    if len(_part_of_with_title) > 0:
        return _part_of_with_title[0]
    else:
        return None


def part_of_main_title(body):
    """Return value for hasTitle[?(@.@type=="Title")].mainTitle, None if not exist """
    main_title_array = body.get('hasTitle', [])
    for m_t in main_title_array:
        if isinstance(m_t, dict) and m_t.get('@type') == 'Title':
            return m_t.get('mainTitle')
    return None


def genre_form(body):
    """ Return array of values from instanceOf.genreForm.[*].@id """
    genre_forms = []
    genre_form_array = body.get('instanceOf', {}).get('genreForm', [])
    for g_f in genre_form_array:
        if isinstance(g_f, dict):
            genre_forms.append(g_f.get('@id'))
    return [gf for gf in genre_forms if gf]


def get_ids(body, path, id_type):
    if id_type:
        ids = []
        ids_array = body.get(path, [])
        for identifier in ids_array:
            if isinstance(identifier, dict) and identifier.get('@type') == id_type:
                ids.append(identifier.get('value'))
        return [identifier for identifier in ids if identifier]
    else:
        if body.get(path):
            return body[path]
    return []


def get_identifiedby_ids(body, identifier=''):
    """Return either identifiedBy ids values if identifier is set otherwise whole identifiedBy array """
    return get_ids(body, 'identifiedBy', identifier)


def get_indirectly_identifiedby_ids(body, identifier=''):
    """Return either indirectlyIdentifiedBy ids values if identifier is set
    otherwise whole indirectlyIdentifiedBy array """
    return get_ids(body, 'indirectlyIdentifiedBy', identifier)


def same_ids(master_ids, candidate_ids):
    if len(master_ids) == 0 or len(candidate_ids) == 0:
        return False
    return set(master_ids) == set(candidate_ids)


def has_same_ids(a, b):
    """ True if one of ids DOI, PMID, ISI, ScopusID and ISBN are the same for identifiedBy
    or if ISBN id are the same for indirectlyIdentifiedBy"""
    if same_ids(get_identifiedby_ids(a, 'DOI'), get_identifiedby_ids(b, 'DOI')):
        return True
    if same_ids(get_identifiedby_ids(a, 'PMID'), get_identifiedby_ids(b, 'PMID')):
        return True
    if same_ids(get_identifiedby_ids(a, 'ISI'), get_identifiedby_ids(b, 'ISI')):
        return True
    if same_ids(clean_scopus_ids(get_identifiedby_ids(a, 'ScopusID')), clean_scopus_ids(get_identifiedby_ids(b, 'ScopusID'))):
        return True
    if same_ids(get_identifiedby_ids(a, 'ISBN'), get_identifiedby_ids(b, 'ISBN')):
        return True
    if same_ids(get_indirectly_identifiedby_ids(a, 'ISBN'), get_indirectly_identifiedby_ids(b, 'ISBN')):
        return True
    return False


# Special handling to clean ScopusID, because we don't (yet) validate/enrich it.
# A Scopus ID seems to be 10 or 11 digits. A Scopus _EID_ seems to be the prefix
# "2-s2.0-" followed by the Scopus ID. For purposes of comparison, this function
# removes the prefix.
def clean_scopus_ids(scopus_ids):
    prefix = "2-s2.0-"
    return [s[len(prefix):] if s.startswith(prefix) else s for s in scopus_ids]


def get_summary(body):
    """ Return value for instanceOf.summary[?(@.@type=="Summary")].label if it exists, None otherwise"""
    summary_array = body.get('instanceOf', {}).get('summary', [])
    for s in summary_array:
        if isinstance(s, dict) and s.get('@type') == 'Summary':
            return s.get('label')
    return None


def get_publication_information(body):
    """ Return first occurrence of PublicationInformation from publication field"""
    for p in body.get('publication', []):
        if isinstance(p, dict) and p.get('@type') == 'Publication':
            return p
    return None


def get_publication_date(body):
    """ Return value for publication[?(@.@type=="Publication")].date if it exists, None otherwise"""
    pub_info = get_publication_information(body)
    if pub_info:
        return pub_info.get("date")
    return None


def get_language(body):
    """ Return value for instanceOf.summary[?(@.@type=="Summary")].label if it exists, None otherwise"""
    language_array = body.get('instanceOf', {}).get('language', [])
    for l in language_array:
        if isinstance(l, dict) and l.get('@type') == 'Language':
            return l.get('code')
    return None
