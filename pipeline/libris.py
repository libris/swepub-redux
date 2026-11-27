import json
from os import environ, getenv
from pipeline.storage import get_connection
from pipeline.util import SSIF_BASE

DEV_SOURCES = ["kkh", "uniarts", "havochvatten", "rkh", "sh"]

def clean(oai_id, data):
    root = json.loads(data)
    root.pop("@context", None) # Remove explicit context
    root["@id"] = f"https://swepub.kb.se/bib/swepub:{oai_id}"
    work = root.get("instanceOf")
    if isinstance(work, dict) and "classification" in work:
        work["classification"] = _ssif_to_links(work["classification"])
    return json.dumps(root)


def _is_ssif(term):
    return isinstance(term, dict) and term.get("@id", "").startswith(SSIF_BASE)


def _ssif_to_links(classifications):
    """
    Replace embedded SSIF term definitions with bare links, including every
    broader level (downstream doesn't fully follow broader). Non-SSIF terms
    are kept as is. Annotations are dropped for now.
    """
    result = []
    seen = set()
    for term in classifications:
        if not _is_ssif(term):
            result.append(term)
            continue
        current = term
        while _is_ssif(current):
            if current["@id"] not in seen:
                seen.add(current["@id"])
                result.append({"@id": current["@id"]})
            current = current.get("broader")
    return result


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
                outFile.write(clean(oai_id, data).encode('utf-8'))
                outFile.write("\n".encode('utf-8'))


def _load_sources():
    from pipeline.harvest import DEFAULT_SWEPUB_SOURCE_FILE

    source_file = environ.get("SWEPUB_SOURCE_FILE", DEFAULT_SWEPUB_SOURCE_FILE)
    return json.load(open(source_file)).values()


def _write_sources(sources, out_file):
    seen = set()
    for source in sources:
        # in tests/sources_test.json several sources can share a code (and @id)...
        if source["@id"] in seen:
            continue
        seen.add(source["@id"])
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