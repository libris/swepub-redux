#!/usr/bin/env python3
import itertools
from pathlib import Path
import sqlite3
from flask import Flask, g, request, jsonify

from utils import *

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


def flatten(t):
    return [item for sublist in t for item in sublist]


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


@app.route("/api/v1/bibliometrics", methods=['POST'])
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

        single_values_where = []
        if from_yr and to_yr:
            single_values_where.append(["year >= ? AND year <= ?", [from_yr, to_yr]])
        if content_marking:
            single_values_where.append([f"content_marking IN ({', '.join(['?'] * len(content_marking))})", content_marking])
        if publication_status:
            single_values_where.append([f"content_marking IN ({', '.join(['?'] * len(publication_status))})", publication_status])
        if swedish_list:
            single_values_where.append(["swedish_list = 1", []])
        if open_access:
            single_values_where.append(["open_access = 1", []])

        single_values_sql_where = " AND ".join(item[0] for item in single_values_where)
        single_values_params = flatten(item[1] for item in single_values_where)

        creator_where = []
        if orcid:
            creator_where.append(["orcid = ?", [orcid]])
        if given_name:
            creator_where.append(["given_name = ?", [orcid]])
        if family_name:
            creator_where.append(["family_name = ?", [family_name]])
        if person_local_id:
            creator_where.append(["orcid = ?", [person_local_id]])
        if person_local_id_by:
            creator_where.append(["orcid = ?", [person_local_id_by]])
        creator_sql_where = " AND ".join(item[0] for item in creator_where)
        creator_params = flatten(item[1] for item in creator_where)

        search_ft_title_kw_where = []
        if title:
            search_ft_title_kw_where.append(["title MATCH ?", [title]])
        if keywords:
            search_ft_title_kw_where.append(["keywords MATCH ?", [keywords]])
        search_ft_title_kw_sql_where = " AND ".join(item[0] for item in search_ft_title_kw_where)
        search_ft_title_kw_params = flatten(item[1] for item in search_ft_title_kw_where)

        cur = get_db().cursor()
        cur.row_factory = lambda cursor, row: row[0]

        single_values_finalized_ids = None
        if single_values_sql_where:
            single_values_finalized_ids = set(cur.execute(
                f"SELECT finalized_id FROM search_single_values WHERE {single_values_sql_where}",
                single_values_params).fetchall())

        creator_finalized_ids = None
        if creator_sql_where:
            creator_finalized_ids = set(cur.execute(
                f"SELECT finalized_id FROM search_creator WHERE {creator_sql_where}",
                creator_params).fetchall())

        search_ft_title_kw_finalized_ids = None
        if search_ft_title_kw_sql_where:
            search_ft_title_kw_finalized_ids = set(cur.execute(
                f"SELECT rowid FROM search_fulltext_title_keywords WHERE {search_ft_title_kw_sql_where}",
                search_ft_title_kw_params).fetchall())

        doi_finalized_ids = None
        if doi:
            doi_finalized_ids = set(cur.execute("SELECT finalized_id from search_doi WHERE doi = ?", [doi]).fetchall())

        genre_form_finalized_ids = None
        if genre_form:
            genre_form_finalized_ids = set(cur.execute(
                f"SELECT finalized_id FROM search_genre_form WHERE genre_form IN ({', '.join(['?'] * len(genre_form))})",
                genre_form).fetchall())

        subject_finalized_ids = None
        if subjects:
            subject_finalized_ids = set(cur.execute(
                f"SELECT finalized_id FROM search_subject WHERE subject IN ({', '.join(['?'] * len(subjects))})",
                subjects).fetchall())

        org_finalized_ids = None
        if orgs:
            org_finalized_ids = set(cur.execute(
                f"SELECT finalized_id FROM search_org WHERE org IN ({', '.join(['?'] * len(orgs))})",
                orgs).fetchall())

        sets_to_use = [item for item in [
                single_values_finalized_ids,
                creator_finalized_ids,
                search_ft_title_kw_finalized_ids,
                doi_finalized_ids,
                genre_form_finalized_ids,
                subject_finalized_ids,
                org_finalized_ids
            ] if isinstance(item, set)]

        finalized_id_set = set.intersection(set(sets_to_use[0]), *itertools.islice(sets_to_use, 1, None))

        return {'ids': list(finalized_id_set)}

    except (AttributeError, ValueError, TypeError):
        return _error(errors=[f"Invalid value for json body query parameter/s."], status_code=400)


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


if __name__ == '__main__':
    app.run()
