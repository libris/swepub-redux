from storage import commit_sqlite, get_cursor, open_existing_storage
import json
import re

def generate_frequency_tables():
    cursor = get_cursor()
    second_cursor = get_cursor()
    third_cursor = get_cursor()

    # First populate the abstract_total_word_counts, so that we know how many
    # times each word occurs (within all combined abstracts).
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

    # Then go over the data again, and select the N rarest words out of each
    # abstract, which we can now calculate given the table populated above.
    # Put these rare words in the abstract_rarest_words table.
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
                5;
            """, words):
                rare_word = total_count_row[0]
                #print(f"Writing rare word {rare_word} for id: {finalized_rowid}")
                third_cursor.execute("""
                INSERT INTO abstract_rarest_words(word, finalized_id) VALUES(?, ?);
                """, (rare_word, finalized_rowid))
        commit_sqlite()

    # Now, go over the data a third time, this time, for each publication retrieving
    # candidates that _plausibly_ have the same subject.
    for finalized_row in cursor.execute("""
    SELECT
        id
    FROM
        finalized;
    """):
        finalized_rowid = finalized_row[0]

        for candidate_row in second_cursor.execute("""
            SELECT
                finalized.data
            FROM
                abstract_rarest_words
            LEFT JOIN
                finalized
            ON
                finalized.id = abstract_rarest_words.finalized_id
            WHERE
                abstract_rarest_words.word IN (SELECT word FROM abstract_rarest_words WHERE finalized_id = ?);
            """, (finalized_rowid,)):
                finalized = json.loads(candidate_row[0])
                for summary in finalized.get("instanceOf", {}).get("summary", []):
                    abstract = summary.get("label", "")
                    #print(f"abstract: {abstract}")
        #print("\n\n")


# For debugging
if __name__ == "__main__":
    open_existing_storage()
    generate_frequency_tables()