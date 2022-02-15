import sqlite3
from sqlite3.dbapi2 import connect
import json
import os
from bibframesource import BibframeSource

sqlite_path = "./swepub.sqlite3"

def _set_pragmas(cursor):
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=OFF;")
    cursor.execute("PRAGMA foreign_keys=ON;")

def clean_and_init_storage():
    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    connection = sqlite3.connect(sqlite_path)
    cursor = connection.cursor()
    _set_pragmas(cursor)

    # To allow incremental updates, we must know the last successful (start of-) harvest time
    # for each source
    cursor.execute("""
    CREATE TABLE last_harvest (
        source TEXT PRIMARY KEY,
        last_successful_harvest DATETIME
    );
    """)

    # Because Swepub APIs expose publications as originally harvested, these must be kept.
    cursor.execute("""
    CREATE TABLE original (
        id INTEGER PRIMARY KEY,
        source TEXT,
        oai_id TEXT, -- TODO ADD UNIQUE,
        accepted INTEGER, -- (fake boolean 1/0)
        rejection_cause TEXT,
        data TEXT
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_original_oai_id ON original (oai_id);
    """)

    # This table is used to store log entries (validation/normalization errors etc) for
    # each publication
    cursor.execute("""
    CREATE TABLE converted_audit_events (
        converted_id INTEGER,
        name TEXT,
        step TEXT,
        code TEXT,
        result TEXT,
        initial_value TEXT,
        value TEXT,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_audit_events_converted_id ON converted_audit_events(converted_id);
    """)

    cursor.execute("""
    CREATE TABLE converted_record_info (
        converted_id INTEGER,
        field_name TEXT,
        validation_status TEXT,
        enrichment_status TEXT,
        normalization_status TEXT,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_record_info_converted_id ON converted_record_info(converted_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_record_info_field_name ON converted_record_info(field_name);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_record_info_validation_status ON converted_record_info(validation_status);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_record_info_enrichment_status ON converted_record_info(enrichment_status);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_record_info_normalization_status ON converted_record_info(normalization_status);
    """)

    # After conversion, validation and normalization each publication is stored in this
    # form, for later in use in deduplication.
    cursor.execute("""
    CREATE TABLE converted (
        id INTEGER PRIMARY KEY,
        oai_id TEXT, -- TODO ADD UNIQUE, -- e.g. "oai:DiVA.org:ri-6513"
        data TEXT, -- JSON
        original_id INTEGER,
        date INTEGER, -- year
        source TEXT, -- source code, e.g. "kth", "ltu"
        is_open_access INTEGER,
        classification_level INT, -- 0 = https://id.kb.se/term/swepub/swedishlist/non-peer-reviewed, 1 = peer-reviewed (1 also means "is_swedishlist")
        events TEXT,
        FOREIGN KEY (original_id) REFERENCES original(id) ON DELETE CASCADE
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
    CREATE INDEX idx_converted_classification_level ON converted(classification_level);
    """)

    cursor.execute("""
    CREATE TABLE converted_ssif_1 (
        converted_id INTEGER,
        value INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_ssif_1_converted_id ON converted_ssif_1(converted_id);
    """)
    cursor.execute("""
    CREATE INDEX idx_converted_ssif_1_value ON converted_ssif_1(value);
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
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
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
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
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
    # cluster_id references into the cluster table, but cannot acutally be a formal
    # foreign key, because cluster_id is not (and cannot be) unique. See the cluster
    # definition above.
    cursor.execute("""
    CREATE TABLE finalized (
        id INTEGER PRIMARY KEY,
        cluster_id INTEGER,
        oai_id TEXT,
        data TEXT
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
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
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
        open_access INTEGER,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
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
    CREATE INDEX idx_search_single_open_access ON search_single(open_access);
    """)

    cursor.execute("""
    CREATE TABLE search_doi (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
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
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
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
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
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
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
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
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
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
        finalized_id,
        title,
        keywords
    );
    """)

    cursor.execute("""
    CREATE TABLE stats_audit_events (
        source TEXT,
        date INT,
        label TEXT,
        valid INT DEFAULT 0,
        invalid INT DEFAULT 0
    );
    """)
    cursor.execute("""
    CREATE INDEX idx_stats_audit_events_source ON stats_audit_events(source);
    """)

    cursor.execute("""
    CREATE TABLE stats_field_events (
        field_name TEXT,
        source TEXT,
        date INT,
        v_valid INT DEFAULT 0,
        v_invalid INT DEFAULT 0,
        e_enriched INT DEFAULT 0,
        e_unchanged INT DEFAULT 0,
        e_unsuccessful INT DEFAULT 0,
        n_unchanged INT DEFAULT 0,
        n_normalized INT DEFAULT 0
    );
    """)

    connection.commit()

def open_existing_storage():
    connection = sqlite3.connect(sqlite_path)
    cursor = connection.cursor()
    _set_pragmas(cursor)

def store_original(oai_id, deleted, original, source, accepted, connection, incremental, min_level_errors):
    cursor = connection.cursor()
    if incremental:
        cursor.execute("""
        DELETE FROM original WHERE oai_id = ?;
        """, (oai_id,))
    
    if deleted:
        connection.commit()
        return None

    rejection_cause = None
    if not accepted:
        rejection_cause = json.dumps(min_level_errors)
    original_rowid = cursor.execute("""
    INSERT INTO original(source, data, accepted, oai_id, rejection_cause) VALUES(?, ?, ?, ?, ?);
    """, (source, original, accepted, oai_id, rejection_cause)).lastrowid

    connection.commit()
    return original_rowid

def store_converted(original_rowid, converted, audit_events, field_events, record_info, connection):
    cursor = connection.cursor()
    doc = BibframeSource(converted)

    converted_events = {'audit_events': audit_events, 'field_events': field_events}

    converted_rowid = cursor.execute("""
    INSERT INTO converted(data, original_id, oai_id, date, source, is_open_access, classification_level, events) VALUES(?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        json.dumps(converted),
        original_rowid,
        doc.record_id,
        doc.publication_year,
        doc.source_org_master,
        doc.open_access,
        doc.level,
        json.dumps(converted_events, default=lambda o: o.__dict__) #, default=lambda o: o.__dict__)
    )).lastrowid

    for ssif_1 in doc.ssif_1_codes:
        cursor.execute("""
        INSERT INTO converted_ssif_1(converted_id, value) VALUES(?, ?)
        """, (converted_rowid, ssif_1))

    for field, value in record_info.items():
        cursor.execute("""
        INSERT INTO converted_record_info(
            converted_id, field_name, validation_status, enrichment_status, normalization_status
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            converted_rowid,
            field,
            value['validation_status'],
            value['enrichment_status'],
            value['normalization_status'],
        ))

    for name, events in audit_events.items():
        for event in events:
            cursor.execute("""
            INSERT INTO converted_audit_events(converted_id, code, initial_value, result, name, step, value) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                converted_rowid,
                event.get("code", None),
                event.get("initial_value", None),
                event.get("result", None),
                name,
                event.get("step", None),
                event.get("value", None)
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
    return converted_rowid

def get_connection():
    return sqlite3.connect(sqlite_path)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
