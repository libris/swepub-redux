from difflib import SequenceMatcher

from jsonpath_rw import parse


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def update_at_path(root, path, new_value):
    basepath, key = path.rsplit('.', 1)
    found = parse(basepath).find(root)
    parent_object = found[0].value
    #print(f"Replacing {parent_object[key]} with {new_value} at {path}")
    parent_object[key] = new_value


def get_at_path(root, path):
    if path == "":
        return root
    return parse(path).find(root)[0].value


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


def make_event(type=None, code=None, result=None, initial_value=None, value=None):
    result = {
        "type": type,
        "code": code,
        "result": result,
        "initial_value": initial_value,
        "value": value
    }

    return {k: v for k, v in result.items() if v is not None}


def make_audit_event(type=None, code=None, result=None, initial_value=None, value=None, name=None):
    return {
        "type": type,
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
    part_of_with_title = [p for p in get_part_of(body) if part_of_main_title(p)]
    if len(part_of_with_title) > 0:
        return part_of_with_title[0]
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


def get_ids(body, path, type):
    if type:
        ids = []
        ids_array = body.get(path, [])
        for id in ids_array:
            if isinstance(id, dict) and id.get('@type') == type:
                ids.append(id.get('value'))
        return [id for id in ids if id]
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
    if same_ids(get_identifiedby_ids(a, 'ScopusID'), get_identifiedby_ids(b, 'ScopusID')):
        return True
    if same_ids(get_identifiedby_ids(a, 'ISBN'), get_identifiedby_ids(b, 'ISBN')):
        return True
    if same_ids(get_indirectly_identifiedby_ids(a, 'ISBN'), get_indirectly_identifiedby_ids(b, 'ISBN')):
        return True
    return False


def get_summary(body):
    """ Return value for instanceOf.summary[?(@.@type=="Summary")].label if exist, None otherwise """
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
    """ Return value for publication[?(@.@type=="Publication")].date if exist, None otherwise """
    pub_info = get_publication_information(body)
    if pub_info:
        return pub_info.get("date")
    return None
