from collections import Counter
import re
import time
import os
from json import load
from os import path
from tempfile import TemporaryDirectory
from concurrent.futures import ProcessPoolExecutor
from functools import partial

from jsonpath_rw_ext import parse
from dateutil.parser import parse as parse_date

import orjson as json

from pipeline.storage import get_connection, checkpoint

categories = load(
    open(path.join(path.dirname(path.abspath(__file__)), "../resources/categories.json"))
)


RAW_SUMMARY_PATH = 'instanceOf.summary[?(@.@type=="Summary")]'
SUMMARY_PATH = parse(RAW_SUMMARY_PATH)

RAW_DATE_PATH = 'publication[?(@.@type=="Publication")].date'
DATE_PATH = parse(RAW_DATE_PATH)

RAW_PUBLICATION_STATUS_PATH = 'instanceOf.hasNote[?(@.@type=="PublicationStatus")].@id'
PUBLICATION_STATUS_PATH = parse(RAW_PUBLICATION_STATUS_PATH)

undesired_binary_chars_table = dict.fromkeys(map(ord, '-–_'), None)
undesired_unary_chars_table = dict.fromkeys(map(ord, ',.;:!?"\'@#$\u00a0'), ' ')

known_bad_rare_words = set()
with open(path.join(path.dirname(path.abspath(__file__)), "../resources/bad_rare_words.txt")) as f:
    for word in f.readlines():
        known_bad_rare_words.add(word.rstrip())

class Publication:
    def __init__(self, publication):
        self._publication = publication

    @property
    def data(self):
        return self._publication

    @property
    def title(self):
        titles = self._publication.get("instanceOf", {}).get("hasTitle", [])
        if titles:
            if titles[0].get("@type", "") == "Title":
                return titles[0].get("mainTitle", None)
        return None

    @property
    def subtitle(self):
        titles = self._publication.get("instanceOf", {}).get("hasTitle", [])
        if titles:
            if titles[0].get("@type", "") == "Title":
                return titles[0].get("subTitle", None)
        return None

    @property
    def keywords(self):
        subjects = self.subjects
        keywords = []
        for subj in subjects:
            if "inScheme" in subj and "code" in subj["inScheme"]:
                code = subj["inScheme"]["code"]
                if code == "hsv" or code == "uka.se":
                    continue
            if "prefLabel" in subj:
                keywords.append(subj["prefLabel"])
        return keywords

    @property
    def subjects(self):
        subjects = []
        for subject in self._publication.get("instanceOf", {}).get("subject", []):
            if subject.get("@type", "") == "Topic":
                subjects.append(subject)
        return subjects

    @property
    def subject_codes(self):
        return [subj["@id"] for subj in self.subjects if "@id" in subj]

    @property
    def uka_swe_classification_list(self):
        classification_list = []
        uka_prefix = "https://id.kb.se/term/uka/"
        swe_lang_id = "https://id.kb.se/language/swe"
        for subj in self._publication.get("instanceOf", {}).get("subject", {}):
            if subj.get("@type", "") == "Topic":
                code = subj.get("@id")
                if not code:
                    continue
                if not code.startswith(uka_prefix):
                    continue
                if subj.get("language", {}).get("@id", "") == swe_lang_id:
                    code = subj.get("code")
                    label = subj.get("prefLabel")
                    cl_string = f"{code}" if code else ""
                    cl_string += f" {label}" if label else ""
                    if cl_string:
                        classification_list.append(cl_string)
        return classification_list

    @property
    def uka_subject_codes(self):
        uka_subject_codes = []
        for subject in self._publication.get("instanceOf", {}).get("subject", {}):
            if (
                subject.get("inScheme", {}).get("code", "") == "uka.se"
                and subject.get("@type", "") == "Topic"
            ):
                subject_code = subject.get("code", "").strip()
                if subject_code:
                    uka_subject_codes.append(subject_code)
        return set(uka_subject_codes)

    @property
    def year(self):
        """Return the publication year as a string or None if missing or invalid."""
        dates = DATE_PATH.find(self._publication)
        if len(dates) == 1 and dates[0].value:
            try:
                parsed_date = parse_date(dates[0].value)
                return "{}".format(parsed_date.year)
            except ValueError:
                return None
        else:
            return None

    @property
    def summaries(self):
        """Return a list of all summaries."""
        summaries = SUMMARY_PATH.find(self._publication)
        return [summary.value for summary in summaries if summary.value]

    @property
    def status(self):
        """Return publication status or None if missing."""
        pub_statuses = PUBLICATION_STATUS_PATH.find(self._publication)
        # FIXME Can we have more than one pub status?
        if len(pub_statuses) == 1 and pub_statuses[0].value:
            return pub_statuses[0].value
        else:
            return None

    @property
    def is_classified(self):
        """Return True if publication has at least one 3 or 5 level UKA subject."""
        SUBJECT_PREFIX = "https://id.kb.se/term/uka/"
        for code in self.subject_codes:
            if not code.startswith(SUBJECT_PREFIX):
                continue
            short = code[len(SUBJECT_PREFIX) :]
            if len(short) == 3 or len(short) == 5:
                return True
        return False

    def get_english_summary(self):
        """Get summary text in English if it exists."""
        return self._get_lang_summary("eng")

    def get_swedish_summary(self):
        """Get summary text in Swedish if it exists."""
        return self._get_lang_summary("swe")

    def _get_lang_summary(self, lang):
        """Get summary for specified language if it exists."""
        for summary in self.summaries:
            if "language" not in summary:
                continue
            if "code" not in summary["language"]:
                continue
            if summary["language"]["code"] != lang:
                continue
            if "label" in summary:
                return summary["label"]
        return None

    def add_subjects(self, subjects):
        """Add a list of subjects to the publication.

        Each subject is flagged with "Autoclassified by Swepub"."""
        if "instanceOf" not in self._publication:
            self._publication["instanceOf"] = {}
        if "subject" not in self._publication["instanceOf"]:
            self._publication["instanceOf"]["subject"] = []
        flag = "Autoclassified by Swepub"
        marked_subjects = [self._add_note(subj, flag) for subj in subjects]
        self._publication["instanceOf"]["subject"].extend(marked_subjects)

    @staticmethod
    def _add_note(obj, text):
        if "hasNote" not in obj:
            obj["hasNote"] = []
        note = {"@type": "Note", "label": text}
        obj["hasNote"].append(note)
        return obj


def _generate_occurrence_table():
    with get_connection() as connection:
        cursor = connection.cursor()
        count_per_word = {}
        for converted_row in cursor.execute(
            """
        SELECT
            data
        FROM
            converted
        WHERE
            deleted = 0
        """
        ):
            converted = json.loads(converted_row[0])
            publication = Publication(converted)
            strings_to_scan = []
            for summary in converted.get("instanceOf", {}).get("summary", []):
                strings_to_scan.append(summary.get("label", ""))
            strings_to_scan.extend(publication.keywords)
            if publication.title:
                strings_to_scan.append(publication.title)
            if publication.subtitle:
                strings_to_scan.append(publication.subtitle)

            for string in strings_to_scan:
                string = string.translate(undesired_binary_chars_table)
                string = string.translate(undesired_unary_chars_table)
                string = string.lower()
                string = re.sub(r"[^a-zåäö ]+", "", string)
                words = re.findall(r"\w+", string)
                for word in words:
                    if word == "" or len(word) < 3:
                        continue
                    word = word.lower()
                    if word not in count_per_word:
                        count_per_word[word] = 1
                    else:
                        count_per_word[word] = 1 + count_per_word[word]
        for word in count_per_word:
            cursor.execute(
                """
            INSERT INTO abstract_total_word_counts(word, occurrences) VALUES(?, ?);
            """,
                (word, count_per_word[word]),
            )
        connection.commit()


def _select_rarest_words():
    with get_connection() as connection:
        cursor = connection.cursor()
        second_cursor = connection.cursor()
        third_cursor = connection.cursor()

        total = cursor.execute("SELECT COUNT(*) FROM converted WHERE deleted = 0").fetchone()[0]
        limit = 25000

        for n in range(0, total//limit + 1):
            # Necessary for WAL file not to grow too big
            checkpoint()

            for converted_row in cursor.execute(
                f"""
            SELECT
                id, data
            FROM
                converted
            WHERE
                deleted = 0
            LIMIT {limit}
            OFFSET {limit*n}
            """
            ):
                converted_rowid = converted_row[0]
                converted = json.loads(converted_row[1])
                publication = Publication(converted)
                strings_to_scan = []
                for summary in converted.get("instanceOf", {}).get("summary", []):
                    strings_to_scan.append(summary.get("label", ""))
                strings_to_scan += publication.keywords

                words_set = set()
                for string in strings_to_scan:
                    string = string.translate(undesired_binary_chars_table)
                    string = string.translate(undesired_unary_chars_table)
                    string = string.lower()
                    string = re.sub(r"[^a-zåäö ]+", "", string)
                    words = re.findall(r"\w+", string)
                    for word in words:
                        if word == "" or len(word) < 4 or word in known_bad_rare_words:
                            continue
                        words_set.add(word.lower())
                words = list(words_set)[0:150]

                for total_count_row in second_cursor.execute(
                    f"""
                SELECT
                    word
                FROM
                    abstract_total_word_counts
                WHERE
                    word IN ({','.join('?'*len(words))})
                ORDER BY
                    occurrences ASC
                LIMIT
                    12;
                """,
                    words,
                ):
                    rare_word = total_count_row[0]
                    # print(f"Writing rare word {rare_word} for id: {converted_rowid}")
                    third_cursor.execute(
                        """
                    INSERT INTO abstract_rarest_words(word, converted_id) VALUES(?, ?);
                    """,
                        (rare_word, converted_rowid),
                    )
                connection.commit()


def eligible_for_autoclassification(converted_data):
    publication = Publication(converted_data)
    # 1. Publication year >= 2012
    if (
        publication.year is None or int(publication.year) < 2012
    ):  # 2010 According to some? Old swepub uses 2012
        return False
    # 2. Swe/eng abstract
    if not (publication.get_english_summary() or publication.get_swedish_summary()):
        return False
    # 3. Publication status == (Published || None)
    if (
        publication.status is not None
        and publication.status != "https://id.kb.se/term/swepub/Published"
    ):
        return False
    # 4. No 3-level/5-level classification
    if publication.is_classified:
        return False
    return True


def _find_and_add_subjects():
    with get_connection() as connection:
        cursor = connection.cursor()

        # Sqlite does not allow reading and writing to occurr concurrently. In this particular
        # case what we want to do concurrently (many in parallell!) is the query in _conc_find_subjects.
        # By writing to a temp dir, instead of directly to the database, it becomes possible to
        # perform that query out-off-process, and thereby doing many queries in parallell.
        # The 'file_sequence_number' is the file each process should be writing results into.
        with TemporaryDirectory() as temp_dir:
            file_sequence_number = 0
            with ProcessPoolExecutor(max_workers=20) as executor:
                batch = []
                for converted_row in cursor.execute(
                    """
                SELECT
                    converted.id, converted.data
                FROM
                    converted
                WHERE
                    deleted = 0
                """
                ):
                    if eligible_for_autoclassification(json.loads(converted_row[1])):
                        batch.append(converted_row)
                        if len(batch) >= 256:
                            func = partial(_conc_find_subjects, temp_dir, file_sequence_number)
                            executor.submit(func, batch)
                            file_sequence_number += 1
                            batch = []
                file_sequence_number += 1
                func = partial(_conc_find_subjects, temp_dir, file_sequence_number)
                executor.submit(func, batch)
                executor.shutdown(wait=True)

            for file in os.listdir(temp_dir):
                with open(f"{temp_dir}/{file}", encoding="utf-8") as f:
                    while True:
                        rowid = f.readline()
                        if not rowid:
                            break
                        jsontext = f.readline().rstrip()

                        # print(f"About to write at id: {rowid}, data:\n{jsontext}")

                        cursor.execute(
                            """
                        SELECT
                            data, events, source, date
                        FROM
                            converted
                        WHERE
                            id = ? ;
                        """,
                            (rowid,),
                        )
                        row = cursor.fetchone()
                        old_publication = Publication(json.loads(row[0]))
                        events = json.loads(row[1])
                        source = row[2]
                        date = row[3]

                        publication = Publication(json.loads(jsontext))
                        code = "auto_classify"
                        initial_value = old_publication.uka_swe_classification_list
                        value = publication.uka_swe_classification_list
                        result = "1"

                        events["audit_events"]["AutoclassifierAuditor"] = [
                            {
                                "code": "auto_classify",
                                "result": "enriched",
                                "initial_value": initial_value,
                                "value": value,
                            }
                        ]

                        cursor.execute(
                            """
                        UPDATE
                            converted
                        SET
                            data = ?, events = ?
                        WHERE
                            id = ? ;
                        """,
                            (jsontext, json.dumps(events), rowid),
                        )

                        cursor.execute(
                            """
                        INSERT INTO converted_record_info
                            (converted_id, source, date, audit_name, audit_code, audit_result)
                        VALUES
                            (?, ?, ?, ?, ?, ?);
                        """,
                            (rowid, source, date, "AutoclassifierAuditor", code, result),
                        )
                connection.commit()


def _conc_find_subjects(temp_dir, file_sequence_number, converted_rows):
    with get_connection() as connection:
        cursor = connection.cursor()

        # orjson's dumps() returns bytes, hence binary mode
        with open(f"{temp_dir}/{file_sequence_number}", "wb") as output:
            for converted_row in converted_rows:
                converted_rowid = converted_row[0]
                converted = json.loads(converted_row[1])

                added_count, new_data = find_subjects_for(converted_rowid, converted, cursor)
                if added_count:
                    output.write(str(converted_rowid).encode())
                    output.write("\n".encode())
                    output.write(json.dumps(new_data))
                    output.write("\n".encode())


def find_subjects_for(converted_rowid, converted, cursor):
    level = 3
    classes = 3

    subjects = Counter()
    publication_subjects = set()

    for candidate_row in cursor.execute(
        """
    SELECT
        converted.id, converted.data, group_concat(abstract_rarest_words.word, '\n')
    FROM
        abstract_rarest_words
    LEFT JOIN
        converted
    ON
        converted.id = abstract_rarest_words.converted_id
    WHERE
        abstract_rarest_words.word IN (SELECT word FROM abstract_rarest_words WHERE converted_id = ?)
    GROUP BY
        abstract_rarest_words.converted_id;
    """,
        (converted_rowid,),
    ):
        candidate_rowid = candidate_row[0]
        candidate_matched_words = []
        if isinstance(candidate_row[2], str):
            candidate_matched_words = candidate_row[2].split("\n")

        if candidate_rowid == converted_rowid:
            continue

        # This is a vital tweaking point. How many _rare_ words do two abstracts need to share
        # in order to be considered on the same subject? 2 seems a balanced choice. 1 "works" too,
        # but may be a bit too aggressive (providing a bit too many false positive matches).
        if len(candidate_matched_words) < 1:
            continue

        # print(f"Matched {converted_rowid} with {candidate_rowid} based on shared rare words: {candidate_matched_words}")
        candidate = json.loads(candidate_row[1])
        for subject in candidate.get("instanceOf", {}).get("subject", []):
            try:
                authority, subject_id = subject["inScheme"]["code"], subject["code"]
            except KeyError:
                continue

            if authority not in ("hsv", "uka.se") or len(subject_id) < level:
                continue

            publication_subjects.add(subject_id[:level])
        score = 5 * len(candidate_matched_words) * len(candidate_matched_words)
        for sub in publication_subjects:
            subjects[sub] += score

    publication = Publication(converted)
    old_subject_codes = publication.uka_subject_codes
    subjects = subjects.most_common(classes)
    new_subjects = [
        (subject, score) for subject, score in subjects if subject not in old_subject_codes
    ]

    # Filter out matches with a score less than 50% of the top match.
    if len(new_subjects) > 1:
        new_subjects = sorted(new_subjects, key=lambda tup: tup[1], reverse=True)

        (top_subject, top_score) = new_subjects.pop(0)
        result = [(top_subject, top_score)]
        good_matches = [(subj, score) for (subj, score) in new_subjects
                        if score >= top_score / 2]
        result.extend(good_matches)
        new_subjects = result

    if len(new_subjects) > 0:
        publication = Publication(converted)
        enriched_subjects = _enrich_subject(new_subjects)
        # print(f"enriched subjects for {converted_rowid}: {str(enriched_subjects)}")

        langs = ["eng", "swe"]
        classifications = []
        for item in enriched_subjects:
            for lang in langs:
                if lang in item:
                    classifications.append(item[lang])

        publication.add_subjects(classifications)

        return True, publication.data

        # print(f"Into publication: {converted_rowid}")
        # for summary in converted.get("instanceOf", {}).get("summary", []):
        #     print(f"  with summary:\"{summary}\"")
        # for keyword in publication.keywords:
        #     print(f"  with keyword:\"{keyword}\"")
        # for classification in classifications:
        #     print(f"  added subject: {classification['prefLabel']}")
        # print("\n")
    return False, None


def _enrich_subject(subjects):
    ret = []
    for code, score in subjects:
        r = {
            "score": score,
            "swe": _create_subject(code, "swe"),
            "eng": _create_subject(code, "eng"),
        }
        ret += [r]
    return ret


def _create_subject(code, lang):
    category_level = {1: (1,), 3: (1, 3), 5: (1, 3, 5)}

    return {
        "@type": "Topic",
        "@id": "https://id.kb.se/term/uka/{}".format(code),
        "inScheme": {
            "@id": "https://id.kb.se/term/uka/",
            "@type": "ConceptScheme",
            "code": "uka.se",
        },
        "code": code,
        "prefLabel": categories.get(code, {}).get(lang),
        "language": {"@type": "Language", "@id": f"https://id.kb.se/language/{lang}", "code": lang},
        "_topic_tree": [categories.get(code[:x], {}).get(lang) for x in category_level[len(code)]],
    }


def auto_classify(incremental, incrementally_converted_rowids):
    if not incremental:
        t0 = time.time()
        # First populate the abstract_total_word_counts table, so that we know
        # how many times each word occurs (within all combined abstracts).
        _generate_occurrence_table()
        t1 = time.time()
        diff = round(t1 - t0, 2)
        print(f"  auto classify 1 (counting) ran for {diff} seconds")
        t0 = t1

        # Then go over the data again, and select the N _rarest_ words out of each
        # abstract, which we can now calculate given the table populated above.
        # Put these rare words in the abstract_rarest_words table.
        _select_rarest_words()
        t1 = time.time()
        diff = round(t1 - t0, 2)
        print(f"  auto classify 2 (selecting) ran for {diff} seconds")
        t0 = t1

        # Now, go over the data a third time, this time, for each publication retrieving
        # candidates that share rare words, and thereby plausibly have the same subject.
        # Selectively copy good subjects over
        _find_and_add_subjects()
        t1 = time.time()
        diff = round(t1 - t0, 2)
        print(f"  auto classify 3 (adding) ran for {diff} seconds")
    else:
        # print(f"Should now have done peicemeal auto classication on: {incrementally_converted_rowids}")
        with get_connection() as connection:
            cursor = connection.cursor()
            for converted_rowid in incrementally_converted_rowids:
                cursor.execute(
                    """
                SELECT
                    data
                FROM
                    converted
                WHERE
                    id = ? AND deleted = 0
                """,
                    (converted_rowid,),
                )

                rows = cursor.fetchall()
                if len(rows) == 0: # A deleted record can't be loaded, so this can occurr.
                    continue

                row = rows[0]  # Can only be one
                converted = json.loads(row[0])

                if eligible_for_autoclassification(converted):
                    added_count, new_data = find_subjects_for(converted_rowid, converted, cursor)
                    if added_count:
                        cursor.execute(
                            """
                        UPDATE
                            converted
                        SET
                            data = ?
                        WHERE
                            id = ? ;
                        """,
                            (new_data, converted_rowid),
                        )
                    # else:
                    #    print(f"Nothing to add for {converted_rowid}")
            connection.commit()


# For debugging
if __name__ == "__main__":
    auto_classify(False, [])
