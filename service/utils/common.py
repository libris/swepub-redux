from collections.abc import Iterable
from enum import Enum
from urllib.parse import urlparse

# https://stackoverflow.com/a/3300514
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def flatten(possibly_nested_list):
    for el in possibly_nested_list:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def get_percentage(count, total):
    if total > 0:
        percentage = round(count / total * 100, 2)
    else:
        percentage = 0.0
    return percentage


class Comparator(Enum):
    match = " MATCH "


def parse_dates(from_date, to_date):
    if from_date == "":
        from_date = None
    if to_date == "":
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


def parse_limit_and_offset(limit, offset):
    """Get limit and offset from query args."""
    errors = []
    if limit is None and offset is not None:
        errors.append(f"Parameter 'offset' must be used together with 'limit'")
    if limit is not None:
        try:
            limit = int(limit)
            if limit < 0:
                errors.append(f"Parameter 'limit' must be non-negative")
        except ValueError:
            errors.append(f"Invalid value for 'limit' parameter: {limit}")
            limit = None
    if offset is not None:
        try:
            offset = int(offset)
            if offset < 0:
                errors.append(f"Parameter 'offset' must be non-negative")
        except ValueError:
            errors.append(f"Invalid value for 'offset' parameter: {offset}")
            offset = None
    return errors, limit, offset


def get_source_org_mapping(oai_sources):
    mapping = {}
    for source in oai_sources:
        mapping[source["code"]] = source["name"]
    return mapping


def export_options(request):
    export_as_csv = False
    csv_mimetype = "text/csv"
    tsv_mimetype = "text/tab-separated-values"
    export_mimetype = csv_mimetype
    csv_flavor = "csv"
    accept = request.headers.get("accept")
    if accept and accept == csv_mimetype:
        export_as_csv = True
    elif accept and accept == tsv_mimetype:
        export_as_csv = True
        csv_flavor = "tsv"
        export_mimetype = tsv_mimetype
    else:
        export_mimetype = "application/json"
    return export_as_csv, export_mimetype, csv_flavor


def get_base_url(request):
    proto = request.headers.get("X-Forwarded-Proto")
    host = request.headers.get("X-Forwarded-Host")
    port = request.headers.get("X-Forwarded-Port")
    path = request.path

    if not proto and not host and not port:
        parsed_from_request = urlparse(request.base_url)
        proto = parsed_from_request.scheme
        host = parsed_from_request.hostname
        port = str(parsed_from_request.port)
    netloc = f"{host}:{port}"

    if proto == "http" and port != 80:
        return f"{proto}://{host}:{port}", (proto, host, port, path, netloc)
    if proto == "https" and port != 443:
        netloc = host
    return f"{proto}://{host}", (proto, host, port, path, netloc)


def unescape_match(match_obj):
    escape_sequence = match_obj.group(0)
    digits = escape_sequence[2:]
    ordinal = int(digits, 16)
    char = chr(ordinal)
    return char
