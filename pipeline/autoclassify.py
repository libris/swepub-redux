from storage import commit_sqlite, get_cursor, open_existing_storage
from collections import Counter
from audit import Publication
import json
import re
import time
import os
from json import load
from os import path
from multiprocessing import Process
from tempfile import TemporaryDirectory

categories = load(open(path.join(path.dirname(__file__), 'categories.json')))

def _generate_occurrence_table():
    cursor = get_cursor()
    count_per_word = {}
    for converted_row in cursor.execute("""
    SELECT
        data
    FROM
        converted;
    """):
        converted = json.loads(converted_row[0])
        for summary in converted.get("instanceOf", {}).get("summary", []):
            abstract = summary.get("label", "")
            words = re.findall(r'\w+', abstract)
            for word in words:
                if word.isnumeric():
                    continue
                word = word.lower()
                if not word in count_per_word:
                    count_per_word[word] = 1
                else:
                    count_per_word[word] = 1 + count_per_word[word]
    for word in count_per_word:
        cursor.execute("""
        INSERT INTO abstract_total_word_counts(word, occurrences) VALUES(?, ?);
        """, (word, count_per_word[word]) )
    commit_sqlite()

def _select_rarest_words():
    cursor = get_cursor()
    second_cursor = get_cursor()
    third_cursor = get_cursor()
    for converted_row in cursor.execute("""
    SELECT
        id, data
    FROM
        converted;
    """):
        converted_rowid = converted_row[0]
        converted = json.loads(converted_row[1])
        for summary in converted.get("instanceOf", {}).get("summary", []):
            abstract = summary.get("label", "")

            words = re.findall(r'\w+', abstract)
            words_set = set()
            for word in words:
                if word.isnumeric():
                    continue
                words_set.add(word.lower())
            words = list(words_set)[0:150]

            for total_count_row in second_cursor.execute(f"""
            SELECT
                word
            FROM
                abstract_total_word_counts
            WHERE
                word IN ({','.join('?'*len(words))})
            ORDER BY
                occurrences ASC
            LIMIT
                6;
            """, words):
                rare_word = total_count_row[0]
                #print(f"Writing rare word {rare_word} for id: {finalized_rowid}")
                third_cursor.execute("""
                INSERT INTO abstract_rarest_words(word, converted_id) VALUES(?, ?);
                """, (rare_word, converted_rowid))
        commit_sqlite()

def _find_and_add_subjects():
    cursor = get_cursor()
    
    # Sqlite does not allow reading and writing to occurr concurrently. In this particular
    # case what we want to do concurrently (many in parallell!) is the query in _conc_find_subjects.
    # By writing to a temp dir, instead of directly to the database, it becomes possible to
    # perform that query out-off-process, and thereby doing many queries in parallell.
    # The 'file_sequence_number' is the file each process should be writing results into.
    with TemporaryDirectory() as temp_dir:
        file_sequence_number = 0
        
        batch = []
        processes = []
        for converted_row in cursor.execute("""
        SELECT
            converted.id, converted.data
        FROM
            converted;
        """):
            
            
            batch.append(converted_row)
            if (len(batch) >= 256):
                while (len(processes) >= 20):
                    time.sleep(0)
                    n = len(processes)
                    i = n-1
                    while i > -1:
                        if not processes[i].is_alive():
                            processes[i].join()
                            del processes[i]
                        i -= 1
                p = Process(target=_conc_find_subjects, args=(batch,temp_dir,file_sequence_number))
                file_sequence_number += 1
                p.start()
                processes.append( p )
                batch = []
        p = Process(target=_conc_find_subjects, args=(batch,temp_dir,file_sequence_number))
        file_sequence_number += 1
        p.start()
        processes.append( p )
        for p in processes:
            p.join()

        for file in os.listdir(temp_dir):
            with open(f"{temp_dir}/{file}", "r") as f:
                rowid = f.readline()
                if not rowid:
                    continue
                jsontext = f.readline()

                #print(f"About to write at id: {rowid}, data:\n{jsontext}")
                
                cursor.execute("""
                UPDATE
                    converted
                SET
                    data = ?
                WHERE
                    id = ? ;
                """, (jsontext, rowid) )
            commit_sqlite()
        

def _conc_find_subjects(converted_rows, temp_dir, file_sequence_number):
    cursor = get_cursor()
    level = 3
    classes = 5

    with open(f"{temp_dir}/{file_sequence_number}", "w") as output:

        for converted_row in converted_rows:
            converted_rowid = converted_row[0]
            converted = json.loads(converted_row[1])

            subjects = Counter()
            publication_subjects = set()

            for candidate_row in cursor.execute("""
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
                """, (converted_rowid,)):
                    candidate_rowid = candidate_row[0]
                    candidate = json.loads(candidate_row[1])
                    candidate_matched_words = []
                    if isinstance(candidate_row[2], str):
                        candidate_matched_words = candidate_row[2].split("\n")

                    if candidate_rowid == converted_rowid:
                        continue
                    
                    # This is a vital tweaking point. How many _rare_ words do two abstracts need to share
                    # in order to be considered on the same subject? 2 seems a balanced choice. 1 "works" too,
                    # but may be a bit too aggressive (providing a bit too many false positive matches).
                    if len(candidate_matched_words) < 2:
                        continue

                    #print(f"Matched {finalized_rowid} with {candidate_rowid} based on shared rare words: {candidate_matched_words}")
            
                    for subject in candidate.get("instanceOf", {}).get("subject", []):
                        try:
                            authority, subject_id = subject['inScheme']['code'], subject['code']
                        except KeyError:
                            continue

                        if authority not in ('hsv', 'uka.se') or len(subject_id) < level:
                            continue

                        publication_subjects.add(subject_id[:level])
                    score = len(candidate_matched_words)
                    for sub in publication_subjects:
                        subjects[sub] += score
            subjects = subjects.most_common(classes)
            if len(subjects) > 0:
                enriched_subjects =_enrich_subject(subjects)
                #print(f"enriched subjects for {finalized_rowid}: {str(enriched_subjects)}")

                LANGS = ['eng', 'swe']
                classifications = []
                for item in enriched_subjects:
                    for lang in LANGS:
                        if lang in item:
                            classifications.append(item[lang])
                
                publication = Publication(converted)
                #initial_value = publication.uka_swe_classification_list
                publication.add_subjects(classifications)

                output.write(str(converted_rowid))
                output.write("\n")
                output.write(json.dumps(publication.data))
                output.write("\n")

                #print(f"added subjects {classifications} into publication: {finalized_rowid}")
                
                #code = "autoclassified"
                #value = publication.uka_swe_classification_list
                #logger.info(
                    #f"Autoclassifying publication {publication.id}", extra={'auditor': self.name})
                #new_audit_events = self._add_audit_event(audit_events, result, code, initial_value, value)

def _enrich_subject(subjects):
    ret = []
    for code, score in subjects:
        r = {
            'score': score,
            'swe': _create_subject(code, 'swe'),
            'eng': _create_subject(code, 'eng')
        }
        ret += [r]
    return ret


def _create_subject(code, lang):
    category_level = {
        1: (1, ),
        3: (1, 3),
        5: (1, 3, 5)
    }

    return {
        "@type": "Topic",
        "@id": "https://id.kb.se/term/uka/{}".format(code),
        "inScheme": {
            "@id": "https://id.kb.se/term/uka/",
            "@type": "ConceptScheme",
            "code": "uka.se"
        },
        "code": code,
        "prefLabel": categories.get(code, {}).get(lang),
        "language": {
            "@type": "Language",
            "@id": f"https://id.kb.se/language/{lang}",
            "code": lang
        },
        "_topic_tree": [
            categories.get(code[:x], {}).get(lang) for x in category_level[len(code)]
        ]
    }

def auto_classify():
    t0 = time.time()
    # First populate the abstract_total_word_counts table, so that we know
    # how many times each word occurs (within all combined abstracts).
    _generate_occurrence_table()
    t1 = time.time()
    diff = t1-t0
    print(f"  auto classify 1 (counting) ran for {diff} seconds")
    t0 = t1

    # Then go over the data again, and select the N _rarest_ words out of each
    # abstract, which we can now calculate given the table populated above.
    # Put these rare words in the abstract_rarest_words table.
    _select_rarest_words()
    t1 = time.time()
    diff = t1-t0
    print(f"  auto classify 2 (selecting) ran for {diff} seconds")
    t0 = t1

    # Now, go over the data a third time, this time, for each publication retrieving
    # candidates that share rare words, and thereby plausibly have the same subject.
    # Selectively copy good subjects over
    _find_and_add_subjects()
    t1 = time.time()
    diff = t1-t0
    print(f"  auto classify 3 (adding) ran for {diff} seconds")
    t0 = t1

# For debugging
if __name__ == "__main__":
    open_existing_storage()
    auto_classify()
