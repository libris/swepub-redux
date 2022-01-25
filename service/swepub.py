#!/usr/bin/env python3
import json
import os

import bibliometrics
from utils import *

import enum
from collections import Iterable
from datetime import datetime
from pathlib import Path
import sqlite3
from flask import Flask, g, request, jsonify
from pypika import Query, Tables, Parameter
from pypika.terms import BasicCriterion

# Database in parent directory of swepub.py directory
DATABASE = str(Path.joinpath(Path(__file__).resolve().parents[1], 'swepub.sqlite3'))

SSIF_LABELS = {
    1: "1 Naturvetenskap",
    2: "2 Teknik",
    3: "3 Medicin och hälsovetenskap",
    4: "4 Lantbruksvetenskap och veterinärmedicin",
    5: "5 Samhällsvetenskap",
    7: "6 Humaniora och konst"
}

INFO_API_MAPPINGS = sort_mappings(json.load(open(os.path.dirname(__file__) + '/../pipeline/ssif_research_subjects.json')))
INFO_API_OUTPUT_TYPES = json.load(open(os.path.dirname(__file__) + '/../pipeline/output_types.json'))
INFO_API_SOURCE_ORG_MAPPING = get_source_org_mapping(json.load(open(os.path.dirname(__file__) + '/../pipeline/sources.json')))

# Note: static files should be served by Apache/nginx
app = Flask(__name__, static_url_path='', static_folder='vue-client/dist')


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# https://stackoverflow.com/a/3300514
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def flatten(l):
    for el in l:
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


def _error(errors, status_code=400):
    resp = {
        'errors': errors,
        'status_code': status_code
    }
    return jsonify(resp), status_code


class Comparator(enum.Enum):
    match = " MATCH "


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
@app.route("/bibliometrics")
@app.route("/classify")
@app.route("/datastatus")
@app.route("/process")
def index_file():
    return app.send_static_file('index.html')


@app.route("/api/v1/bibliometrics", methods=['POST'], strict_slashes=False)
def bibliometrics_api():
    if request.content_type != 'application/json':
        return _error(errors=['Content-Type must be "application/json"'])

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
            return _error(errors)

        content_marking = [cm.strip() for cm in query_data.get("contentMarking", []) if len(cm.strip()) > 0]
        if len(content_marking) > 0:
            if not (all(cm in ("ref", "vet", "pop") for cm in content_marking)):
                return _error(errors=[f"Invalid value for content marking."], status_code=400)

        publication_status = [ps.strip() for ps in query_data.get("publicationStatus", []) if len(ps.strip()) > 0]
        if len(publication_status) > 0:
            if not all(ps in ("published", "epub", "submitted") for ps in publication_status):
                return _error(errors=[f"Invalid value for publication status."], status_code=400)

        swedish_list = query_data.get("swedishList")
        open_access = query_data.get("openAccess")

        orcid = query_data.get("creator", {}).get("ORCID")
        given_name = query_data.get("creator", {}).get("givenName")
        family_name = query_data.get("creator", {}).get("familyName")
        person_local_id = query_data.get("creator", {}).get("localId")
        person_local_id_by = query_data.get("creator", {}).get("localIdBy")

    except (AttributeError, ValueError, TypeError):
        return _error(errors=[f"Invalid value for json body query parameter/s."], status_code=400)

    finalized, search_single, search_creator, search_fulltext, search_doi, search_genre_form, search_subject, search_org = Tables('finalized', 'search_single', 'search_creator', 'search_fulltext', 'search_doi', 'search_genre_form', 'search_subject', 'search_org')
    q = Query.from_(finalized).select('data')
    if limit:
        q = q.limit(limit)
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
        q = q.join(search_fulltext).on(finalized.id == search_fulltext.rowid)

    for param in [(search_doi, doi), (search_genre_form, genre_form), (search_subject, subjects), (search_org, orgs)]:
        if param[1]:
            if isinstance(param[1], list):
                q = q.where(param[0].value.isin([Parameter(', '.join(['?'] * len(param[1])))]))
            else:
                q = q.where(param[0].value == Parameter('?'))
            q = q.join(param[0]).on(finalized.id == param[0].finalized_id)
            values.append(param[1])

    print(str(q))
    print(list(flatten(values)))

    cur = get_db().cursor()
    #cur.row_factory = lambda cursor, row: row[0]
    cur.row_factory = dict_factory
    rows = cur.execute(str(q), list(flatten(values))).fetchall()

    fields = query_data.get("fields", [])
    if fields is None:
        fields = []
    (result, errors) = bibliometrics.build_result(rows, from_yr, to_yr, fields)

    if len(errors) > 0:
        return _error(errors)

    handled_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    #if export_as_csv:
    #    return Response(
    #        csv_export(result['hits'], fields, csv_flavor, query_data, handled_at),
    #        mimetype=default_mimetype)
    #else:
    result["query"] = query_data
    result["query_handled_at"] = handled_at
    return jsonify(result)


# TODO: from/to
@app.route("/api/v1/datastatus")
def datastatus():
    from_yr = request.args.get("from")
    to_yr = request.args.get("to")
    errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
    if errors:
        return _error(errors)

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    result = {"sources": {}}

    total_docs = cur.execute(f"SELECT COUNT(*) AS total_docs FROM converted").fetchone()["total_docs"]
    result["total"] = total_docs
    oa = cur.execute("SELECT COUNT(*) AS oa FROM converted WHERE is_open_access = 1").fetchone()["oa"]
    result["openAccess"] = {"percentage": get_percentage(oa, total_docs), "total": oa}

    ssif = cur.execute("SELECT COUNT(*) AS ssif from converted WHERE classification_level > 0").fetchone()["ssif"]
    result["ssif"] = {"percentage": get_percentage(ssif, total_docs), "total": ssif}

    swedish_list = cur.execute("SELECT COUNT(*) AS swedishlist from converted WHERE is_swedishlist = 1").fetchone()["swedishlist"]
    result["swedishList"] = {"percentage": get_percentage(swedish_list, total_docs), "total": swedish_list}

    for row in cur.execute("SELECT source, count(*) AS total FROM converted GROUP BY source"):
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
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    result = {"ssif": {}}

    total_sql = "SELECT COUNT(*) AS total_docs from converted"
    total_params = []
    classification_sql = "SELECT classification_level, count(*) AS total FROM converted GROUP BY classification_level"
    classification_params = []
    if source:
        result["source"] = source
        total_sql = "SELECT COUNT(*) AS total_docs from converted WHERE source = ?"
        total_params = [source]
        classification_sql = "SELECT classification_level, count(*) AS total FROM converted WHERE source = ? GROUP BY classification_level"
        classification_params = [source]

    result["total"] = cur.execute(total_sql, total_params).fetchone()["total_docs"]
    for row in cur.execute(classification_sql, classification_params):
        ssif_label = SSIF_LABELS[row["classification_level"]]
        result["ssif"][ssif_label] = {
            "total": row["total"],
            "percentage": get_percentage(row["total"], result["total"])
        }

    return result


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
    codes = cur.execute("SELECT DISTINCT value FROM search_org").fetchall()
    sources = []
    for code in codes:
        sources.append({'name': INFO_API_SOURCE_ORG_MAPPING[code], 'code': code})
    return {'sources': sources}


if __name__ == '__main__':
    app.run()
