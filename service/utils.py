def parse_dates(from_date, to_date):
    if from_date == '':
        from_date = None
    if to_date == '':
        to_date = None
    # we require either both dates or no dates
    if from_date is None and to_date is None:
        return [], from_date, to_date
    if from_date and not to_date:
        return ["Missing parameter: 'to'"], None, None
    if to_date and not from_date:
        return ["Missing parameter: 'from'"], None, None
    errors = []
    try:
        if from_date is not None:
            from_date = int(from_date)
    except ValueError:
        errors.append(f"Invalid value for 'from' parameter: {from_date}")
    try:
        if to_date is not None:
            to_date = int(to_date)
    except ValueError:
        errors.append(f"Invalid value for 'to' parameter: {to_date}")
    if errors:
        return errors, None, None
    if to_date < from_date:
        errors.append("'to' cannot be before 'from'")

    return errors, from_date, to_date


def sort_mappings(unsorted):
    """Create a tree given a dict
    We expect the dict to contain keys of length 1, 3, or 5. These lengths
    correspond to different levels in the tree. A longer key must have a
    shorter key as "parent".
    """
    sorted_subjects = {}
    # We iterate over the keys sorted by first prefix and then length
    # `1` comes first, `101` comes before `10101`, which comes before `2`
    for k in sorted(unsorted.keys(), key=lambda k: len(k)):
        v = unsorted[k]
        if len(k) == 1:
            if k not in sorted_subjects:
                sorted_subjects[k] = v
        elif len(k) == 3:
            assert k[:1] in sorted_subjects
            if 'subcategories' not in sorted_subjects[k[:1]]:
                sorted_subjects[k[:1]]['subcategories'] = {}
            sorted_subjects[k[:1]]['subcategories'][k] = v
        elif len(k) == 5:
            assert k[:1] in sorted_subjects
            # `subcategories` key should have been added in the previous case
            assert 'subcategories' in sorted_subjects[k[:1]]
            assert k[:3] in sorted_subjects[k[:1]]['subcategories']
            if 'subcategories' not in sorted_subjects[k[:1]]['subcategories'][k[:3]]:
                sorted_subjects[k[:1]]['subcategories'][k[:3]]['subcategories'] = {}
            sorted_subjects[k[:1]]['subcategories'][k[:3]]['subcategories'][k] = v
    return sorted_subjects


def get_source_org_mapping(oai_sources):
    mapping = {}
    for source in oai_sources:
        mapping[source['code']] = source['name']
    return mapping