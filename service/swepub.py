#!/usr/bin/env python3
import json
import orjson
from functools import wraps
from os import getenv
from pathlib import Path
import requests

from datetime import datetime
import sqlite3
from flask import (
    Flask,
    g,
    request,
    jsonify,
    Response,
    stream_with_context,
    url_for,
    make_response,
    abort,
    send_from_directory,
    render_template,
)
from flask_cors import CORS
from lxml.etree import LxmlError
from pypika import Query, Tables, Parameter, Table, Criterion
from pypika.terms import BasicCriterion
from pypika import functions as fn
from collections import Counter
from tempfile import NamedTemporaryFile
from simplemma.langdetect import lang_detector

from pipeline.convert import ModsParser
from pipeline.util import Enrichment, Normalization, Validation, ENRICHING_AUDITORS_CODES
from pipeline.legacy_publication import Publication as LegacyPublication
from pipeline.ldcache import embellish

from service.utils import bibliometrics
from service.utils.common import *
from service.utils.process import *
from service.utils.process_csv import export as process_csv_export
from service.utils.bibliometrics_csv import export as bibliometrics_csv_export
from service.utils import ssif

MODULE_DIR = Path(__file__).parent
PROJECT_ROOT = MODULE_DIR.parent

# sqlite DB path defaults to file in parent directory of swepub.py directory if SWEPUB_DB_READONLY not set
SWEPUB_DB_READONLY = getenv("SWEPUB_DB_READONLY") or str(PROJECT_ROOT / "swepub.sqlite3")

with (PROJECT_ROOT / "resources" / "ssif.jsonld").open() as f:
    SSIF_DATA = json.load(f)

SSIF_MAPPINGS = ssif.make_mappings(SSIF_DATA)
SSIF_TREE = ssif.build_tree_form(SSIF_MAPPINGS)
SSIF_LABELS = ssif.get_top_labels(SSIF_TREE)

with (PROJECT_ROOT / "resources" / "output_types.json").open() as f:
    INFO_API_OUTPUT_TYPES = json.load(f)


DEFAULT_SWEPUB_SOURCE_FILE = PROJECT_ROOT / "resources" / "sources.json"
SWEPUB_SOURCE_FILE = getenv("SWEPUB_SOURCE_FILE", DEFAULT_SWEPUB_SOURCE_FILE)

INFO_API_SOURCE_ORG_MAPPING = json.load(open(SWEPUB_SOURCE_FILE))

with (PROJECT_ROOT / "resources" / "mods_to_xjsonld.xsl").open() as f:
    DEFAULT_XSLT = "\n".join(
        [
            x.strip("\n\r")
            for x in f
            if x.strip(" \t\n\r")
        ]
    )

ANNIF_EN_URL = getenv("ANNIF_EN_URL", "http://127.0.0.1:8083/v1/projects/swepub-en")
ANNIF_SV_URL = getenv("ANNIF_SV_URL", "http://127.0.0.1:8083/v1/projects/swepub-sv")

# Note: static files should be served by Apache/nginx
app = Flask(__name__, static_url_path="/app", static_folder="vue-client/dist")
CORS(app)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(f"{SWEPUB_DB_READONLY}")
        if getenv("SWEPUB_LOG_LEVEL") == "DEBUG":
            db.set_trace_callback(print)
        cursor = db.cursor()
        cursor.execute("PRAGMA cache_size=-64000")  # negative number = kibibytes
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA journal_mode=WAL")
    return db


@app.teardown_appcontext
def close_connection(_exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def _errors(errors, status_code=400):
    resp = {"errors": errors, "status_code": status_code}
    abort(make_response(jsonify(resp), status_code))


def check_from_to(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.from_yr = request.args.get("from")
        g.to_yr = request.args.get("to")
        errors, from_yr, to_yr = parse_dates(g.from_yr, g.to_yr)
        if errors:
            _errors(errors)
        return f(*args, **kwargs)

    return decorated_function


@app.before_request
def valid_source():
    if (
        request.view_args
        and "source" in request.view_args
        and request.view_args["source"] not in INFO_API_SOURCE_ORG_MAPPING
    ):
        _errors(["Source not found"], status_code=404)


# Catchall routes - the Vue app handles all non-API routes
@app.route("/", defaults={"_path": ""})
@app.route("/<path:_path>")
def catch_all(_path):
    return app.send_static_file("index.html")


# ██████╗ ██╗██████╗ ██╗     ██╗ ██████╗ ███╗   ███╗███████╗████████╗██████╗ ██╗ ██████╗███████╗
# ██╔══██╗██║██╔══██╗██║     ██║██╔═══██╗████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝██╔════╝
# ██████╔╝██║██████╔╝██║     ██║██║   ██║██╔████╔██║█████╗     ██║   ██████╔╝██║██║     ███████╗
# ██╔══██╗██║██╔══██╗██║     ██║██║   ██║██║╚██╔╝██║██╔══╝     ██║   ██╔══██╗██║██║     ╚════██║
# ██████╔╝██║██████╔╝███████╗██║╚██████╔╝██║ ╚═╝ ██║███████╗   ██║   ██║  ██║██║╚██████╗███████║
# ╚═════╝ ╚═╝╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝


@app.route("/api/v1/bibliometrics", methods=["POST"], strict_slashes=False)
@app.route("/api/v2/bibliometrics", methods=["POST"], strict_slashes=False)
def bibliometrics_api():
    if request.content_type != "application/json":
        _errors(errors=['Content-Type must be "application/json"'])

    export_as_csv, export_mimetype, csv_flavor = export_options(request)
    query_data = request.json
    try:
        limit = query_data.get("limit")
        if limit:
            limit = int(limit)

        doi = query_data.get("DOI")

        # TODO: Ugly replacements, fix frontend
        genre_form = [
            gf.strip().replace(".", "/").rstrip("/")
            for gf in query_data.get("genreForm", [])
            if len(gf.strip()) > 0
        ]

        genre_form_broader = [gfb.strip() for gfb in query_data.get("match-genreForm", []) if len(gfb.strip()) > 0]

        orgs = [o.strip() for o in query_data.get("org", []) if len(o.strip()) > 0]
        title = query_data.get("title", "").replace(",", " ")
        keywords = query_data.get("keywords", "").replace(",", " ")

        subjects = query_data.get("classification", [])
        if isinstance(subjects, str):
            subjects = subjects.split(",")
        subjects = [s.strip() for s in subjects if len(s.strip()) > 0]

        from_yr = query_data.get("years", {}).get("from")
        to_yr = query_data.get("years", {}).get("to")
        errors, from_yr, to_yr = parse_dates(from_yr, to_yr)
        if errors:
            return _errors(errors)

        content_marking = [
            cm.strip() for cm in query_data.get("contentMarking", []) if len(cm.strip()) > 0
        ]
        if len(content_marking) > 0:
            if not (all(cm in ("ref", "vet", "pop") for cm in content_marking)):
                _errors(errors=[f"Invalid value for content marking."], status_code=400)

        publication_status = [
            ps.strip() for ps in query_data.get("publicationStatus", []) if len(ps.strip()) > 0
        ]
        if len(publication_status) > 0:
            if not all(ps in ("published", "epub", "submitted", "retracted") for ps in publication_status):
                _errors(errors=[f"Invalid value for publication status."], status_code=400)

        swedish_list = query_data.get("swedishList", None)
        open_access = query_data.get("openAccess", None)
        autoclassified = query_data.get("autoclassified", None)
        doaj = query_data.get("DOAJ", None)

        orcid = query_data.get("creator", {}).get("ORCID")
        given_name = query_data.get("creator", {}).get("givenName")
        family_name = query_data.get("creator", {}).get("familyName")
        person_local_id = query_data.get("creator", {}).get("localId")
        person_local_id_by = query_data.get("creator", {}).get("localIdBy")

    except (AttributeError, ValueError, TypeError):
        _errors(errors=[f"Invalid value for json body query parameter/s."], status_code=400)

    (
        finalized,
        search_single,
        search_creator,
        search_fulltext,
        search_doi,
        search_genre_form,
        search_subject,
        search_org,
    ) = Tables(
        "finalized",
        "search_single",
        "search_creator",
        "search_fulltext",
        "search_doi",
        "search_genre_form",
        "search_subject",
        "search_org",
    )
    q = Query.from_(search_single)
    values = []

    if from_yr and to_yr:
        q = q.where((search_single.year >= Parameter("?")) & (search_single.year <= Parameter("?")))
        values.append([from_yr, to_yr])
    if swedish_list is not None:
        q = q.where(search_single.swedish_list == bool(swedish_list))
    if open_access is not None:
        q = q.where(search_single.open_access == bool(open_access))
    if autoclassified is not None:
        q = q.where(search_single.autoclassified == bool(autoclassified))
    if doaj is not None:
        q = q.where(search_single.doaj == bool(doaj))
    for field_name, value in {
        "content_marking": content_marking,
        "publication_status": publication_status,
    }.items():
        if value:
            q = q.where(search_single[field_name].isin([Parameter(", ".join(["?"] * len(value)))]))
            values.append(value)

    for field_name, value in {
        "orcid": orcid,
        "given_name": given_name,
        "family_name": family_name,
        "local_id": person_local_id,
        "local_id_by": person_local_id_by,
    }.items():
        if value:
            q = q.where(search_creator[field_name] == Parameter("?"))
            values.append(value)
    if any([orcid, given_name, family_name, person_local_id, person_local_id_by]):
        q = q.join(search_creator).on(search_single.finalized_id == search_creator.finalized_id)

    for field_name, value in {"title": title, "keywords": keywords}.items():
        if value:
            q = q.where(
                BasicCriterion(
                    Comparator.match,
                    search_fulltext[field_name],
                    search_fulltext[field_name].wrap_constant(Parameter("?")),
                )
            )
            # Search string needs to be escaped for SQLite's FTS5
            escaped_string = ""
            for word in value.split():
                escaped_string = f"{escaped_string} \"{word}\""
            values.append(escaped_string)
    if any([title, keywords]):
        q = q.join(search_fulltext).on(search_single.finalized_id == search_fulltext.finalized_id)

    has_joined_search_org = False # ugh
    for param in [
        (search_doi, doi),
        (search_subject, subjects),
        (search_org, orgs),
    ]:
        if param[1]:
            if isinstance(param[1], list):
                q = q.where(param[0].value.isin([Parameter(", ".join(["?"] * len(param[1])))]))
            else:
                q = q.where(param[0].value == Parameter("?"))
            q = q.join(param[0]).on(search_single.finalized_id == param[0].finalized_id)
            values.append(param[1])
            if param[0] == search_org:
                has_joined_search_org = True

    if genre_form or genre_form_broader:
        q = q.join(search_genre_form).on(search_single.finalized_id == search_genre_form.finalized_id)

    if genre_form:
        if isinstance(genre_form, list):
            q = q.where(search_genre_form.value.isin([Parameter(", ".join(["?"] * len(genre_form)))]))
        else:
            q = q.where(search_genre_form.value == Parameter("?"))
        values.append(genre_form)

    if genre_form_broader:
        criteria = []
        for _gf_b in genre_form_broader:
            criteria.append(search_genre_form.value.like(Parameter("?")))
        q = q.where(Criterion.any(criteria))
        values.append(list(map(lambda x: f"{x}%", genre_form_broader)))

    q_orgs = q.select(search_org.value).distinct()
    if not has_joined_search_org:
        q_orgs = q_orgs.join(search_org).on(search_org.finalized_id == search_single.finalized_id)

    q_total = q.select(fn.Count(search_single.finalized_id).distinct().as_("total"))
    q = q.select(finalized.data).distinct()
    q = q.join(finalized).on(search_single.finalized_id == finalized.id)
    if limit:
        q = q.limit(limit)

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    matching_orgs = cur.execute(str(q_orgs), list(flatten(values))).fetchall()
    matching_orgs_list = [
        {"code": d["value"], "name": INFO_API_SOURCE_ORG_MAPPING[d["value"]]["name"]} for d in matching_orgs
    ]
    matching_orgs_list.sort(key=lambda k: k["name"])

    total_docs = cur.execute(str(q_total), list(flatten(values))).fetchone()["total"]
    fields = query_data.get("fields", [])
    if fields is None:
        fields = []
    handled_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Results are streamed to the client so we're not bothered by limits
    def get_results():
        if export_as_csv:
            yield f"# Swepub bibliometric export. Query handled at {handled_at}. Query parameters: {query_data}\n"
        else:
            yield f'{{"hits": ['

        total = 0
        output = ""
        for row in cur.execute(str(q), list(flatten(values))):
            (result, build_errors) = bibliometrics.build_result(row, fields)
            if export_as_csv:
                output = f"{output}{bibliometrics_csv_export(result, fields, csv_flavor, total)}"
            else:
                maybe_comma = "," if total > 0 else ""
                output = f"{output}{maybe_comma}{json.dumps(result)}"
            total += 1
            if total % 256 == 0:
                yield output
                output = ""
        yield output

        if not export_as_csv:
            yield "],"
            if from_yr and to_yr:
                yield f'"from": {from_yr},'
                yield f'"to": {to_yr},'
            yield (
                f'"query": {json.dumps(query_data)},'
                f'"query_handled_at": "{handled_at}",'
                f'"matching_orgs": {json.dumps(matching_orgs_list)},'
                f'"total": {total_docs}'
                "}"
            )

    return app.response_class(stream_with_context(get_results()), mimetype=export_mimetype)


@app.route("/api/v1/bibliometrics/publications/<path:record_id>", methods=["GET"])
@app.route("/api/v2/bibliometrics/publications/<path:record_id>", methods=["GET"])
def bibliometrics_get_record(record_id):
    if record_id is None:
        _errors(['Missing parameter: "record_id"'], status_code=400)

    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM finalized WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        _errors(["Not Found"], status_code=404)
    doc = json.loads(row[0])

    if request.args.get("_legacy") is not None:
        doc = LegacyPublication(doc).body_with_required_legacy_search_fields

    # TODO: Don't store the following in the actual document
    doc.pop("_publication_ids", None)
    doc.pop("_publication_orgs", None)
    return doc


#  ██████╗██╗      █████╗ ███████╗███████╗██╗███████╗██╗   ██╗
# ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
# ██║     ██║     ███████║███████╗███████╗██║█████╗   ╚████╔╝
# ██║     ██║     ██╔══██║╚════██║╚════██║██║██╔══╝    ╚██╔╝
# ╚██████╗███████╗██║  ██║███████║███████║██║██║        ██║
#  ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝        ╚═╝


@app.route("/api/v1/classify", methods=["POST"], strict_slashes=False)
@app.route("/api/v2/classify", methods=["POST"], strict_slashes=False)
def classify():
    if request.content_type != "application/json":
        _errors('Content-Type must be "application/json"')

    data = request.json
    abstract = str(data.get("abstract", ""))[:5000]
    classes = data.get("classes", 5)
    level = data.get("level", 3)
    title = str(data.get("title", ""))[:1000]
    keywords = str(data.get("keywords", ""))[:500]

    try:
        classes = int(classes)
        level = int(level)
    except ValueError:
        _errors("Parameters 'classes' and 'level' must be integers")
    if level not in [1, 3, 5]:
        _errors("Parameter 'level' must be either 1, 3 or 5")
    if classes < 1:
        _errors("Parameter 'classes' must be larger than 0")

    annif_input = f"{title} {abstract} {keywords}"

    predicted_lang, lang_score = lang_detector(annif_input, lang=("sv", "en"))[0]
    if predicted_lang == "sv":
        annif_url = ANNIF_SV_URL
    else:
        annif_url = ANNIF_EN_URL

    try:
        r = requests.post(
                f"{annif_url}/suggest",
                data={
                    "text": annif_input,
                    "limit": 20,
                    "threshold": 0.1,
                },
            )
        results = r.json()["results"]
    except Exception as e:
        _errors(["Classify backend unavailable"], status_code=500)

    subjects = []
    if len(results) > 0:
        for d in results:
            code = d["uri"].split("/")[-1]
            if len(code) != level:
                continue
            subjects.append((code, round(d["score"], 2)))

    if len(subjects) > 0:
        status = "match"
    else:
        status = "no match"

    suggestions = [dict(embellish({"@id": f"https://id.kb.se/term/ssif/{code}"}, ["broader"]), **{"_score": score}) for code, score in subjects[:5]]

    return {
        "abstract": abstract,
        "status": status,
        "suggestions": suggestions,
    }


# ██████╗  █████╗ ████████╗ █████╗ ███████╗████████╗ █████╗ ████████╗██╗   ██╗███████╗
# ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██║   ██║██╔════╝
# ██║  ██║███████║   ██║   ███████║███████╗   ██║   ███████║   ██║   ██║   ██║███████╗
# ██║  ██║██╔══██║   ██║   ██╔══██║╚════██║   ██║   ██╔══██║   ██║   ██║   ██║╚════██║
# ██████╔╝██║  ██║   ██║   ██║  ██║███████║   ██║   ██║  ██║   ██║   ╚██████╔╝███████║
# ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝


@app.route("/api/v1/datastatus", methods=["GET"], strict_slashes=False)
@app.route("/api/v2/datastatus", methods=["GET"], strict_slashes=False)
def datastatus():
    return datastatus_source(source=None)


@app.route("/api/v1/datastatus/<source>", methods=["GET"], strict_slashes=False)
@app.route("/api/v2/datastatus/<source>", methods=["GET"], strict_slashes=False)
@check_from_to
def datastatus_source(source):
    stats_converted = Table("stats_converted")
    values = []
    result = {}

    q = (
        Query.select(
            stats_converted.source,
            fn.Sum(stats_converted.total).as_("total_docs"),
            fn.Sum(stats_converted.open_access).as_("open_access"),
            fn.Sum(stats_converted.has_ssif_1).as_("ssif"),
            fn.Sum(stats_converted.swedishlist).as_("swedishlist"),
        )
        .from_(stats_converted)
        .groupby(stats_converted.source)
    )

    q_total = Query.select(fn.Sum(stats_converted.total).as_("total_docs")).from_(stats_converted)

    if g.from_yr and g.to_yr:
        result.update({"from": g.from_yr, "to": g.to_yr})
        q_total = q_total.where(
            (stats_converted.date >= Parameter("?")) & (stats_converted.date <= Parameter("?"))
        )
        q = q.where(
            (stats_converted.date >= Parameter("?")) & (stats_converted.date <= Parameter("?"))
        )
        values.append([g.from_yr, g.to_yr])

    if source:
        result["source"] = source
        q_total = q_total.where(stats_converted.source == Parameter("?"))
        q = q.where(stats_converted.source == Parameter("?"))
        values.append(source)

    values = list(flatten(values))
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    total_docs = cur.execute(str(q_total), values).fetchone()["total_docs"]
    rows = cur.execute(str(q), values).fetchall()

    total_docs = sum(filter(None, [item["total_docs"] for item in rows]))
    total_open_access = sum(filter(None, [item["open_access"] for item in rows]))
    total_ssif = sum(filter(None, [item["ssif"] for item in rows]))
    total_swedishlist = sum(filter(None, [item["swedishlist"] for item in rows]))

    result.update(
        {
            "total": total_docs,
            "openAccess": {
                "percentage": get_percentage(total_open_access, total_docs),
                "total": total_open_access,
            },
            "ssif": {"percentage": get_percentage(total_ssif, total_docs), "total": total_ssif},
            "swedishList": {
                "percentage": get_percentage(total_swedishlist, total_docs),
                "total": total_swedishlist,
            },
        }
    )

    if not source:
        result["sources"] = {}
        for row in rows:
            result["sources"][row["source"]] = {
                "percentage": get_percentage(row["total_docs"], total_docs),
                "total": row["total_docs"],
            }
    return result


@app.route("/api/v1/datastatus/ssif")
@app.route("/api/v2/datastatus/ssif")
def datastatus_ssif_endpoint():
    return datastatus_ssif_source_api(None)


@app.route("/api/v1/datastatus/ssif/<source>")
@app.route("/api/v2/datastatus/ssif/<source>")
@check_from_to
def datastatus_ssif_source_api(source=None):
    stats_ssif_1, stats_converted = Tables("stats_ssif_1", "stats_converted")
    values = []
    result = {"ssif": {}}

    q = (
        Query.select(
            stats_ssif_1.ssif_1,
            fn.Sum(stats_ssif_1.total).as_("total"),
        )
        .from_(stats_ssif_1)
        .groupby(stats_ssif_1.ssif_1)
    )

    q_total = Query.select(fn.Sum(stats_converted.total).as_("total_docs")).from_(stats_converted)

    if g.from_yr and g.to_yr:
        result.update({"from": g.from_yr, "to": g.to_yr})
        q = q.where((stats_ssif_1.date >= Parameter("?")) & (stats_ssif_1.date <= Parameter("?")))
        q_total = q_total.where(
            (stats_converted.date >= Parameter("?")) & (stats_converted.date <= Parameter("?"))
        )
        values.append([g.from_yr, g.to_yr])

    if source:
        result["source"] = source
        q = q.where(stats_ssif_1.source == Parameter("?"))
        q_total = q_total.where(stats_converted.source == Parameter("?"))
        values.append(source)

    values = list(flatten(values))
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    result["total"] = cur.execute(str(q_total), values).fetchone()["total_docs"]

    for row in cur.execute(str(q), values):
        if row["ssif_1"]:
            ssif_label = SSIF_LABELS[row["ssif_1"]]
            result["ssif"][ssif_label] = {
                "total": row["total"],
                "percentage": get_percentage(row["total"], result["total"]),
            }
    return result


@app.route("/api/v1/datastatus/validations", methods=["GET"])
@app.route("/api/v2/datastatus/validations", methods=["GET"])
def datastatus_validations():
    return datastatus_validations_source(source=None)


@app.route("/api/v1/datastatus/validations/<source>", methods=["GET"])
@app.route("/api/v2/datastatus/validations/<source>", methods=["GET"])
@check_from_to
def datastatus_validations_source(source=None):
    stats_field_events = Table("stats_field_events")

    values = []
    q = (
        Query.select(
            stats_field_events.field_name,
            fn.Sum(stats_field_events.v_invalid).as_("sum"),
        )
        .from_(stats_field_events)
        .groupby(stats_field_events.field_name)
    )

    if source:
        q = q.where(stats_field_events.source == Parameter("?"))
        values.append(source)

    if g.from_yr and g.to_yr:
        q = q.where(
            (stats_field_events.date >= Parameter("?"))
            & (stats_field_events.date <= Parameter("?"))
        )
        values.append([g.from_yr, g.to_yr])

    cur = get_db().cursor()
    cur.row_factory = dict_factory
    rows = cur.execute(str(q), list(flatten(values))).fetchall()

    total = sum(row["sum"] for row in rows)
    result = {"total": total, "validationFlags": {}}

    for row in rows:
        if total:
            percentage = round((row["sum"] / total) * 100, 2)
        else:
            percentage = 0

        result["validationFlags"][row["field_name"]] = {
            "percentage": percentage,
            "total": row["sum"],
        }

    if source:
        result["source"] = source

    if g.from_yr and g.to_yr:
        result["from"] = g.from_yr
        result["to_yr"] = g.to_yr

    return result


# ██╗███╗   ██╗███████╗ ██████╗
# ██║████╗  ██║██╔════╝██╔═══██╗
# ██║██╔██╗ ██║█████╗  ██║   ██║
# ██║██║╚██╗██║██╔══╝  ██║   ██║
# ██║██║ ╚████║██║     ╚██████╔╝
# ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝


@app.route("/api/v1/info/research-subjects", methods=["GET"])
@app.route("/api/v2/info/research-subjects", methods=["GET"])
def info_research_subjects():
    return jsonify(SSIF_TREE)


@app.route("/api/v1/info/output-types", methods=["GET"])
@app.route("/api/v2/info/output-types", methods=["GET"])
def info_output_types():
    return jsonify(INFO_API_OUTPUT_TYPES)


@app.route("/api/v1/info/sources", methods=["GET"])
@app.route("/api/v2/info/sources", methods=["GET"])
def info_sources():
    cur = get_db().cursor()
    cur.row_factory = lambda cursor, row: row[0]
    codes = cur.execute("SELECT DISTINCT source FROM harvest_history").fetchall()
    sources = []
    for code in codes:
        sources.append({"name": INFO_API_SOURCE_ORG_MAPPING[code]["name"], "code": code})
    return {"sources": sources}


# ██████╗ ██████╗  ██████╗  ██████╗███████╗███████╗███████╗
# ██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝██╔════╝
# ██████╔╝██████╔╝██║   ██║██║     █████╗  ███████╗███████╗
# ██╔═══╝ ██╔══██╗██║   ██║██║     ██╔══╝  ╚════██║╚════██║
# ██║     ██║  ██║╚██████╔╝╚██████╗███████╗███████║███████║
# ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚══════╝╚══════╝


@app.route("/api/v1/process/publications/<path:record_id>", methods=["GET"])
@app.route("/api/v2/process/publications/<path:record_id>", methods=["GET"])
def process_get_publication(record_id=None):
    if record_id is None:
        _errors(['Missing parameter: "record_id"'], status_code=400)

    cur = get_db().cursor()
    row = cur.execute(
        "SELECT data, modified FROM converted WHERE oai_id = ? AND deleted = 0", [record_id]
    ).fetchone()
    if not row:
        _errors(["Not Found"], status_code=404)
    data = json.loads(row[0])
    if request.args.get("_legacy") is not None:
        data = LegacyPublication(data).body_with_required_legacy_search_fields
    if request.args.get("_debug") is not None:
        data["meta"]["_harvest_time"] = datetime.fromtimestamp(row[1]).isoformat()
    return Response(json.dumps(data), mimetype="application/ld+json")


@app.route("/api/v1/process/publications/<path:record_id>/original", methods=["GET"])
@app.route("/api/v2/process/publications/<path:record_id>/original", methods=["GET"])
def process_get_original_publication(record_id=None):
    if record_id is None:
        _errors(['Missing parameter: "record_id"'], status_code=400)

    cur = get_db().cursor()
    row = cur.execute("SELECT data FROM original WHERE oai_id = ?", [record_id]).fetchone()
    if not row:
        _errors(["Not Found"], status_code=404)
    return Response(row[0], mimetype="application/xml; charset=utf-8")


@app.route("/api/v1/process/<source>/status")
@app.route("/api/v2/process/<source>/status")
def process_get_harvest_status(source):
    cur = get_db().cursor()
    cur.row_factory = dict_factory

    row = cur.execute(
        """
    SELECT id, harvest_start AS start, harvest_completed AS completed, harvest_succeeded, successes, rejected, deleted, failures
    FROM harvest_history
    WHERE source = ?
    ORDER BY harvest_completed DESC
    LIMIT 1
    """,
        (source,),
    ).fetchone()
    if not row:
        _errors(["Not Found"], status_code=404)

    # Some of these properties are no longer relevant after the redux rewrite,
    # and are only present here for legacy reasons
    result = {
        "deleted_so_far": row["deleted"],
        "failures": row["failures"],
        "harvest_id": row["id"],
        "harvest_retries": 0,
        "indexed_so_far": row["successes"],
        "prevented": 0,
        "rejected": row["rejected"],
        "source_code": source,
        "source_name": INFO_API_SOURCE_ORG_MAPPING[source]["name"],
        "start_timestamp": row["start"],
        "successes": row["successes"],
    }

    if row["harvest_succeeded"]:
        result["completed_timestamp"] = row["completed"]
        result["failed_sets"] = 0
    else:
        result["failed_timestamp"] = row["completed"]
        result["failed_sets"] = 1
    return result


@app.route("/api/v1/process/<source>/status/history")
@app.route("/api/v2/process/<source>/status/history")
def process_get_harvest_status_history(source):
    result = {
        "harvest_history": [],
        "source_code": source,
        "source_name": INFO_API_SOURCE_ORG_MAPPING[source]["name"],
    }

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    for row in cur.execute(
        """
        SELECT id, harvest_start, harvest_completed, harvest_succeeded, successes, rejected
        FROM harvest_history
        WHERE source = ?
        ORDER BY harvest_completed DESC
    """,
        (source,),
    ):
        history_record = {
            "harvest_id": row["id"],
            "rejected": row["rejected"],
            "successes": row["successes"],
            "start_timestamp": row["harvest_start"],
        }
        if row["harvest_succeeded"]:
            history_record["completed_timestamp"] = row["harvest_completed"]
        else:
            history_record["failed_timestamp"] = row["harvest_completed"]
        result["harvest_history"].append(history_record)

    oldest_harvest = cur.execute(
        "SELECT MIN(harvest_start) AS oldest FROM harvest_history WHERE source = ?",
        (source,),
    ).fetchone()["oldest"]
    latest_harvest = cur.execute(
        "SELECT MAX(harvest_start) AS latest FROM harvest_history WHERE source = ?",
        (source,),
    ).fetchone()["latest"]

    result["harvests_from"] = oldest_harvest
    result["harvests_to"] = latest_harvest

    return result


@app.route("/api/v1/process/<harvest_id>/rejected")
@app.route("/api/v2/process/<harvest_id>/rejected")
def process_get_rejected_publications(harvest_id):
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    (errors, limit, offset) = parse_limit_and_offset(limit, offset)
    if errors:
        _errors(errors)

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    total_rejections = cur.execute(
        "SELECT COUNT(*) AS total FROM rejected WHERE harvest_id = ?", (harvest_id,)
    ).fetchone()["total"]
    if not total_rejections:
        _errors(["Not found"], status_code=404)

    source = cur.execute(
        "SELECT source FROM harvest_history WHERE id = ? LIMIT 1", (harvest_id,)
    ).fetchone()["source"]

    rejected = Table("rejected")

    q = (
        Query.select(rejected.oai_id, rejected.rejection_cause)
        .from_(rejected)
        .where(rejected.harvest_id == Parameter("?"))
        .orderby("id")
    )

    if limit:
        q = q.limit(limit)
    if offset:
        q = q.offset(offset)

    result = {
        "harvest_id": harvest_id,
        "rejected_publications": [],
        "source_code": source,
        "source_name": INFO_API_SOURCE_ORG_MAPPING[source]["name"],
        "total": total_rejections,
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

        result["rejected_publications"].append({"record_id": row["oai_id"], "errors": error_list})

    resp = make_response(jsonify(result))

    (prev_page, next_page) = process_get_pagination_links(
        request,
        url_for("process_get_rejected_publications", harvest_id=harvest_id),
        limit,
        offset,
        total_rejections,
    )
    if prev_page:
        resp.headers.add("Link", f"<{prev_page}>", rel="prev")
    if next_page:
        resp.headers.add("Link", f"<{next_page}>", rel="next")

    return resp


@app.route("/api/v1/process/<source>", methods=["GET"])
@app.route("/api/v2/process/<source>", methods=["GET"])
@check_from_to
def process_get_stats(source=None):
    audit_labels_to_include = [
        "ISSN_missing_check",
        "SSIF_comprehensive_check",
        "contributor_duplicate_check",
        "creator_count_check",
    ]

    result = {
        "code": source,
        "source": INFO_API_SOURCE_ORG_MAPPING[source]["name"],
        "audits": {},
        "enrichments": {},
        "normalizations": {},
        "validations": {},
        "total": 0,
    }

    if g.from_yr and g.to_yr:
        date_sql = f" AND date >= ? AND date <= ?"
        values = [source, g.from_yr, g.to_yr]
    else:
        date_sql = ""
        values = [source]

    cur = get_db().cursor()
    cur.row_factory = dict_factory

    result["total"] = cur.execute(
        "SELECT SUM(total) AS total_docs FROM stats_converted WHERE source = ?", [source]
    ).fetchone()["total_docs"]

    for row in cur.execute(
        f"""
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
            """,
        values,
    ):
        # Autoclassified is a bit of a special case. It's technically an auditor but should here
        # be counted as an enricher. "valid" means "enriched"; we don't actually log "not enriched"
        # for the autoclassifier, so we just subtract the number of enriched from the total.
        if row["label"] in ENRICHING_AUDITORS_CODES:
            result["enrichments"][row["label"]] = {}
            result["enrichments"][row["label"]]["enriched"] = row["valid"]
            result["enrichments"][row["label"]]["unchanged"] = result["total"] - row["valid"]
            continue
        if row["label"] not in audit_labels_to_include:
            continue

        result["audits"][row["label"]] = {}
        if row["valid"]:
            result["audits"][row["label"]]["valid"] = row["valid"]
        if row["invalid"]:
            result["audits"][row["label"]]["invalid"] = row["invalid"]

    for row in cur.execute(
        f"""
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
    """,
        values,
    ):
        result["enrichments"][row["field_name"]] = {}
        result["normalizations"][row["field_name"]] = {}
        result["validations"][row["field_name"]] = {}

        if row["e_enriched"]:
            result["enrichments"][row["field_name"]]["enriched"] = row["e_enriched"]
        if row["e_unchanged"]:
            result["enrichments"][row["field_name"]]["unchanged"] = row["e_unchanged"]
        if row["e_unsuccessful"]:
            result["enrichments"][row["field_name"]]["unsuccessful"] = row["e_unsuccessful"]

        if row["n_unchanged"]:
            result["normalizations"][row["field_name"]]["unchanged"] = row["n_unchanged"]
        if row["n_normalized"]:
            result["normalizations"][row["field_name"]]["normalized"] = row["n_normalized"]

        if row["v_valid"]:
            result["validations"][row["field_name"]]["valid"] = row["v_valid"]
        if row["v_invalid"]:
            result["validations"][row["field_name"]]["invalid"] = row["v_invalid"]

    return result


@app.route("/api/v1/process/<source>/export", methods=["GET"])
@app.route("/api/v2/process/<source>/export", methods=["GET"])
@check_from_to
def process_get_export(source=None):
    export_as_csv, export_mimetype, csv_flavor = export_options(request)
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    (errors, limit, offset) = parse_limit_and_offset(limit, offset)
    if errors:
        _errors(errors)
    validation_flags = request.args.get("validation_flags")
    enrichment_flags = request.args.get("enrichment_flags")
    normalization_flags = request.args.get("normalization_flags")
    audit_flags = request.args.get("audit_flags")
    (errors, selected_flags) = parse_flags(
        validation_flags, enrichment_flags, normalization_flags, audit_flags
    )
    if errors:
        _errors(errors)

    converted, converted_record_info, converted_audit_events = Tables(
        "converted", "converted_record_info", "converted_audit_events"
    )
    values = []
    q = (
        Query
        .from_(converted)
        .left_join(converted_record_info).on(converted.id == converted_record_info.converted_id)
        .where(converted_record_info.source == Parameter("?"))
    )
    values.append(source)

    if g.from_yr and g.to_yr:
        q = q.where((converted_record_info.date >= Parameter("?")) & (converted_record_info.date <= Parameter("?")))
        values.append([g.from_yr, g.to_yr])

    # Specified flags should be OR'd together, so we build up a list of criteria and use
    # pypika's Criterion.any.
    criteria = []
    for flag_type, flags in selected_flags.items():
        for flag_name, flag_values in flags.items():
            if flag_type in ["validation", "enrichment", "normalization"] and flag_name not in ENRICHING_AUDITORS_CODES:
                for flag_value in flag_values:
                    criteria.append(
                        (converted_record_info.field_name == Parameter("?"))
                        & (converted_record_info[f"{flag_type}_status"] == Parameter("?"))
                    )
                    if flag_type == "enrichment":
                        flag_value = int(Enrichment[flag_value.upper()])
                    if flag_type == "normalization":
                        flag_value = int(Normalization[flag_value.upper()])
                    if flag_type == "validation":
                        flag_value = int(Validation[flag_value.upper()])

                    values.append([flag_name, flag_value])
            if flag_type == "audit" or flag_name in ENRICHING_AUDITORS_CODES:
                for flag_value in flag_values:
                    criteria.append(
                        (converted_record_info.audit_code == Parameter("?"))
                        & (converted_record_info.audit_result == Parameter("?"))
                    )
                    # TODO: Fix horrible "valid"/"invalid" 0/1 confusion
                    if flag_value == "valid" or (
                        flag_name == "creator_count_check" and flag_value == "invalid"
                    ):
                        int_flag_value = 0
                    else:
                        int_flag_value = 1
                    values.append([flag_name, int_flag_value])
    q = q.where(Criterion.any(criteria))

    q_total = q.select(fn.Count(converted.id).distinct().as_("total"))

    sub_q = (
        q.select(converted.id)
        .distinct()
    )

    q = (
        Query.from_(converted)
        .select(converted.id, converted.date, converted.data, converted.events, converted.oai_id)
        .where(converted.id.isin(sub_q))
    )

    if limit:
        q = q.limit(limit)
    if offset:
        q = q.offset(offset)

    handled_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    cur = get_db().cursor()
    cur.row_factory = dict_factory
    total_docs = cur.execute(str(q_total), list(flatten(values))).fetchone()["total"]

    def get_results():
        # Exports can be large and we don't want to load everything into memory, so we stream
        # the output (each yield is sent directly to the client).
        # Since we send one result at a time, we can't send a ready-made dict when JSON is selected.
        if export_as_csv:
            yield f"# Swepub data processing export. Query handled at {handled_at}. Query parameters: {request.args.to_dict()}\n"
        else:
            yield f'{{"code": "{source}",' f'"hits": ['
        total = 0
        output = ""
        for row in cur.execute(str(q), list(flatten(values))):
            flask_url = url_for("process_get_original_publication", record_id=row["oai_id"])
            base_url, _parts = get_base_url(request)
            mods_url = f"{base_url}{flask_url}"
            export_result = build_export_result(
                orjson.loads(row["data"]),
                orjson.loads(row["events"]),
                selected_flags,
                row["oai_id"],
                mods_url,
            )

            if export_as_csv:
                csv_result = process_csv_export(
                    export_result,
                    csv_flavor,
                    request.args.to_dict(),
                    handled_at,
                    total_docs,
                )
                output = f"{output}{csv_result}"
            else:
                maybe_comma = "," if total > 0 else ""
                output = f"{output}{maybe_comma}{json.dumps(export_result)}"
            total += 1
            if total % 256 == 0:
                yield output
                output = ""
        yield output
        if not export_as_csv:
            yield "],"
            if g.from_yr and g.to_yr:
                yield f'"from": {g.from_yr},'
                yield f'"to": {g.to_yr},'
            yield (
                f'"query": {json.dumps(request.args)},'
                f'"query_handled_at": "{handled_at}",'
                f'"source": "{INFO_API_SOURCE_ORG_MAPPING[source]["name"]}",'
                f'"total": {total_docs}'
                "}"
            )

    resp = app.response_class(stream_with_context(get_results()), mimetype=export_mimetype)

    (prev_page, next_page) = process_get_pagination_links(
        request,
        url_for("process_get_export", source=source),
        limit,
        offset,
        total_docs,
    )
    if prev_page:
        resp.headers.add("Link", f"<{prev_page}>", rel="prev")
    if next_page:
        resp.headers.add("Link", f"<{next_page}>", rel="next")

    return resp


# ███╗   ███╗██╗███████╗ ██████╗
# ████╗ ████║██║██╔════╝██╔════╝
# ██╔████╔██║██║███████╗██║
# ██║╚██╔╝██║██║╚════██║██║
# ██║ ╚═╝ ██║██║███████║╚██████╗██╗
# ╚═╝     ╚═╝╚═╝╚══════╝ ╚═════╝╚═╝


@app.route("/api/v2/apidocs", methods=["GET"], strict_slashes=False)
def api_docs():
    return send_from_directory(app.root_path, "apidocs/index.html")


@app.route("/apidocs/<path:filename>")
def custom_static(filename):
    return send_from_directory(app.root_path + "/apidocs/", filename)


@app.route("/xsleditor", methods=["GET", "POST"], strict_slashes=False)
def xsl_editor():
    if request.method == "POST":
        xslt = request.form.get("xslt", "")
        mods = request.form.get("mods", "")

        f = NamedTemporaryFile(mode="w")
        f.write(xslt)
        f.flush()

        result = {"publication": {}, "errors": []}
        try:
            result["publication"] = ModsParser().parse_mods(mods, encode_ampersand=True)
        except LxmlError as e:
            result["errors"] = [{"message": str(e)}]
        f.close()

        return jsonify(
            {
                "result": re.sub(
                    r"(\\u[0-9A-Fa-f]{1,4})",
                    unescape_match,
                    json.dumps(result["publication"], indent=4),
                ),
                "error": re.sub(
                    r"(\\u[0-9A-Fa-f]{1,4})", unescape_match, json.dumps(result["errors"], indent=4)
                ),
            }
        )
    else:
        return render_template("xsleditor.html", default_xslt=DEFAULT_XSLT)


if __name__ == "__main__":
    port = getenv("SWEPUB_SERVICE_PORT", 5000)
    app.run(port=int(port))
