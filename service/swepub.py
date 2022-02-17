#!/usr/bin/env python3
import json
from os import path

from utils import bibliometrics
from utils.common import *
from utils.process import *
from utils.process_csv import export as process_csv_export
from utils.bibliometrics_csv import export as bibliometrics_csv_export
from utils.classify import enrich_subject

from datetime import datetime
from pathlib import Path
import sqlite3
from flask import Flask, g, request, jsonify, Response, stream_with_context, url_for, make_response
from pypika import Query, Tables, Parameter, Table, Criterion, Order
from pypika.terms import BasicCriterion
from pypika import functions as fn
from collections import Counter

# Database in parent directory of swepub.py directory
DATABASE = str(Path.joinpath(Path(__file__).resolve().parents[1], 'swepub.sqlite3'))

SSIF_LABELS = {
    1: "1 Naturvetenskap",
    2: "2 Teknik",
    3: "3 Medicin och hälsovetenskap",
    4: "4 Lantbruksvetenskap och veterinärmedicin",
    5: "5 Samhällsvetenskap",
    6: "6 Humaniora och konst"
}

INFO_API_MAPPINGS = sort_mappings(json.load(open(path.join(path.dirname(path.abspath(__file__)), '../resources/ssif_research_subjects.json'))))
INFO_API_OUTPUT_TYPES = json.load(open(path.join(path.dirname(path.abspath(__file__)), '../resources/output_types.json')))
INFO_API_SOURCE_ORG_MAPPING = json.load(open(path.join(path.dirname(path.abspath(__file__)), '../resources/sources.json')))
CATEGORIES = json.load(open(path.join(path.dirname(path.abspath(__file__)), '../resources/categories.json')))

# Note: static files should be served by Apache/nginx
app = Flask(__name__, static_url_path='/app', static_folder='vue-client/dist')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def _errors(errors, status_code=400):
    resp = {
        'errors': errors,
        'status_code': status_code
    }
    return jsonify(resp), status_code


# Catchall routes - the Vue app handles all non-API routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return app.send_static_file("index.html")


# ██████╗ ██╗██████╗ ██╗     ██╗ ██████╗ ███╗   ███╗███████╗████████╗██████╗ ██╗ ██████╗███████╗
# ██╔══██╗██║██╔══██╗██║     ██║██╔═══██╗████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝██╔════╝
# ██████╔╝██║██████╔╝██║     ██║██║   ██║██╔████╔██║█████╗     ██║   ██████╔╝██║██║     ███████╗
# ██╔══██╗██║██╔══██╗██║     ██║██║   ██║██║╚██╔╝██║██╔══╝     ██║   ██╔══██╗██║██║     ╚════██║
# ██████╔╝██║██████╔╝███████╗██║╚██████╔╝██║ ╚═╝ ██║███████╗   ██║   ██║  ██║██║╚██████╗███████║
# ╚═════╝ ╚═╝╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝

@app.route("/api/v1/bibliometrics", methods=['POST'], strict_slashes=False)
def bibliometrics_api():
    if request.content_type != 'application/json':
        return _errors(errors=['Content-Type must be "application/json"'])

    export_as_csv = False
    csv_mimetype = 'text/csv'
    tsv_mimetype = 'text/tab-separated-values'
    export_mimetype = csv_mimetype
    csv_flavor = 'csv'
    accept = request.headers.get('accept')
    if accept and accept == csv_mimetype:
        export_as_csv = True
    elif accept and accept == tsv_mimetype:
        export_as_csv = True
        csv_flavor = 'tsv'
        export_mimetype = tsv_mimetype
    else:
        export_mimetype = 'application/json'

    query_data = request.json
    try:
        limit = query_data.get('limit')
        if limit:
            limit = int(limit)

        doi = query_data.get("DOI")
        genre_form = [gf.strip() for gf in query_data.get("genreForm", []) if len(gf.strip()) > 0]
        orgs = [o.strip() for o in query_data.get("org", []) if len(o.strip()) > 0]
        title = query_data.get("title", "").replace(",", " ")
        keywords = query_data.get("keywords", "").replace(",", " ")

        subjects = query_data.get("subject", [])
        if isinstance(subjects, str):
            subjects = subjects.split(',')
        subjects = [s.strip() for s in subjects if len(s.strip()) > 0]

        from_yr = query_data.get("years", {}).get("from")
        to_yr = query_data.get("years", {}).get("to")
        errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
        if errors:
            return _errors(errors)

        content_marking = [cm.strip() for cm in query_data.get("contentMarking", []) if len(cm.strip()) > 0]
        if len(content_marking) > 0:
            if not (all(cm in ("ref", "vet", "pop") for cm in content_marking)):
                return _errors(errors=[f"Invalid value for content marking."], status_code=400)

        publication_status = [ps.strip() for ps in query_data.get("publicationStatus", []) if len(ps.strip()) > 0]
        if len(publication_status) > 0:
            if not all(ps in ("published", "epub", "submitted") for ps in publication_status):
                return _errors(errors=[f"Invalid value for publication status."], status_code=400)

        swedish_list = query_data.get("swedishList")
        open_access = query_data.get("openAccess")

        orcid = query_data.get("creator", {}).get("ORCID")
        given_name = query_data.get("creator", {}).get("givenName")
        family_name = query_data.get("creator", {}).get("familyName")
        person_local_id = query_data.get("creator", {}).get("localId")
        person_local_id_by = query_data.get("creator", {}).get("localIdBy")

    except (AttributeError, ValueError, TypeError):
        return _errors(errors=[f"Invalid value for json body query parameter/s."], status_code=400)

    finalized, search_single, search_creator, search_fulltext, search_doi, search_genre_form, search_subject, search_org = Tables('finalized', 'search_single', 'search_creator', 'search_fulltext', 'search_doi', 'search_genre_form', 'search_subject', 'search_org')
    q = Query.from_(finalized)#.select('data')
    values = []

    if from_yr and to_yr:
        q = q.where((search_single.year >= Parameter('?')) & (search_single.year <= Parameter('?')))
        values.append([from_yr, to_yr])
    if swedish_list:
        q = q.where(search_single.swedish_list == 1)
    if open_access:
        q = q.where(search_single.open_access == 1)
    for k, v in {'content_marking': content_marking, 'publication_status': publication_status}.items():
        if v:
            q = q.where(search_single['k'].isin([Parameter(', '.join(['?'] * len(v)))]))
            values.append(content_marking)
    if any([(from_yr and to_yr), content_marking, publication_status, swedish_list, open_access]):
        q = q.join(search_single).on(finalized.id == search_single.finalized_id)

    for k, v in {'orcid': orcid, 'given_name': given_name, 'family_name': family_name, 'person_local_id': person_local_id, 'person_local_id_by': person_local_id_by}.items():
        if v:
            q = q.where(search_creator[k] == Parameter('?'))
            values.append(v)
    if any([orcid, given_name, family_name, person_local_id, person_local_id_by]):
        q = q.join(search_creator).on(finalized.id == search_creator.finalized_id)

    for k, v in {'title': title, 'keywords': keywords}.items():
        if v:
            q = q.where(BasicCriterion(Comparator.match, search_fulltext[k], search_fulltext[k].wrap_constant(Parameter('?'))))
            values.append(v)
    if any([title, keywords]):
        q = q.join(search_fulltext).on(finalized.id == search_fulltext.finalized_id)

    for param in [(search_doi, doi), (search_genre_form, genre_form), (search_subject, subjects), (search_org, orgs)]:
        if param[1]:
            if isinstance(param[1], list):
                q = q.where(param[0].value.isin([Parameter(', '.join(['?'] * len(param[1])))]))
            else:
                q = q.where(param[0].value == Parameter('?'))
            q = q.join(param[0]).on(finalized.id == param[0].finalized_id)
            values.append(param[1])

    q_total = q.select(fn.Count('*').as_("total"))
    q = q.select('data')
    if limit:
        q = q.limit(limit)

    cur = get_db().cursor()
    cur.row_factory = dict_factory
    total_docs = cur.execute(str(q_total), list(flatten(values))).fetchone()['total']
    fields = query_data.get("fields", [])
    if fields is None:
        fields = []
    handled_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    # Results are streamed to the client so we're not bothered by limits
    def get_results():
        if export_as_csv:
            yield f"# Swepub bibliometric export. Query handled at {handled_at}. Query parameters: {request.args.to_dict()}\n"
        else:
            yield(
                f'{{"hits": ['
            )

        total = 0
        for row in cur.execute(str(q), list(flatten(values))):
            (result, errors) = bibliometrics.build_result(row, fields)
            if export_as_csv:
                yield(bibliometrics_csv_export(result, fields, csv_flavor, total))
            else:
                maybe_comma = ',' if total > 0 else ''
                yield(maybe_comma + json.dumps(result))
            total += 1

        if not export_as_csv:
            yield('],')
            if from_yr and to_yr:
                yield(f'"from": {from_yr},')
                yield(f'"to": {to_yr},')
            yield(
                f'"query": {json.dumps(query_data)},'
                f'"query_handled_at": "{handled_at}",'
                f'"total": {total_docs}'
                '}'
            )

    return app.response_class(stream_with_context(get_results()), mimetype=export_mimetype)


@app.route("/api/v1/bibliometrics/publications/<record_id>", methods=['GET'])
def bibliometrics_get_record(record_id):
    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM finalized WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        return _errors(["Not Found"], status_code=404)
    doc = json.loads(row[0])
    # TODO: Don't store the following in the actual document
    doc.pop('_publication_ids', None)
    doc.pop('_publication_orgs', None)
    return doc


#  ██████╗██╗      █████╗ ███████╗███████╗██╗███████╗██╗   ██╗
# ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
# ██║     ██║     ███████║███████╗███████╗██║█████╗   ╚████╔╝ 
# ██║     ██║     ██╔══██║╚════██║╚════██║██║██╔══╝    ╚██╔╝  
# ╚██████╗███████╗██║  ██║███████║███████║██║██║        ██║   
#  ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝        ╚═╝   

@app.route("/api/v1/classify", methods=['POST'])
def classify():
    if request.content_type != 'application/json':
        return _errors('Content-Type must be "application/json"')

    data = request.json
    abstract = data.get('abstract', '')
    classes = data.get('classes', 5)
    level = data.get('level', 3)
    title = data.get('title', '')
    keywords = data.get('keywords', '')

    try:
        classes = int(classes)
        level = int(level)
    except ValueError:
        return _errors("Parameters 'classes' and 'level' must be integers")
    if level not in [1, 3, 5]:
        return _errors("Parameter 'level' must be either 1, 3 or 5")
    if classes < 1:
        return _errors("Parameter 'classes' must be larger than 0")

    # NOTE! From here on the code is copied/adapted from pipeline's autoclassify.

    # Extract individual words
    words_set = set()
    for string in [abstract, title, keywords]:
        words = re.findall(r'\w+', string)
        for word in words:
            if word.isnumeric():
                continue
            words_set.add(word.lower())
    words = list(words_set)[0:150]

    # Out of the extracted words, determine which are the rarest ones
    cur = get_db().cursor()
    cur.row_factory = lambda cursor, row: row[0]
    rare_words = cur.execute(f"""
        SELECT
            word
        FROM
            abstract_total_word_counts
        WHERE
            word IN ({','.join('?'*len(words))})
        ORDER BY
            occurrences ASC
        LIMIT
            6
    """, words).fetchall()

    # Find publications sharing those rare words
    subjects = Counter()
    publication_subjects = set()

    cur.row_factory = dict_factory
    for candidate_row in cur.execute(f"""
        SELECT
            converted.id, converted.data, group_concat(abstract_rarest_words.word, '\n') AS rarest_words
        FROM
            abstract_rarest_words
        LEFT JOIN
            converted
        ON
            converted.id = abstract_rarest_words.converted_id
        WHERE
            abstract_rarest_words.word IN ({','.join('?'*len(rare_words))})
        GROUP BY
            abstract_rarest_words.converted_id
        """, rare_words):

        candidate_rowid = candidate_row["id"]
        candidate = json.loads(candidate_row["data"])
        candidate_matched_words = []
        if isinstance(candidate_row["rarest_words"], str):
            candidate_matched_words = candidate_row["rarest_words"].split("\n")

        # This is a vital tweaking point. How many _rare_ words do two abstracts need to share
        # in order to be considered on the same subject? 2 seems a balanced choice. 1 "works" too,
        # but may be a bit too aggressive (providing a bit too many false positive matches).
        if len(candidate_matched_words) < 1:
            continue

        for subject in candidate.get("instanceOf", {}).get("subject", []):
            try:
                authority, subject_id = subject['inScheme']['code'], subject['code']
            except KeyError:
                continue
            if authority not in ('hsv', 'uka.se') or len(subject_id) < level:
                continue

            publication_subjects.add(subject_id[:level])
        score = len(candidate_matched_words)
        for sub in publication_subjects:
            subjects[sub] += score

    subjects = subjects.most_common(classes)
    status = "match" if len(subjects) > 0 else "no match"

    return {
        "abstract": abstract,
        "status": status,
        "suggestions": enrich_subject(subjects, CATEGORIES)
    }


# ██████╗  █████╗ ████████╗ █████╗ ███████╗████████╗ █████╗ ████████╗██╗   ██╗███████╗
# ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██║   ██║██╔════╝
# ██║  ██║███████║   ██║   ███████║███████╗   ██║   ███████║   ██║   ██║   ██║███████╗
# ██║  ██║██╔══██║   ██║   ██╔══██║╚════██║   ██║   ██╔══██║   ██║   ██║   ██║╚════██║
# ██████╔╝██║  ██║   ██║   ██║  ██║███████║   ██║   ██║  ██║   ██║   ╚██████╔╝███████║
# ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝

@app.route("/api/v1/datastatus", methods=['GET'])
def datastatus():
    return datastatus_source(source=None)


@app.route("/api/v1/datastatus/<source>", methods=['GET'])
def datastatus_source(source):
    from_yr = request.args.get("from")
    to_yr = request.args.get("to")
    errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
    if errors:
        return _errors(errors)
    if source and source not in INFO_API_SOURCE_ORG_MAPPING:
        return _errors(['Source not found'], status_code=404)

    converted = Table('converted')
    values = []
    result = {}

    q_total = Query \
        .select(fn.Count('*').as_('total_docs')) \
        .from_(converted)
    q_oa = Query \
        .select(fn.Count('*').as_('oa')) \
        .from_(converted) \
        .where(converted.is_open_access == 1)
    q_ssif = Query \
        .select(fn.Count('*').as_('ssif')) \
        .from_(converted) \
        .where(converted.ssif_1 > 0)
    q_swedishlist = Query \
        .select(fn.Count('*').as_('swedishlist')) \
        .from_(converted) \
        .where(converted.classification_level == 1)
    q_total_per_source = Query \
        .select(converted.source, fn.Count('*').as_('total')) \
        .from_(converted) \
        .groupby(converted.source)

    if from_yr and to_yr:
        result.update({"from": from_yr, "to": to_yr})
        q_total = q_total.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        q_oa = q_oa.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        q_ssif = q_ssif.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        q_swedishlist = q_swedishlist.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        q_total_per_source = q_total_per_source.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        values.append([from_yr, to_yr])

    if source:
        result['source'] = source
        q_total = q_total.where(converted.source == Parameter('?'))
        q_oa = q_oa.where(converted.source == Parameter('?'))
        q_ssif = q_ssif.where(converted.source == Parameter('?'))
        q_swedishlist = q_swedishlist.where(converted.source == Parameter('?'))
        q_total_per_source = q_total_per_source.where(converted.source == Parameter('?'))
        values.append(source)

    values = list(flatten(values))
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    total_docs = cur.execute(str(q_total), values).fetchone()['total_docs']
    oa = cur.execute(str(q_oa), values).fetchone()['oa']
    ssif = cur.execute(str(q_ssif), values).fetchone()['ssif']
    swedishlist = cur.execute(str(q_swedishlist), values).fetchone()['swedishlist']

    result.update({
        "total": total_docs,
        "openAccess": {"percentage": get_percentage(oa, total_docs), "total": oa},
        "ssif": {"percentage": get_percentage(ssif, total_docs), "total": ssif},
        "swedishList": {"percentage": get_percentage(swedishlist, total_docs), "total": swedishlist}
    })

    if not source:
        result['sources'] = {}
        for row in cur.execute(str(q_total_per_source), values):
            result["sources"][row["source"]] = {
                "percentage": get_percentage(row["total"], total_docs),
                "total": row["total"]
            }
    return result


@app.route("/api/v1/datastatus/ssif")
def datastatus_ssif_endpoint():
    return datastatus_ssif_source_api(None)


@app.route("/api/v1/datastatus/ssif/<source>")
def datastatus_ssif_source_api(source=None):
    from_yr = request.args.get("from")
    to_yr = request.args.get("to")
    errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
    if errors:
        return _errors(errors)

    if source and source not in INFO_API_SOURCE_ORG_MAPPING:
        return _errors(['Source not found'], status_code=404)

    converted, converted_ssif_1 = Tables('converted', 'converted_ssif_1')
    values = []
    result = {"ssif": {}}

    q_total = Query \
        .select(fn.Count('*').as_('total_docs')) \
        .from_(converted_ssif_1)

    q_ssif = Query \
        .select(converted_ssif_1.value.as_('ssif_1'), fn.Count('*').as_('total')) \
        .from_(converted_ssif_1) \
        .groupby(converted_ssif_1.value)

    if source or (from_yr and to_yr):
        q_total = q_total \
            .left_join(converted) \
            .on(converted_ssif_1.converted_id == converted.id)
        q_ssif = q_ssif \
            .left_join(converted) \
            .on(converted_ssif_1.converted_id == converted.id)

    if source:
        result['source'] = source
        q_total = q_total.where(converted.source == Parameter('?'))
        q_ssif = q_ssif.where(converted.source == Parameter('?'))
        values.append(source)

    if from_yr and to_yr:
        result.update({"from": from_yr, "to": to_yr})
        q_total = q_total.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        q_ssif = q_ssif.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        values.append([from_yr, to_yr])

    values = list(flatten(values))
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    result['total'] = cur.execute(str(q_total), values).fetchone()['total_docs']
    for row in cur.execute(str(q_ssif), values):
        if row['ssif_1']:
            ssif_label = SSIF_LABELS[row['ssif_1']]
            result['ssif'][ssif_label] = {
                'total': row['total'],
                'percentage': get_percentage(row['total'], result['total'])
            }

    return result


@app.route('/api/v1/datastatus/validations', methods=['GET'])
def datastatus_validations():
    return datastatus_validations_source(source=None)


@app.route('/api/v1/datastatus/validations/<source>', methods=['GET'])
def datastatus_validations_source(source=None):
    from_yr = request.args.get("from")
    to_yr = request.args.get("to")
    errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
    if errors:
        return _errors(errors)

    if source and source not in INFO_API_SOURCE_ORG_MAPPING:
        return _errors(['Source not found'], status_code=404)

    stats_field_events = Table('stats_field_events')

    values = []
    q = Query \
        .select(stats_field_events.field_name, fn.Sum(stats_field_events.v_invalid).as_("sum")) \
        .from_(stats_field_events) \
        .groupby(stats_field_events.field_name)

    if source:
        q = q.where(stats_field_events.source == Parameter('?'))
        values.append(source)

    if from_yr and to_yr:
        q = q.where((stats_field_events.date >= Parameter('?')) & (stats_field_events.date <= Parameter('?')))
        values.append([from_yr, to_yr])

    cur = get_db().cursor()
    cur.row_factory = dict_factory
    rows = cur.execute(str(q), list(flatten(values))).fetchall()

    total = sum(row['sum'] for row in rows)
    result = {'total': total, 'validationFlags': {}}

    for row in rows:
        result['validationFlags'][row['field_name']] = {
            'percentage': round((row['sum'] / total) * 100, 2),
            'total': row['sum']
        }

    if source:
        result['source'] = source

    if from_yr and to_yr:
        result['from'] = from_yr
        result['to_yr'] = to_yr

    return result


# ██╗███╗   ██╗███████╗ ██████╗ 
# ██║████╗  ██║██╔════╝██╔═══██╗
# ██║██╔██╗ ██║█████╗  ██║   ██║
# ██║██║╚██╗██║██╔══╝  ██║   ██║
# ██║██║ ╚████║██║     ╚██████╔╝
# ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ 

@app.route("/api/v1/info/research-subjects", methods=['GET'])
def info_research_subjects():
    return jsonify(INFO_API_MAPPINGS)


@app.route("/api/v1/info/output-types", methods=['GET'])
def info_output_types():
    return jsonify(INFO_API_OUTPUT_TYPES)


@app.route("/api/v1/info/sources", methods=['GET'])
def info_sources():
    cur = get_db().cursor()
    cur.row_factory = lambda cursor, row: row[0]
    codes = cur.execute("SELECT DISTINCT source FROM harvest_history").fetchall()
    sources = []
    for code in codes:
        sources.append({'name': INFO_API_SOURCE_ORG_MAPPING[code]['name'], 'code': code})
    return {'sources': sources}


# ██████╗ ██████╗  ██████╗  ██████╗███████╗███████╗███████╗
# ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝██╔════╝
# ██████╔╝██████╔╝██║   ██║██║     █████╗  ███████╗███████╗
# ██╔═══╝ ██╔══██╗██║   ██║██║     ██╔══╝  ╚════██║╚════██║
# ██║     ██║  ██║╚██████╔╝╚██████╗███████╗███████║███████║
# ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚══════╝╚══════╝

@app.route("/api/v1/process/publications/<path:record_id>", methods=['GET'])
def process_get_publication(record_id=None):
    if record_id is None:
        return _errors(['Missing parameter: "record_id"'], status_code=400)

    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM converted WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        return _errors(["Not Found"], status_code=404)
    return Response(row[0], mimetype='application/ld+json')


@app.route("/api/v1/process/publications/<path:record_id>/original", methods=['GET'])
def process_get_original_publication(record_id=None):
    if record_id is None:
        return _errors(['Missing parameter: "record_id"'], status_code=400)

    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM original WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        return _errors(["Not Found"], status_code=404)
    return Response(row[0], mimetype='application/xml; charset=utf-8')


@app.route("/api/v1/process/<source>/status")
def process_get_harvest_status(source):
    if source is None:
        return _errors(['Missing parameter: "source"'], status_code=400)
    if source not in INFO_API_SOURCE_ORG_MAPPING:
        return _errors(['Source not found'], status_code=404)

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    row = cur.execute("""
    SELECT id, strftime('%Y-%m-%dT%H:%M:%SZ', harvest_start) AS start, strftime('%Y-%m-%dT%H:%M:%SZ', harvest_completed) AS completed, successes, rejected
    FROM harvest_history
    WHERE source = ?
    ORDER BY harvest_completed DESC
    LIMIT 1
    """, (source,)).fetchone()

    return {
        "completed_timestamp": row["completed"],
        "rejected": row["rejected"],
        "successes": row["successes"],
        "source_code": source,
        "source_name": INFO_API_SOURCE_ORG_MAPPING[source]['name'],
        "start_timestamp": row["start"]
    }


@app.route("/api/v1/process/<source>/status/history")
def process_get_harvest_status_history(source):
    if source is None:
        return _errors(['Missing parameter: "source"'], status_code=400)
    if source not in INFO_API_SOURCE_ORG_MAPPING:
        return _errors(['Source not found'], status_code=404)

    result = {
        "harvest_history": [],
        "source_code": source,
        "source_name": INFO_API_SOURCE_ORG_MAPPING[source]['name'],
    }

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    for row in cur.execute("""
        SELECT id, harvest_start, harvest_completed, successes, rejected
        FROM harvest_history
        WHERE source = ?
        ORDER BY harvest_completed DESC
    """, (source,)):
        result["harvest_history"].append({
            "completed_timestamp": row["harvest_completed"],
            "harvest_id": row["id"],
            "rejected": row["rejected"],
            "successes": row["successes"],
            "start_timestamp": row["harvest_start"]
        })

    oldest_harvest = cur.execute("SELECT MIN(harvest_start) AS oldest FROM harvest_history WHERE source = ?", (source,)).fetchone()['oldest']
    latest_harvest = cur.execute("SELECT MAX(harvest_start) AS latest FROM harvest_history WHERE source = ?", (source,)).fetchone()['latest']

    result["harvests_from"] = oldest_harvest
    result["harvests_to"] = latest_harvest

    return result

# TODO: 404, 500, ..
@app.route("/api/v1/process/<harvest_id>/rejected")
def process_get_rejected_publications(harvest_id):
    if harvest_id is None:
        return _errors(['Missing parameter: "harvest_id"'])

    limit = request.args.get('limit')
    offset = request.args.get('offset')
    (errors, limit, offset) = parse_limit_and_offset(limit, offset)
    if errors:
        return _errors(errors)

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    total_rejections = cur.execute("SELECT COUNT(*) AS total FROM rejected WHERE harvest_id = ?", (harvest_id,)).fetchone()["total"]
    source = cur.execute("SELECT source FROM harvest_history WHERE id = ? LIMIT 1", (harvest_id,)).fetchone()["source"]

    rejected = Table('rejected')

    q = Query \
        .select(rejected.oai_id, rejected.rejection_cause) \
        .from_(rejected) \
        .where(rejected.harvest_id == Parameter('?')) \
        .orderby('id')

    if limit:
        q = q.limit(limit)
    if offset:
        q = q.offset(offset)

    result = {
        "harvest_id": harvest_id,
        "rejected_publications": [],
        "source_code": source,
        "source_name": INFO_API_SOURCE_ORG_MAPPING[source]['name'],
        "total": total_rejections
    }

    for row in cur.execute(str(q), (harvest_id,)):
        error_list = []
        error_codes = json.loads(row["rejection_cause"])
        for error_code in error_codes:
            error = {"error_code": error_code}
            labels = DELIVERY_STATUS_ERROR_DESCRIPTIONS.get(error_code)
            if labels:
                error["labelByLang"] = labels
            error_list.append(error)

        result["rejected_publications"].append({
            "record_id": row["oai_id"],
            "errors": error_list
        })

    resp = make_response(jsonify(result))

    (prev_page, next_page) = process_get_pagination_links(request, url_for('process_get_rejected_publications', harvest_id=harvest_id), limit, offset, total_rejections)
    if prev_page:
        resp.headers.add('Link', f"<{prev_page}>", rel="prev")
    if next_page:
        resp.headers.add('Link', f"<{next_page}>", rel="next")

    return resp


@app.route('/api/v1/process/<source>', methods=['GET'])
def process_get_stats(source=None):
    if source is None:
        return _errors(['Missing parameter: "source"'], status_code=400)
    if source not in INFO_API_SOURCE_ORG_MAPPING:
        return _errors(['Source not found'], status_code=404)

    from_yr = request.args.get("from")
    to_yr = request.args.get("to")
    errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
    if errors:
        return _errors(errors)

    result = {
        'code': source,
        'source': INFO_API_SOURCE_ORG_MAPPING[source]['name'],
        'audits': {},
        'enrichments': {},
        'normalizations': {},
        'validations': {},
        'total': 0,
    }

    if from_yr and to_yr:
        date_sql = f' AND date >= ? AND date <= ?'
        values = [source, from_yr, to_yr]
    else:
        date_sql = ''
        values = [source]

    cur = get_db().cursor()
    cur.row_factory = dict_factory
    for row in cur.execute(f"""
        SELECT
            label, SUM(valid) AS valid, SUM(invalid)
        AS
            invalid
        FROM
            stats_audit_events
        WHERE
            source = ?
        {date_sql}
        GROUP BY
            label
            """, values):
        result['audits'][row['label']] = {}
        if row['valid']:
            result['audits'][row['label']]['valid'] = row['valid']
        if row['invalid']:
            result['audits'][row['label']]['invalid'] = row['invalid']

    for row in cur.execute(f"""
        SELECT
            field_name,
            SUM(e_enriched) AS e_enriched,
            SUM(e_unchanged) AS e_unchanged,
            SUM(e_unsuccessful) AS e_unsuccessful,
            SUM(n_unchanged) AS n_unchanged,
            SUM(n_normalized) AS n_normalized,
            SUM(v_valid) AS v_valid,
            SUM(v_invalid) AS v_invalid
        FROM
            stats_field_events
        WHERE
            source = ?
        {date_sql}
        GROUP BY
            field_name
    """, values):
        result['enrichments'][row['field_name']] = {}
        result['normalizations'][row['field_name']] = {}
        result['validations'][row['field_name']] = {}

        if row['e_enriched']:
            result['enrichments'][row['field_name']]['enriched'] = row['e_enriched']
        if row['e_unchanged']:
            result['enrichments'][row['field_name']]['unchanged'] = row['e_unchanged']
        if row['e_unsuccessful']:
            result['enrichments'][row['field_name']]['unsuccessful'] = row['e_unsuccessful']

        if row['n_unchanged']:
            result['normalizations'][row['field_name']]['unchanged'] = row['n_unchanged']
        if row['n_normalized']:
            result['normalizations'][row['field_name']]['normalized'] = row['n_normalized']

        if row['v_valid']:
            result['validations'][row['field_name']]['valid'] = row['v_valid']
        if row['v_invalid']:
            result['validations'][row['field_name']]['invalid'] = row['v_invalid']

    result['total'] = cur.execute("SELECT COUNT(*) AS total_docs FROM converted WHERE source = ?", [source]).fetchone()["total_docs"]

    return result


@app.route('/api/v1/process/<source>/export', methods=['GET'])
def process_get_export(source=None):
    if source is None:
        return _errors(['Missing parameter: "source"'], status_code=400)
    if source not in INFO_API_SOURCE_ORG_MAPPING:
        return _errors(['Source not found'], status_code=404)

    export_as_csv = False
    csv_mimetype = 'text/csv'
    tsv_mimetype = 'text/tab-separated-values'
    export_mimetype = csv_mimetype
    csv_flavor = 'csv'
    accept = request.headers.get('accept')
    if accept and accept == csv_mimetype:
        export_as_csv = True
    elif accept and accept == tsv_mimetype:
        export_as_csv = True
        csv_flavor = 'tsv'
        export_mimetype = tsv_mimetype
    else:
        export_mimetype = 'application/json'

    from_date = request.args.get('from')
    to_date = request.args.get('to')
    limit = request.args.get('limit')
    offset = request.args.get('offset')
    (errors, limit, offset) = parse_limit_and_offset(limit, offset)
    if errors:
        return _errors(errors)
    (errors, from_date, to_date) = parse_dates(from_date, to_date)
    if errors:
        return _errors(errors)
    validation_flags = request.args.get('validation_flags')
    enrichment_flags = request.args.get('enrichment_flags')
    normalization_flags = request.args.get('normalization_flags')
    audit_flags = request.args.get('audit_flags')
    (errors, selected_flags) = parse_flags(
        validation_flags, enrichment_flags, normalization_flags, audit_flags)
    if errors:
        return _errors(errors)

    converted, converted_record_info, converted_audit_events = Tables('converted', 'converted_record_info', 'converted_audit_events')
    values = []
    q = Query \
        .select(converted.oai_id).distinct() \
        .select(converted.date, converted.data, converted.events) \
        .from_(converted) \
        .where(converted.source == Parameter('?'))

    values.append(source)

    # We only need to join the converted_record_info table if a validation/enrichment/normalization flag
    # was selected, *or* if no flags were selected at all
    if any([selected_flags['validation'], selected_flags['enrichment'], selected_flags['normalization']]) or not any(selected_flags.values()):
        q = q \
            .left_join(converted_record_info) \
            .on(converted.id == converted_record_info.converted_id)

    # ...and likewise for converted_audit_events
    if selected_flags['audit'] or not any(selected_flags.values()):
        q = q \
            .left_join(converted_audit_events) \
            .on(converted.id == converted_audit_events.converted_id)

    if from_date and to_date:
        q = q.where((converted.date >= Parameter('?')) & (converted.date <= Parameter('?')))
        values.append([from_date, to_date])

    # Specified flags should be OR'd together, so we build up a list of criteria and use
    # pypika's Criterion.any.
    criteria = []
    for flag_type, flags in selected_flags.items():
        for flag_name, flag_values in flags.items():
            if flag_type in ['validation', 'enrichment', 'normalization']:
                for flag_value in flag_values:
                    criteria.append(
                        (converted_record_info.field_name == Parameter('?')) & \
                        (converted_record_info[f"{flag_type}_status"] == Parameter('?'))
                    )
                    values.append([flag_name, flag_value])
            if flag_type == 'audit':
                for flag_value in flag_values:
                    criteria.append(
                        (converted_audit_events.code == Parameter('?')) & \
                        (converted_audit_events.result == Parameter('?'))
                    )
                    int_flag_value = 1 if flag_value == 'valid' else 0
                    values.append([flag_name, int_flag_value])
    q = q.where(Criterion.any(criteria))

    if limit:
        q = q.limit(limit)
    if offset:
        q = q.offset(offset)

    handled_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    def get_results():
        # Exports can be large and we don't want to load everything into memory, so we stream
        # the output (each yield is sent directly to the client).
        # Since we send one result at a time, we can't send a ready-made dict when JSON is selected.
        if export_as_csv:
            yield f"# Swepub data processing export. Query handled at {handled_at}. Query parameters: {request.args.to_dict()}\n"
        else:
            yield(
                f'{{"code": "{source}",'
                f'"hits": ['
            )
        total = 0
        for row in cur.execute(str(q), list(flatten(values))):
            flask_url = url_for('process_get_original_publication', record_id=row['oai_id'])
            proto = request.headers.get("X-Forwarded-Proto")
            host = request.headers.get("X-Forwarded-Host")
            mods_url = f"{proto}://{host}{flask_url}"
            export_result = build_export_result(
                    json.loads(row['data']),
                    json.loads(row['events']),
                    selected_flags,
                    row['oai_id'],
                    mods_url)

            if export_as_csv:
                yield(process_csv_export(export_result, csv_flavor, request.args.to_dict(), handled_at,  total))
            else:
                maybe_comma = ',' if total > 0 else ''
                yield(maybe_comma + json.dumps(export_result))
            total += 1
        if not export_as_csv:
            yield('],')
            if from_date and to_date:
                yield(f'"from": {from_date},')
                yield(f'"to": {to_date},')
            yield(
                f'"query": {json.dumps(request.args)},'
                f'"query_handled_at": "{handled_at}",'
                f'"source": "{INFO_API_SOURCE_ORG_MAPPING[source]["name"]}",'
                f'"total": {total}'
                '}'
            )

    return app.response_class(stream_with_context(get_results()), mimetype=export_mimetype)


if __name__ == '__main__':
    app.run()
