import json
from os import sys
from pathlib import Path
import re

from flask import jsonify

from pipeline.convert import ModsParser


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: in swepub-redux: python3 -m misc.mods_to_json <path-to-xsl> <path-record-in-MODS-xml>")
        sys.exit(1)

    xslt = Path(sys.argv[1]).read_text()
    mods = Path(sys.argv[2]).read_text()

    result = {"publication": {}, "errors": []}
    try:
        result["publication"] = ModsParser().parse_mods(mods, encode_ampersand=True)
    except LxmlError as e:
        result["errors"] = [{"message": str(e)}]

    print(json.dumps({"result": result["publication"], "error": result["errors"]}, indent=4))
