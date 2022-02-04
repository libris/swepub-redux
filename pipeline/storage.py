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
        name TEXT,
        field TEXT,
        path TEXT,
        step TEXT,
        code TEXT,
        initial_value TEXT,
        result TEXT,
        FOREIGN KEY (converted_id) REFERENCES converted(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_events_converted_id ON converted_events(converted_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_events_type ON converted_events(type);
    """)

    # After conversion, validation and normalization each publication is stored in this
    # form, for later in use in deduplication.
    cursor.execute("""
    CREATE TABLE converted (
        id INTEGER PRIMARY KEY,
        oai_id TEXT, -- e.g. "oai:DiVA.org:ri-6513"
        data TEXT, -- JSON
        original_id INTEGER,
        date INTEGER, -- year
        source TEXT, -- source code, e.g. "kth", "ltu"
        is_open_access INTEGER,
        ssif_1 INTEGER, -- SSIF 1-level classification (1-6)
        classification_level TEXT, -- e.g. "https://id.kb.se/term/swepub/swedishlist/peer-reviewed". TOOD: store as int?
        is_swedishlist INTEGER, -- whether doc is peer-reviewed (see above) or not. Merge classification_level and is_swedishlist?
        FOREIGN KEY (original_id) REFERENCES original(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_oai_id ON converted(oai_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_date ON converted(date);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_source ON converted(source);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_is_open_access ON converted(is_open_access);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_ssif_1 ON converted(ssif_1);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_classification_level ON converted(classification_level);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_is_swedishlist ON converted(is_swedishlist);
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
    cursor.execute("""
    CREATE INDEX idx_finalized_oai_id ON finalized(oai_id);
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
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_abstract_rarest_words ON abstract_rarest_words (word, converted_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_abstract_rarest_words_id ON abstract_rarest_words (converted_id);
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
    CREATE INDEX idx_abstract_total_word_counts ON abstract_total_word_counts (word, occurrences);
    """)

    # SUGGESTED BY SQLITE: CREATE INDEX abstract_total_word_counts_idx_77e8bc04 ON abstract_total_word_counts(word, occurrences);

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
    CREATE INDEX idx_search_single_finalized_id ON search_single(finalized_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_single_finalized_year ON search_single(year);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_single_finalized_content_marking ON search_single(content_marking);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_single_publication_status ON search_single(publication_status);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_single_swedish_list ON search_single(swedish_list);
    """)

    cursor.execute("""
    CREATE TABLE search_doi (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_search_doi_finalized_id ON search_doi(finalized_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_doi_value ON search_doi(value);
    """)

    cursor.execute("""
    CREATE TABLE search_genre_form (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_search_genre_form_finalized_id ON search_genre_form(finalized_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_genre_form_value ON search_genre_form(value);
    """)

    cursor.execute("""
    CREATE TABLE search_subject (
        finalized_id INTEGER,
        value INTEGER,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_search_subject_finalized_id ON search_subject(finalized_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_subject_value ON search_subject(value);
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
    CREATE INDEX idx_search_creator_finalized_id ON search_creator(finalized_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_creator_orcid ON search_creator(orcid);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_creator_family_name ON search_creator(family_name);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_creator_given_name ON search_creator(given_name);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_creator_local_id ON search_creator(local_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_creator_local_id_by ON search_creator(local_id_by);
    """)

    cursor.execute("""
    CREATE TABLE search_org (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id)
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_search_org_finalized_id ON search_org(finalized_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_search_org_value ON search_org(value);
    """)

    cursor.execute("""
    CREATE VIRTUAL TABLE search_fulltext USING FTS5 (
        title,
        keywords
    );
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

def store_original_and_converted(original, converted, source, accepted, events):
    cursor = connection.cursor()
    doc = BibframeSource(converted)

    #print(f'Inserting with oai_id {converted["@id"]} : \n\n{json.dumps(converted)}\n\n')

    original_rowid = cursor.execute("""
    INSERT INTO original(source, data, accepted, oai_id) VALUES(?, ?, ?, ?);
    """, (source, original, accepted, converted["@id"])).lastrowid

    if not accepted:
        connection.commit()
        return

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
        str(doc.level),
        doc.is_swedishlist
    )).lastrowid

    for event in events:
        cursor.execute("""
        INSERT INTO converted_events(converted_id, type, field, path, code, initial_value, result, name, step) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            converted_rowid,
            event["type"],
            event["field"],
            event["path"],
            event["code"],
            event["initial_value"],
            event["result"],
            event["name"],
            event["step"]
        ))

    identifiers = []
    for title in converted["instanceOf"]["hasTitle"]:
        main_title = title.get("mainTitle")
        if main_title is not None and isinstance(main_title, str):
            identifiers.append(main_title) # TODO: STRIP AWAY WHITESPACE ETC
    
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
