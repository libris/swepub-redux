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
