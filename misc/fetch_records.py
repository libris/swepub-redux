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
