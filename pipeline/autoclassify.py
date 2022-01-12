from storage import commit_sqlite, get_cursor, open_existing_storage
import json
import re

FLOAT_SCALE = 10000000

def generate_frequency_tables():
    cursor = get_cursor()

    # First populate the abstract_total_word_frequencies
    # So that we know the frequency of ech word (within all combined
    # abstracts).
    total_word_count = 0 # Across ALL abstracts in swepub!
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
                total_word_count += 1
                if not word in count_per_word:
                    count_per_word[word] = 1
                else:
                    count_per_word[word] = 1 + count_per_word[word]
    for word in count_per_word:
        cursor.execute("""
        INSERT INTO abstract_total_word_frequencies(word, frequency) VALUES(?, ?);
        """, (word, FLOAT_SCALE * (count_per_word[word]/total_word_count)))
    commit_sqlite()

    # Then go over the data again, and record the _relative_ frequency of
    # each word in each abstract. So for example:
    # Say that the word "mathematics" has a total frequency of 70490 (out
    # of every 10 million), as calculated above.
    # Now calculate the corresponding frequency _within_ each abstract.
    # Say that one abstract has the word mathematics in a frequency of 170490
    # (again per 10 million), which is higher. It means that:
    # For this abstract, the relative frequency for that word is:
    # 170490 / 70490 = 2.4. An elevated frequency (higher than 1.0)!
    # Let's then record the relative frequency of "mathematics" for this
    # publication/abstract as 2.4 (but again converted to points per 10 million
    # as we can't store floats).
    #
    # We should store only the few highest relative frequencies that's all we're
    # interested in, and storing everything will be very expensive.
    second_cursor = get_cursor()
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
            word_count = len(words)
            for word in set(words):
                word = word.lower()
                freq_int = int(( FLOAT_SCALE * abstract.count(word) ) / word_count)
                for total_freq_row in second_cursor.execute("""
                SELECT
                    frequency
                FROM
                    abstract_total_word_frequencies
                WHERE
                    word = ?;
                """, (word,) ): # Should only ever be one row
                    total_freq_int = total_freq_row[0]
                    relative_freq = freq_int / total_freq_int
                    #print(f"The relative frequency for '{word}' within (the abstract of) {finalized['@id']} is {relative_freq}")
                    second_cursor.execute("""
                    INSERT INTO abstract_word_frequencies(word, frequency, finalized_id) VALUES(?, ?, ?);
                    """, (word, FLOAT_SCALE * relative_freq, finalized_rowid))
        commit_sqlite()

# For debugging
if __name__ == "__main__":
    open_existing_storage()
    generate_frequency_tables()