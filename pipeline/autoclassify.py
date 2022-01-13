from storage import commit_sqlite, get_cursor, open_existing_storage
from collections import Counter
import json
import re
from json import load
from os import path

categories = load(open(path.join(path.dirname(__file__), 'categories.json')))

def generate_occurrence_table():
    cursor = get_cursor()
    count_per_word = {}
    for finalized_row in cursor.execute("""
    SELECT
        data
    FROM
        finalized;
    """):
        finalized = json.loads(finalized_row[0])
        for summary in finalized.get("instanceOf", {}).get("summary", []):
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

def select_rarest_words():
    cursor = get_cursor()
    second_cursor = get_cursor()
    third_cursor = get_cursor()
    for finalized_row in cursor.execute("""
    SELECT
        id, data
    FROM
        finalized;
    """):
        finalized_rowid = finalized_row[0]
        finalized = json.loads(finalized_row[1])
        for summary in finalized.get("instanceOf", {}).get("summary", []):
            abstract = summary.get("label", "")

            words = re.findall(r'\w+', abstract)
            words_set = set()
            for word in words:
                if word.isnumeric():
                    continue
                words_set.add(word.lower())
            words = list(words_set)

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
                INSERT INTO abstract_rarest_words(word, finalized_id) VALUES(?, ?);
                """, (rare_word, finalized_rowid))
        commit_sqlite()

def find_subjects():
    cursor = get_cursor()
    second_cursor = get_cursor()
    for finalized_row in cursor.execute("""
    SELECT
        finalized.id, finalized.data
    FROM
        finalized;
    """):
        finalized_rowid = finalized_row[0]
        finalized = json.loads(finalized_row[1])

        subjects = Counter()
        publication_subjects = set()

        for candidate_row in second_cursor.execute("""
            SELECT
                finalized.id, finalized.data, group_concat(abstract_rarest_words.word, '\n')
            FROM
                abstract_rarest_words
            LEFT JOIN
                finalized
            ON
                finalized.id = abstract_rarest_words.finalized_id
            WHERE
                abstract_rarest_words.word IN (SELECT word FROM abstract_rarest_words WHERE finalized_id = ?)
            GROUP BY
                abstract_rarest_words.finalized_id;
            """, (finalized_rowid,)):
                candidate_rowid = candidate_row[0]
                candidate = json.loads(candidate_row[1])
                candidate_matched_words = []
                if isinstance(candidate_row[2], str):
                    candidate_matched_words = candidate_row[2].split("\n")

                if candidate_rowid == finalized_rowid:
                    continue
                
                # This is a vital tweaking point. How many _rare_ words do two abstracts need to share
                # in order to be considered on the same subject. 2 seems a balanced choice. 1 "works" too,
                # but may be a bit too aggressive (providing a bit too many false positive matches)
                if len(candidate_matched_words) < 2:
                    continue

                level = 3
                classes = 5

                print(f"Matched {finalized_rowid} with {candidate_rowid} based on shared rare words: {candidate_matched_words}")
        
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
        #print(f"most common subjects: {subjects.most_common(classes)}")
        subjects = subjects.most_common(classes)
        if len(subjects) > 0:
            enriched_subjects =_enrich_subject(subjects)
            print(f"enriched subjects for {finalized_rowid}: {str(enriched_subjects)}")


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



# For debugging
if __name__ == "__main__":
    open_existing_storage()

    # First populate the abstract_total_word_counts table, so that we know
    # how many times each word occurs (within all combined abstracts).
    generate_occurrence_table()

    # Then go over the data again, and select the N _rarest_ words out of each
    # abstract, which we can now calculate given the table populated above.
    # Put these rare words in the abstract_rarest_words table.
    select_rarest_words()

    # Now, go over the data a third time, this time, for each publication retrieving
    # candidates that share rare words, and thereby plausibly have the same subject.
    # Selectively copy good subjects over
    find_subjects()

    