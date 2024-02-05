import json
from pathlib import Path
import re

from lxml.etree import LxmlError

from pipeline.convert import ModsParser


def process(xslt_path, mods_path):
    xslt = Path(xslt_path).read_text()
    mods = Path(mods_path).read_text()

    result = {"publication": {}, "errors": []}
    try:
        result["publication"] = ModsParser().parse_mods(mods, encode_ampersand=True)
    except LxmlError as e:
        result["errors"] = [{"message": str(e)}]

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(f"Usage: in swepub-redux: python3 -m misc.mods_to_json <path-to-xsl> <path-record-in-MODS-xml>")
        sys.exit(1)

    result = process(sys.argv[1], sys.argv[2])

    print(json.dumps({"result": result["publication"], "error": result["errors"]}, indent=4))
