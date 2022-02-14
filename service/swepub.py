#!/usr/bin/env python3
import json
import os

from utils import bibliometrics
from utils.common import *
from utils.process import *

from datetime import datetime
from pathlib import Path
import sqlite3
from flask import Flask, g, request, jsonify, Response, stream_with_context, url_for
from pypika import Query, Tables, Parameter, Table, Criterion
from pypika.terms import BasicCriterion
from pypika import functions as fn

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
INFO_API_SOURCE_ORG_MAPPING = json.load(open(os.path.dirname(__file__) + '/../pipeline/sources.json'))

# Note: static files should be served by Apache/nginx
app = Flask(__name__, static_url_path='', static_folder='vue-client/dist')


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


def _error(errors, status_code=400):
    resp = {
        'errors': errors,
        'status_code': status_code
    }
    return jsonify(resp), status_code


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
    print(str(q_total))
    print(str(q))
    print(list(flatten(values)))

    cur = get_db().cursor()
    cur.row_factory = dict_factory
    total = cur.execute(str(q_total), list(flatten(values))).fetchone()

    rows = cur.execute(str(q), list(flatten(values))).fetchall()

    fields = query_data.get("fields", [])
    if fields is None:
        fields = []
    (result, errors) = bibliometrics.build_result(rows, from_yr, to_yr, fields, total['total'])

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


@app.route("/api/v1/bibliometrics/publications/<record_id>", methods=['GET'])
def bibliometrics_get_record(record_id):
    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM finalized WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        return _error(["Not Found"], status_code=404)
    doc = json.loads(row[0])
    # TODO: Don't store the following in the actual document
    doc.pop('_publication_ids', None)
    doc.pop('_publication_orgs', None)
    return doc


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

    if from_yr and to_yr:
        result.update({"from": from_yr, "to": to_yr})
        date_params = [from_yr, to_yr]

        total_docs = cur.execute(f"SELECT COUNT(*) AS total_docs FROM converted WHERE date >= ? AND date <= ?", date_params).fetchone()["total_docs"]
        oa = cur.execute("SELECT COUNT(*) AS oa FROM converted WHERE is_open_access = 1 AND date >= ? AND date <= ?", date_params).fetchone()["oa"]
        ssif = cur.execute("SELECT COUNT(*) AS ssif from converted WHERE classification_level > 0 AND date >= ? AND date <= ?", date_params).fetchone()["ssif"]
        swedish_list = cur.execute("SELECT COUNT(*) AS swedishlist from converted WHERE classification_level = 1 AND date >= ? AND date <= ?", date_params).fetchone()[
            "swedishlist"]
        total_per_source_sql = "SELECT source, count(*) AS total FROM converted WHERE date >= ? AND date <= ? GROUP BY source"
        total_per_source_params = date_params
    else:
        total_docs = cur.execute(f"SELECT COUNT(*) AS total_docs FROM converted").fetchone()["total_docs"]
        oa = cur.execute("SELECT COUNT(*) AS oa FROM converted WHERE is_open_access = 1").fetchone()["oa"]
        ssif = cur.execute("SELECT COUNT(*) AS ssif from converted WHERE classification_level > 0").fetchone()["ssif"]
        swedish_list = cur.execute("SELECT COUNT(*) AS swedishlist from converted WHERE classification_level = 1").fetchone()[
            "swedishlist"]
        total_per_source_sql = "SELECT source, count(*) AS total FROM converted GROUP BY source"
        total_per_source_params = []

    result.update({
        "sources": {},
        "total": total_docs,
        "openAccess": {"percentage": get_percentage(oa, total_docs), "total": oa},
        "ssif": {"percentage": get_percentage(ssif, total_docs), "total": ssif},
        "swedishList": {"percentage": get_percentage(swedish_list, total_docs), "total": swedish_list}
    })

    for row in cur.execute(total_per_source_sql, total_per_source_params):
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
        return _error(errors)

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    result = {"ssif": {}}

    total_sql = "SELECT COUNT(*) AS total_docs from converted"
    total_params = []
    classification_sql = "SELECT classification_level, count(*) AS total FROM converted GROUP BY classification_level"
    classification_params = []
    if source:
        result["source"] = source
        total_sql = "SELECT COUNT(*) AS total_docs FROM converted WHERE source = ?"
        total_params = [source]
        classification_sql = "SELECT classification_level, count(*) AS total FROM converted WHERE source = ? GROUP BY classification_level"
        classification_params = [source]

    result["total"] = cur.execute(total_sql, total_params).fetchone()["total_docs"]
    for row in cur.execute(classification_sql, classification_params):
        if (row["classification_level"]):
            ssif_label = SSIF_LABELS[row["classification_level"]]
            result["ssif"][ssif_label] = {
                "total": row["total"],
                "percentage": get_percentage(row["total"], result["total"])
            }
    return result


@app.route('/api/v1/validations', methods=['GET'])
def datastatus_validations():
    return datastatus_validations_source(source=None)


@app.route('/api/v1/validations/<source>', methods=['GET'])
def datastatus_validations_source(source=None):
    from_yr = request.args.get("from")
    to_yr = request.args.get("to")
    errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
    if errors:
        return _error(errors)

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

    if not rows:
        return _error(["Not Found"], status_code=404)

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
        sources.append({'name': INFO_API_SOURCE_ORG_MAPPING[code]['name'], 'code': code})
    return {'sources': sources}


@app.route("/api/v1/process/publications/<path:record_id>", methods=['GET'])
def process_get_publication(record_id=None):
    if record_id is None:
        return _error(['Missing parameter: "record_id"'], status_code=400)

    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM converted WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        return _error(["Not Found"], status_code=404)
    return Response(row[0], mimetype='application/ld+json')



@app.route("/api/v1/process/publications/<path:record_id>/original", methods=['GET'])
def process_get_original_publication(record_id=None):
    if record_id is None:
        return _error(['Missing parameter: "record_id"'], status_code=400)

    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM original WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        return _error(["Not Found"], status_code=404)
    return Response(row[0], mimetype='application/xml; charset=utf-8')


# TODO?
@app.route("/api/v1/process/<harvest_id>/rejected")
def process_get_rejected_publications(harvest_id):
    return {}


@app.route('/api/v1/process/<source>', methods=['GET'])
def process_get_stats(source=None):
    if source is None:
        return _error(['Missing parameter: "source"'], status_code=400)
    if source not in INFO_API_SOURCE_ORG_MAPPING:
        return _error(['Source not found'], status_code=404)

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    result = {
        'code': source,
        'source': INFO_API_SOURCE_ORG_MAPPING[source]['name'],
        'audits': {},
        'enrichments': {},
        'normalizations': {},
        'validations': {},
        'total': 0,
    }

    for row in cur.execute("""
        SELECT
            label, SUM(valid) AS valid, SUM(invalid)
        AS
            invalid
        FROM
            stats_audit_events
        WHERE
            source = ?
        GROUP BY
            label
            """, [source]):
        result['audits'][row['label']] = {}
        if row['valid']:
            result['audits'][row['label']]['valid'] = row['valid']
        if row['invalid']:
            result['audits'][row['label']]['invalid'] = row['invalid']

    for row in cur.execute("""
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
        GROUP BY
            field_name
    """, [source]):
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
        return _error(['Missing parameter: "source"'], status_code=400)
    if source not in INFO_API_SOURCE_ORG_MAPPING:
        return _error(['Source not found'], status_code=404)

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

    print(selected_flags)

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
                        (converted_audit_events.step == Parameter('?')) & \
                        (converted_audit_events.result == Parameter('?'))
                    )
                    int_flag_value = 1 if flag_value == 'valid' else 0
                    values.append([flag_name, int_flag_value])
    q = q.where(Criterion.any(criteria))

    if limit:
        q = q.limit(limit)
    if offset:
        q = q.offset(offset)

    print(str(q))

    handled_at = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    def get_results():
        # Exports can be large and we don't want to load everything into memory, so we stream
        # the output (each yield is sent directly to the client).
        # Since we send one result at a time, we can't send a ready-made dict when JSON is selected.
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
            maybe_comma = ',' if total > 0 else ''
            total += 1
            yield(maybe_comma + json.dumps(build_export_result(
                json.loads(row['data']),
                json.loads(row['events']),
                selected_flags,
                row['oai_id'],
                mods_url))
            )
        yield(
            f'],'
            f'"query": {json.dumps(request.args)},'
            f'"query_handled_at": "{handled_at}",'
            f'"source": "{INFO_API_SOURCE_ORG_MAPPING[source]["name"]}",'
            f'"total": {total}'
            '}'
        )

    return app.response_class(stream_with_context(get_results()), mimetype='application/json')


if __name__ == '__main__':
    app.run()
