import json
import os
from argparse import ArgumentParser
from pathlib import Path

import psutil
from pathvalidate import sanitize_filename
import time

from concurrent.futures import ProcessPoolExecutor
import sys
import traceback
import lxml.etree as etree
import io

import pipeline.sickle as sickle
from pipeline.oai import RecordIterator
from pipeline.swepublog import logger as log

DEFAULT_SWEPUB_ENV = os.getenv("SWEPUB_ENV", "DEV")  # or QA, PROD
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SWEPUB_SOURCE_FILE = os.path.join(FILE_PATH, "../resources/sources.json")
SWEPUB_USER_AGENT = os.getenv(
    "SWEPUB_USER_AGENT", "https://github.com/libris/swepub-redux"
)


def fetch(source):
    start_time = time.time()
    count = 0
    for source_set in source["sets"]:
        path = Path(f"{os.getenv('SWEPUB_FETCH_OUTPUT_DIRECTORY')}/{source['code']}")
        path.mkdir(mode=0o755, parents=True, exist_ok=True)
        harvest_info = f'{source_set["url"]} ({source_set["subset"]}, {source_set["metadata_prefix"]})'
        log.info(f"[{source['code']}]\t START fetch: {harvest_info}")

        record_iterator = RecordIterator(source["code"], source_set, None, None,
                                         SWEPUB_USER_AGENT, False)

        try:
            for record in record_iterator:
                if record.is_successful():
                    file_path = path / f"{sanitize_filename(record.oai_id)}.xml"
                    with file_path.open("w") as f:
                        f.write(record.xml)
                    count += 1
        except Exception as e:
            log.info(f"[{source['code']}]\t FAILED fetch, error: {e}")
            log.warning(traceback.format_exc())
            return
    finish_time = time.time()
    log.info(
        f"[{source['code']}]\t FINISHED fetch in {finish_time - start_time} seconds. {count} records, {round(count / (finish_time - start_time), 2)} records/s"
    )


def _fetch_sources(sources_to_process):
    log.info("Fetching " + " ".join([source["code"] for source in sources_to_process]))
    t0 = time.time()
    max_workers = max(psutil.cpu_count(logical=True) * 2, 8)
    with ProcessPoolExecutor(
        max_workers, initializer=init, initargs=(log,)
    ) as executor:
        for source in sources_to_process:
            executor.submit(fetch, source)
        executor.shutdown(wait=True)

    t1 = time.time()
    diff = t1 - t0
    log.info(f"Fetch completed in {diff} seconds")


def _fetch_individual_records(oai_ids, sources):
    codes = set()
    count = 0
    for oai_id in oai_ids:
        log.info(f"Fetching {oai_id}")
        # Quick and dirty way to figure out institution code from OAI ID
        if oai_id.lower().startswith("oai:diva.org"):
            code = oai_id.split(":")[2].split("-")[0]
        else:
            code = oai_id.split(":")[1].split(".")[-2]
        if code == "chalmers":
            code = "cth"
        codes.add(code)
        source_set = sources[code]["sets"][0]
        get_record_params = {
            "identifier": oai_id,
            "metadataPrefix": source_set["metadata_prefix"],
        }
        sickle_client = sickle.Sickle(source_set["url"], max_retries=8, timeout=90, headers={"User-Agent": SWEPUB_USER_AGENT})
        try:
            path = Path(f"{os.getenv('SWEPUB_FETCH_OUTPUT_DIRECTORY')}/{code}")
            path.mkdir(mode=0o755, parents=True, exist_ok=True)
            record = sickle_client.GetRecord(**get_record_params)
            file_path = path / f"{sanitize_filename(record.header.identifier)}.xml"
            with file_path.open("w") as f:
                parsed_xml = etree.parse(io.StringIO(record.raw))
                f.write(etree.tostring(parsed_xml, pretty_print=True).decode("utf-8"))
            count += 1
        except Exception as e:
            log.warning(f"FAILED retching record {oai_id}: {e}")
            log.warning(traceback.format_exc())
    log.info(f"Fetched {count} records from {' '.join(list(codes))}")
    print("Now you might want to do this (DEV ENVIRONMENT ONLY!):")
    print("python3 -m misc.oai_pmh_server # in a different terminal")
    print(f"python3 -m pipeline.harvest -f {' '.join(list(codes))} --local-server")

def handle_args():
    parser = ArgumentParser()

    parser.add_argument(
        "-e",
        "--env",
        default=None,
        help="One of DEV, QA, PROD (default DEV). Overrides SWEPUB_ENV.",
    )
    parser.add_argument(
        "-s",
        "--source-file",
        default=None,
        help="Source file to use. Overrides SWEPUB_SOURCE_FILE.",
    )
    parser.add_argument(
        "source",
        nargs="*",
        default="",
        help="Source(s) to process (if not specified, everything in the source will be processed).",
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="./_xml",
        help="Directory to write results to.",
    )

    return parser.parse_args()


def init(lg):
    global log
    log = lg


if __name__ == "__main__":
    args = handle_args()

    if args.env:
        os.environ["SWEPUB_ENV"] = args.env
    elif not os.getenv("SWEPUB_ENV", None):
        os.environ["SWEPUB_ENV"] = DEFAULT_SWEPUB_ENV

    if args.source_file:
        os.environ["SWEPUB_SOURCE_FILE"] = args.source_file
    elif not os.getenv("SWEPUB_SOURCE_FILE", None):
        os.environ["SWEPUB_SOURCE_FILE"] = DEFAULT_SWEPUB_SOURCE_FILE

    os.environ["SWEPUB_FETCH_OUTPUT_DIRECTORY"] = args.directory
    log.info(f"SWEPUB_ENV is {os.environ['SWEPUB_ENV']}")

    sources = json.load(open(os.environ["SWEPUB_SOURCE_FILE"]))

    if args.source and args.source[0].startswith("oai:"):
        _fetch_individual_records(args.source, sources)
    else:
        sources_to_process = []
        if args.source:
            for code in args.source:
                if code not in sources:
                    log.error(
                        f"Source {code} does not exist in {os.environ['SWEPUB_SOURCE_FILE']}"
                    )
                    sys.exit(1)
                # Some sources should have different URIs/settings for different environments
                sources[code]["sets"][:] = [
                    item
                    for item in sources[code]["sets"]
                    if os.getenv("SWEPUB_ENV") in item.get("envs", []) or "envs" not in item
                ]
                sources_to_process.append(sources[code])
        else:
            for source in sources.values():
                source["sets"][:] = [
                    item
                    for item in source["sets"]
                    if os.getenv("SWEPUB_ENV") in item.get("envs", []) or "envs" not in item
                ]
                sources_to_process.append(source)
        _fetch_sources(sources_to_process)

