#!/usr/bin/env python3

from flask import Flask, request, send_from_directory
from os import path
import json

app = Flask(__name__)
FILE_PATH = path.dirname(path.abspath(__file__))
sources = json.load(open(path.join(FILE_PATH, "./sources_test.json")))


@app.route('/<path:r>')
def endpoint(r):
    r = request.path[1:]

    if r not in sources:
        return f"{r} not found in sources_test.json", 404, {'Content-Type': 'text/plain'}

    return send_from_directory(app.root_path + "/test_data", f"{r}.xml")


if __name__ == "__main__":
    app.run(port=8549)
