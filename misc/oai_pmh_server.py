import argparse
import multiprocessing
import sys
import uuid
from multiprocessing import Manager
from pathlib import Path

import gunicorn.app.base
from flask import Flask, request, stream_with_context
from datetime import datetime

app = Flask(__name__)

RESUMPTION_KEY = "resumptionToken"
RESULTS_PER_QUERY = 100


# Given a directory a directory structure created by `fetch_records.py`, this is
# the _very bare minimum_ necessary to make (non-incremental) harvesting with pipeline.harvest work.
@app.route("/oai/<divaornot>/<source>", methods=["GET"])
def oai(divaornot, source):
    global data
    global files

    oaiSet = request.args.get("set")
    metadataPrefix = request.args.get("metadataPrefix")
    resumptionToken = request.args.get("resumptionToken")

    def get_results():
        response_date = datetime.today().strftime("%Y-%m-%dT%H:%M:%SZ")
        yield f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>{response_date}</responseDate>
  <request verb="ListRecords" set="{oaiSet}" metadataPrefix="{metadataPrefix}">http://localhost:8383/oai/{source}</request>
  <ListRecords>
        """
        offset = 0
        if resumptionToken:
            offset = data[RESUMPTION_KEY][resumptionToken]

        for file in files[source][offset:offset+RESULTS_PER_QUERY]:
            with open(file, "r") as f:
                yield f.read()

        has_resumption = False
        if len(files[source]) > offset + RESULTS_PER_QUERY:
            has_resumption = True
            new_offset = offset + RESULTS_PER_QUERY
            new_token = uuid.uuid4().hex
            data[RESUMPTION_KEY][new_token] = new_offset

        if has_resumption:
            yield f"""<resumptionToken completeListSize="{len(files[source])}" cursor="{new_offset}">{new_token}</resumptionToken>"""
        yield "</ListRecords></OAI-PMH>"

    return app.response_class(stream_with_context(get_results()), mimetype="text/xml")


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def init(xml_path):
    global data
    global files
    data = {}
    manager = Manager()
    data[RESUMPTION_KEY] = manager.dict()

    if not Path(xml_path).exists() or not Path(xml_path).is_dir():
        print(f"{xml_path} does not exist or is not a directory. Exiting!")
        sys.exit(1)

    directories = [
        directory for directory in Path(xml_path).glob("*") if directory.is_dir()
    ]
    files = {}
    for directory in directories:
        files[directory.name] = [file for file in directory.glob("*") if file.is_file()]


if __name__ == "__main__":
    global data
    global files

    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", "-d", type=str, default="./_xml", help="Directory to read from, e.g. ./xml")
    parser.add_argument(
        "--workers", "-w", type=int, default=(multiprocessing.cpu_count() + 1)
    )
    parser.add_argument("--port", "-p", type=str, default="8383")
    args = parser.parse_args()

    options = {
        "bind": "%s:%s" % ("127.0.0.1", args.port),
        "workers": args.workers,
        "worker_class": "gthread",
        "keepalive": 5,
    }

    init(args.directory)
    StandaloneApplication(app, options).run()
