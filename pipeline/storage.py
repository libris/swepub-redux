import sqlite3
from sqlite3.dbapi2 import connect
import json
import os
from bibframesource import BibframeSource

sqlite_path = "./swepub.sqlite3"

connection = None

def clean_and_init_storage():
    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    global connection
    connection = sqlite3.connect(sqlite_path)
    cursor = connection.cursor()

    # Use sqlite WAL mode
    cursor.execute("PRAGMA journal_mode=WAL;")
    # Faster!!
    cursor.execute("PRAGMA synchronous=OFF;")

    # Because Swepub APIs expose publications as originally harvested, these must be kept.
    cursor.execute("""
    CREATE TABLE original (
        id INTEGER PRIMARY KEY,
        source TEXT,
        data TEXT
    );
    """)

    # After conversion, validation and normalization each publication is stored in this
    # form, for later in use in deduplication.
    cursor.execute("""
    CREATE TABLE converted (
        id INTEGER PRIMARY KEY,
        oai_id TEXT,
        data TEXT,
        original_id INTEGER,
        date INTEGER,
        source TEXT,
        is_open_access INTEGER,
        ssif_1 INTEGER,
        classification_level INTEGER,
        is_swedishlist INTEGER,
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
        oai_id TEXT,
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

    cursor.execute("""
    CREATE TABLE search_single (
        id INTEGER PRIMARY KEY,
        finalized_id INTEGER,
        year INTEGER,
        content_marking TEXT,
        publication_status TEXT,
        swedish_list INTEGER,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE search_doi (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE search_genre_form (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE search_subject (
        finalized_id INTEGER,
        value INTEGER,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE search_creator (
        finalized_id INTEGER,
        orcid TEXT,
        family_name TEXT,
        given_name TEXT,
        local_id TEXT,
        local_id_by TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE search_org (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)

    cursor.execute("""
    CREATE VIRTUAL TABLE search_fulltext USING FTS5 (
        title,
        keywords
    );
    """)

    connection.commit()

def open_existing_storage():
    global connection
    connection = sqlite3.connect(sqlite_path)

def store_converted(converted, source):
    cursor = connection.cursor()
    doc = BibframeSource(converted)

    #print(f'Inserting with oai_id {converted["@id"]}')

    original_rowid = cursor.execute("""
    INSERT INTO original(source, data) VALUES(?, ?);
    """, (source, json.dumps(converted),)).lastrowid

    converted_rowid = cursor.execute("""
    INSERT INTO converted(data, original_id, oai_id, date, source, is_open_access, ssif_1, classification_level, is_swedishlist) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        json.dumps(converted),
        original_rowid,
        doc.record_id,
        doc.publication_year,
        doc.source_org_master,
        doc.open_access,
        doc.ssif_1,
        doc.level,
        doc.is_swedishlist
    )).lastrowid

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