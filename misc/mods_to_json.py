import json
from os import path, sys
from pathlib import Path
import re

from flask import jsonify

from pipeline.convert import ModsParser

FILE_PATH = path.dirname(path.abspath(__file__))
XSLT = Path(f"{FILE_PATH}/../resources/mods_to_xjsonld.xsl").read_text()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"Usage: in swepub-redux: python3 -m misc.mods_to_json <path-record-in-MODS-xml>")
        sys.exit(1)

    mods = Path(sys.argv[1]).read_text()

    result = {"publication": {}, "errors": []}
    try:
        result["publication"] = ModsParser().parse_mods(mods, encode_ampersand=True)
    except LxmlError as e:
        result["errors"] = [{"message": str(e)}]

    print(json.dumps({"result": result["publication"], "error": result["errors"]}, indent=4))
