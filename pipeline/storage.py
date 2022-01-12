import sqlite3
from sqlite3.dbapi2 import connect
import json
import os

sqlite_path = "./swepub.sqlite3"

connection = None

def clean_and_init_storage():
    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    global connection
    connection = sqlite3.connect(sqlite_path, timeout=(5*60*60))
    cursor = connection.cursor()

    # Because Swepub APIs expose publications as originally harvested, these must be kept.
    cursor.execute("""
    CREATE TABLE original (
        id INTEGER PRIMARY KEY,
        data TEXT
    );
    """)

    # After conversion, validation and normalization each publication is stored in this
    # form, for later in use in deduplication.
    cursor.execute("""
    CREATE TABLE converted (
        id INTEGER PRIMARY KEY,
        data TEXT,
        original_id INTEGER,
        FOREIGN KEY (original_id) REFERENCES original(id)
    );
    """)

    # To facilitate deduplication, store all of each publications ids (regardless of type)
    # in this table. This includes (a mangled form of) maintitles. Grouping on
    # 'identifier' in this table, will produce the raw candidates for deduplication.
    # These, to be clear, will overlap. But overlaping clusters will be joined in a later
    # step. This table should be considered temporary and dropped after deduplication.
    cursor.execute("""
    CREATE TABLE clusteringidentifiers (
        id INTEGER PRIMARY KEY,
        identifier TEXT,
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id)
    );
    """)

    # Deduplicated clusters, multiple rows per cluster. So for example, a cluster consisting
    # of publications A, B and C would look something like:
    # cluster_id | converted_id
    #---------------------------
    # 123        | A
    # 123        | B
    # 123        | C
    #---------------------------
    # These may initially overlap (publication A may be in more than one cluster).
    # But any overlaps should have been joined into a single cluster by the end of deduplication.
    cursor.execute("""
    CREATE TABLE cluster (
        cluster_id INTEGER,
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_clusters_clusterid ON cluster (cluster_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_clusters_convertedid ON cluster (converted_id);
    """)

    # The final form of a publication in swepub. Each row in this table contains a merged
    # publication, that represents one of the clusters found in the deduplication process.
    cursor.execute("""
    CREATE TABLE finalized (
        id INTEGER PRIMARY KEY,
        cluster_id INTEGER,
        data TEXT,
        FOREIGN KEY (cluster_id) REFERENCES cluster(cluster_id)
    );
    """)

    # To facilitate "auto classification", store each word in each publications abstract
    # together with the realtive frequency (integer) of that word within the abstract,
    # divided by the frequency of that word across all abstracts.
    #
    # The idea here, is that searching for other records having similar elevated frequencies
    # of certain words (whatever is most elevated in you abstract) will (hopefully) give you
    # publications talking about "the same sorts of things". In other words, "the same subject".
    # If these found publications appear to have a "better" explicit subject, we try to copy the
    # subject to our own publication.
    #
    # This is a temporary table, it should be dropped after AutoClassification
    cursor.execute("""
    CREATE TABLE abstract_word_frequencies (
        id INTEGER PRIMARY KEY,
        word TEXT,
        frequency INTEGER,
        finalized_id INTEGER,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_abstract_word_frequencies ON abstract_word_frequencies (word, frequency);
    """)
    # In order to calculate values for the above table, we also need an answer to the question:
    #
    # What is the frequency of each word that appears in an abstract, as seen over all of
    # swepubs abstracts? 
    # 
    # So for example if all abstracts together consists of 1500000*100 word, and "mathematics"
    # appears 500 times total, across a bunch of publications.
    # The total frequency for mathematics is then 500 / 1500000*100.
    # As we can't use floating point numbers in sqlite, we encode this as 10000000 / 500 / 1500000*100
    # (points per 10 million instead of [0.0,1.0] )
    #
    # This is a temporary table, it should be dropped after AutoClassification
    cursor.execute("""
    CREATE TABLE abstract_total_word_frequencies (
        id INTEGER PRIMARY KEY,
        word TEXT,
        frequency INTEGER
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_abstract_total_word_frequencies ON abstract_total_word_frequencies (word);
    """)

    connection.commit()

def open_existing_storage():
    global connection
    connection = sqlite3.connect(sqlite_path, timeout=(5*60*60))

def store_converted(xml, converted):
    cursor = connection.cursor()

    #print(f'Inserting with oai_id {converted["@id"]}')

    original_rowid = cursor.execute("""
    INSERT INTO original(data) VALUES(?);
    """, (json.dumps(converted),)).lastrowid

    converted_rowid = cursor.execute("""
    INSERT INTO converted(data, original_id) VALUES(?, ?);
    """, (json.dumps(converted), original_rowid)).lastrowid

    identifiers = []
    for title in converted["instanceOf"]["hasTitle"]:
        if title["mainTitle"] is not None and isinstance(title["mainTitle"], str):
            identifiers.append(title["mainTitle"]) # TODO: STRIP AWAY WHITESPACE ETC
    
    for id_object in converted["identifiedBy"]:
        if id_object["@type"] != "Local":
            identifier = id_object["value"]
            if identifier is not None and isinstance(identifier, str):
                identifiers.append(identifier)
            
    for identifier in identifiers:
        cursor.execute("""
        INSERT INTO clusteringidentifiers(identifier, converted_id) VALUES (?, ?)
        """, (identifier, converted_rowid))
            
    connection.commit()

def get_cursor():
    return connection.cursor()

def commit_sqlite():
    connection.commit()