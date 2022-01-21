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
    connection = sqlite3.connect(sqlite_path)
    cursor = connection.cursor()

    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=OFF;")

    # Because Swepub APIs expose publications as originally harvested, these must be kept.
    cursor.execute("""
    CREATE TABLE original (
        id INTEGER PRIMARY KEY,
        source TEXT,
        oai_id, TEXT,
        accepted INTEGER, -- (fake boolean 1/0)
        data TEXT
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_original_oai_id ON original (oai_id);
    """)

    # This table is used to store log entries (validation/normalization errors etc) for
    # each publication
    cursor.execute("""
    CREATE TABLE converted_events (
        converted_id INTEGER,
        type TEXT,
        field TEXT,
        path TEXT,
        code TEXT,
        value TEXT,
        FOREIGN KEY (converted_id) REFERENCES converted(id)
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

    # To facilitate "auto classification", store (for each publication) the N rarest
    # words that occurr in that publications abstract.
    #
    # The idea here, is that when you are to auto classify publication A, list the
    # rarest words in A's abstract. Then find all other publications (B, C, D) that
    # also contains one or more of those words (with an emphasis on more).
    # 
    # Hopefully B, D, and C are now "about the same sorts of things" as A, since they
    # share rare abstract words.
    # If any of B, C or D appear to have a "better" explicit subject than A, we try to
    # copy that subject to our own publication (A).
    #
    # This is a temporary table, it should be dropped after AutoClassification
    cursor.execute("""
    CREATE TABLE abstract_rarest_words (
        id INTEGER PRIMARY KEY,
        word TEXT,
        finalized_id INTEGER,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_abstract_rarest_words ON abstract_rarest_words (word);
    """)
    cursor.execute("""
    CREATE INDEX idx_abstract_rarest_words_id ON abstract_rarest_words (finalized_id);
    """)
    # In order to calculate values (rarity) for the above table, we also need an answer
    # to the question:
    #
    # How many times does 'word' occurr inside abstracts of any of our publications?
    #
    # This is a temporary table, it should be dropped after AutoClassification
    cursor.execute("""
    CREATE TABLE abstract_total_word_counts (
        id INTEGER PRIMARY KEY,
        word TEXT,
        occurrences INTEGER
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_abstract_total_word_counts ON abstract_total_word_counts (word);
    """)

    connection.commit()

def open_existing_storage():
    global connection
    connection = sqlite3.connect(sqlite_path)

def store_original_and_converted(original, converted, source, accepted, events):
    cursor = connection.cursor()

    #print(f'Inserting with oai_id {converted["@id"]} : \n\n{json.dumps(converted)}\n\n')

    original_rowid = cursor.execute("""
    INSERT INTO original(source, data, accepted, oai_id) VALUES(?, ?, ?, ?);
    """, (source, json.dumps(original), accepted, converted["@id"])).lastrowid

    if not accepted:
        connection.commit()
        return

    converted_rowid = cursor.execute("""
    INSERT INTO converted(data, original_id) VALUES(?, ?);
    """, (json.dumps(converted), original_rowid)).lastrowid

    for event in events:
        cursor.execute("""
        INSERT INTO converted_events(converted_id, type, field, path, code, value) VALUES (?, ?, ?, ?, ?, ?)
        """, (converted_rowid, event["type"], event["field"], event["path"], event["code"], event["value"]))

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