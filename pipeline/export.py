from os import path
from argparse import ArgumentParser

import json
import orjson

from pipeline.storage import get_connection, dict_factory

FILE_PATH = path.dirname(path.abspath(__file__))
DEFAULT_SWEPUB_DB = path.join(FILE_PATH, "../swepub.sqlite3")

def handle_args():
    parser = ArgumentParser()
    parser.add_argument("--year", default=None)
    # deduplicated/deduplicated rather than finalized/converted for "legacy" reasons...
    parser.add_argument("table", choices=["deduplicated", "duplicated"])

    return parser.parse_args()


def dump_deduplicated(year=None):
    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        where_sql = ""
        params = []
        if year:
            where_sql = " AND search_single.year = ? "
            params = [year]

        for row in cur.execute(f"""
            SELECT
                finalized.data AS finalized_data, group_concat(converted.data, "\n") AS converted_data
            FROM
                cluster
            LEFT JOIN
                converted ON converted.id = cluster.converted_id
            LEFT JOIN
                finalized ON cluster.cluster_id = finalized.cluster_id
            LEFT JOIN
                search_single ON search_single.finalized_id = finalized.id
            WHERE
                deleted = 0
            {where_sql}
            GROUP BY
                cluster.cluster_id
        """, params):

            finalized = orjson.loads(row["finalized_data"])
            # TODO: Don't store the following in the actual document
            finalized.pop("_publication_ids", None)
            finalized.pop("_publication_orgs", None)

            publications = []
            for raw_publication in row["converted_data"].split('\n'):
                publications.append(orjson.loads(raw_publication))

            result = {
                "master": finalized,
                "publications": publications,
                "publication_count": len(publications)
            }

            print(json.dumps(result))


def dump_duplicated(year=None):
    with get_connection() as con:
        cur = con.cursor()
        cur.row_factory = dict_factory

        where_sql = ""
        params = []
        if year:
            where_sql = " AND date = ? "
            params = [year]

        for row in cur.execute(f"SELECT data FROM converted WHERE deleted = 0 {where_sql}", params):
            # TODO: should be able to simply print row["data"].decode("utf-8");
            # however, the type is sometimes str, sometimes bytes -- investigare why.
            if row.get("data"):
                print(json.dumps(orjson.loads(row["data"])))


if __name__ == "__main__":
    args = handle_args()

    if args.table == "duplicated":
        dump_duplicated(args.year)

    if args.table == "deduplicated":
        dump_deduplicated(args.year)
