import json
from os import environ, getenv
from pipeline.storage import get_connection

DEV_SOURCES = ["kkh", "uniarts", "havochvatten", "rkh", "sh"]

def clean(oai_id, data, source_id_by_code):
    root = json.loads(data)
    root.pop("@context", None) # Remove explicit context
    root["@id"] = f"https://swepub.kb.se/bib/swepub:{oai_id}"

    orgs = root.pop("_publication_orgs", None)
    if not orgs:
        orgs = [root.get("meta", {}).get("assigner", {}).get("label")]

    derived_from = []
    for org in sorted(set(filter(None, orgs))):
        source_id = source_id_by_code.get(org)
        if source_id:
            derived_from.append({"@type": "Record", "publisher": {"@id": source_id}})
    if derived_from:
        root.setdefault("meta", {})["derivedFrom"] = derived_from

    root.pop("_publication_ids", None)

    return json.dumps(root)


def generate_libris_dataset():
    extraSql = ""

    if getenv("SWEPUB_ENV") == "DEV":
        extraSql = f"""
        WHERE EXISTS (
            SELECT 1
            FROM search_org so
            WHERE so.finalized_id = f.id
              AND so.value IN ({', '.join(f"'{x}'" for x in DEV_SOURCES)})
        )"""

    sources = _load_sources()
    source_id_by_code = {
        source["code"]: source["@id"] for source in sources
    }

    with open("/tmp/swepub.jsonld.lines", "wb") as outFile:

        outFile.write("""{"@id": "https://id.kb.se/dataset/swepub", "@type": "Dataset", "label": "Swepub", "created": "2025-11-24T13:37:00Z"}""".encode('utf-8'))
        outFile.write("\n".encode('utf-8'))
        _write_sources(sources, outFile)
        with get_connection() as connection:
            cursor = connection.cursor()
            for cluster_row in cursor.execute(
                f"SELECT oai_id, data FROM finalized f {extraSql};"
            ):
                oai_id = cluster_row[0]
                data = cluster_row[1]
                outFile.write(clean(oai_id, data, source_id_by_code).encode('utf-8'))
                outFile.write("\n".encode('utf-8'))


def _load_sources():
    from pipeline.harvest import DEFAULT_SWEPUB_SOURCE_FILE

    source_file = environ.get("SWEPUB_SOURCE_FILE", DEFAULT_SWEPUB_SOURCE_FILE)
    return json.load(open(source_file)).values()


def _write_sources(sources, out_file):
    for source in sources:
        out_file.write(json.dumps({
            "@id": source["@id"],
            "@type": "Organization",
            "code": source["code"],
            "name": source["name"],
        }).encode('utf-8'))
        out_file.write("\n".encode('utf-8'))


# For debugging
if __name__ == "__main__":
    generate_libris_dataset()