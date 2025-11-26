import json
from pipeline.storage import get_connection

def clean(data):
    root = json.loads(data)
    root.pop("@context", None) # Remove explicit context
    return json.dumps(root)


def generate_libris_dataset():
    with open("/tmp/swepub.jsonld.lines", "wb") as outFile:

        outFile.write("""{"@id": "https://id.kb.se/dataset/swepub", "@type": "Dataset", "label": "Swepub", "created": "2025-11-24T13:37:00Z"}""".encode('utf-8'))
        outFile.write("\n".encode('utf-8'))
        with get_connection() as connection:
            cursor = connection.cursor()
            for cluster_row in cursor.execute(
                "SELECT data FROM finalized;"
            ):
                data = cluster_row[0]
                outFile.write(clean(data).encode('utf-8'))
                outFile.write("\n".encode('utf-8'))

# For debugging
if __name__ == "__main__":
    generate_libris_dataset()