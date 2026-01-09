import json
from pipeline.storage import get_connection

def clean(oai_id, data):
    root = json.loads(data)
    root.pop("@context", None) # Remove explicit context
    root["@id"] = f"https://swepub.kb.se/bib/swepub:{oai_id}"
    return json.dumps(root)


def generate_libris_dataset():
    with open("/tmp/swepub.jsonld.lines", "wb") as outFile:

        outFile.write("""{"@id": "https://id.kb.se/dataset/swepub", "@type": "Dataset", "label": "Swepub", "created": "2025-11-24T13:37:00Z"}""".encode('utf-8'))
        outFile.write("\n".encode('utf-8'))
        with get_connection() as connection:
            cursor = connection.cursor()
            for cluster_row in cursor.execute(
                "SELECT oai_id, data FROM finalized;"
            ):
                oai_id = cluster_row[0]
                data = cluster_row[1]
                outFile.write(clean(oai_id, data).encode('utf-8'))
                outFile.write("\n".encode('utf-8'))

# For debugging
if __name__ == "__main__":
    generate_libris_dataset()