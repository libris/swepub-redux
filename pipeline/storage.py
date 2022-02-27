import sqlite3
import orjson as json
import os
from bibframesource import BibframeSource


def _set_pragmas(cursor):
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=OFF")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA cache_size=-64000")  # negative number = kibibytes
    cursor.execute("PRAGMA temp_store=MEMORY")


def get_sqlite_path():
    return os.getenv("SWEPUB_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../swepub.sqlite3"))


def storage_exists():
    return os.path.exists(get_sqlite_path())


def clean_and_init_storage():
    sqlite_path = get_sqlite_path()

    if os.path.exists(sqlite_path):
        os.remove(sqlite_path)
    if os.path.exists(f"{sqlite_path}-wal"):
        os.remove(f"{sqlite_path}-wal")
    if os.path.exists(f"{sqlite_path}-shm"):
        os.remove(f"{sqlite_path}-shm")
    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()
    _set_pragmas(cur)

    # To allow incremental updates, we must know the last successful (start of-) harvest time
    # for each source
    cur.execute("""
    CREATE TABLE last_harvest (
        source TEXT PRIMARY KEY,
        last_successful_harvest DATETIME
    );
    """)

    cur.execute("""
    CREATE TABLE harvest_history (
        id TEXT PRIMARY KEY, -- uuid4
        source TEXT,
        harvest_start DATETIME,
        harvest_completed DATETIME,
        successes INT,
        rejected INT
    );
    """)
    cur.execute("CREATE INDEX idx_harvest_history_source ON harvest_history (source)")

    # Because Swepub APIs expose publications as originally harvested, these must be kept.
    cur.execute("""
    CREATE TABLE original (
        id INTEGER PRIMARY KEY,
        source TEXT,
        source_subset TEXT,
        oai_id TEXT UNIQUE, -- NOTE: if you remove UNIQUE for whatever reason, _do_ create an index on oai_id
        accepted INTEGER, -- (fake boolean 1/0)
        data TEXT
    );
    """)
    cur.execute("CREATE INDEX idx_original_source ON original (source)")

    cur.execute("""
    CREATE TABLE rejected (
        id INTEGER PRIMARY KEY,
        harvest_id TEXT,
        oai_id TEXT,
        rejection_cause,
        FOREIGN KEY (harvest_id) REFERENCES harvest_history(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_rejected_harvest_id ON rejected(harvest_id)")

    # This table is used to store log entries (validation/normalization errors etc.) for
    # each publication
    cur.execute("""
    CREATE TABLE converted_audit_events (
        converted_id INTEGER,
        name TEXT,
        code TEXT,
        result TEXT,
        initial_value TEXT,
        value TEXT,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_converted_audit_events_converted_id ON converted_audit_events(converted_id)")

    cur.execute("""
    CREATE TABLE converted_record_info (
        converted_id INTEGER,
        field_name TEXT,
        validation_status TEXT,
        enrichment_status TEXT,
        normalization_status TEXT,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_converted_record_info_converted_id ON converted_record_info(converted_id)")
    cur.execute("CREATE INDEX idx_converted_record_info_field_name ON converted_record_info(field_name)")
    cur.execute("CREATE INDEX idx_converted_record_info_validation_status ON converted_record_info(validation_status)")
    cur.execute("CREATE INDEX idx_converted_record_info_enrichment_status ON converted_record_info(enrichment_status)")
    cur.execute("CREATE INDEX idx_converted_record_info_normalization_status ON converted_record_info(normalization_status)")

    # After conversion, validation and normalization each publication is stored in this
    # form, for later in use in deduplication.
    # The original_id foreign key is *NOT* ON DELETE CASCADE, because we need to keep the (mostly-emptied)
    # converted record around. See triggers below.
    cur.execute("""
    CREATE TABLE converted (
        id INTEGER PRIMARY KEY,
        oai_id TEXT UNIQUE, -- e.g. "oai:DiVA.org:ri-6513"
        data TEXT, -- JSON
        original_id INTEGER,
        date INTEGER, -- year
        source TEXT, -- source code, e.g. "kth", "ltu"
        is_open_access INTEGER,
        classification_level INT, -- 0 = https://id.kb.se/term/swepub/swedishlist/non-peer-reviewed, 1 = peer-reviewed (1 also means "is_swedishlist")
        events TEXT,
        modified INTEGER DEFAULT (strftime('%s', 'now')), -- seconds since epoch
        deleted INTEGER DEFAULT 0,-- bool
        FOREIGN KEY (original_id) REFERENCES original(id)
    );
    """)
    cur.execute("CREATE INDEX idx_converted_oai_id ON converted(oai_id)")
    cur.execute("CREATE INDEX idx_converted_date ON converted(date)")
    cur.execute("CREATE INDEX idx_converted_source ON converted(source)")
    cur.execute("CREATE INDEX idx_converted_is_open_access ON converted(is_open_access)")
    cur.execute("CREATE INDEX idx_converted_classification_level ON converted(classification_level)")
    cur.execute("CREATE INDEX idx_converted_modified ON converted(modified)")
    cur.execute("CREATE INDEX idx_converted_deleted ON converted(deleted)")
    cur.execute("CREATE INDEX idx_converted_original_id ON converted(original_id)")

    cur.execute("""
    CREATE TABLE converted_ssif_1 (
        converted_id INTEGER,
        value INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_converted_ssif_1_converted_id ON converted_ssif_1(converted_id)")
    cur.execute("CREATE INDEX idx_converted_ssif_1_value ON converted_ssif_1(value)")

    # To facilitate deduplication, store all of each publication's ids (regardless of type)
    # in this table. This includes (a mangled form of) mainTitles. Grouping on
    # 'identifier' in this table, will produce the raw candidates for deduplication.
    # These, to be clear, will overlap. But overlapping clusters will be joined in a later
    # step. This table should be considered temporary and dropped after deduplication.
    cur.execute("""
    CREATE TABLE clusteringidentifiers (
        id INTEGER PRIMARY KEY,
        identifier TEXT,
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_clusteringidentifiers_convertedid ON clusteringidentifiers(converted_id)")

    # Deduplicated clusters, multiple rows per cluster. So for example, a cluster consisting
    # of publications A, B and C would look something like:
    # cluster_id | converted_id
    # ---------------------------
    # 123        | A
    # 123        | B
    # 123        | C
    # ---------------------------
    # These may initially overlap (publication A may be in more than one cluster).
    # But any overlaps should have been joined into a single cluster by the end of deduplication.
    cur.execute("""
    CREATE TABLE cluster (
        cluster_id INTEGER,
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_clusters_clusterid ON cluster (cluster_id)")
    cur.execute("CREATE INDEX idx_clusters_convertedid ON cluster (converted_id)")

    # The final form of a publication in swepub. Each row in this table contains a merged
    # publication, that represents one of the clusters found in the deduplication process.
    # cluster_id references into the cluster table, but cannot acutally be a formal
    # foreign key, because cluster_id is not (and cannot be) unique. See the cluster
    # definition above.
    cur.execute("""
    CREATE TABLE finalized (
        id INTEGER PRIMARY KEY,
        cluster_id INTEGER,
        oai_id TEXT UNIQUE,
        data TEXT
    );
    """)
    cur.execute("CREATE INDEX idx_finalized_oai_id ON finalized(oai_id)")
    cur.execute("CREATE INDEX idx_finalized_cluster_id ON finalized(cluster_id)")

    # To facilitate "auto classification", store (for each publication) the N rarest
    # words that occur in that publication's abstract.
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
    cur.execute("""
    CREATE TABLE abstract_rarest_words (
        id INTEGER PRIMARY KEY,
        word TEXT,
        converted_id INTEGER,
        FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_abstract_rarest_words ON abstract_rarest_words (word, converted_id)")
    cur.execute("CREATE INDEX idx_abstract_rarest_words_id ON abstract_rarest_words (converted_id)")

    # In order to calculate values (rarity) for the above table, we also need an answer
    # to the question:
    #
    # How many times does 'word' occur inside abstracts of any of our publications?
    #
    # This is a temporary table, it should be dropped after AutoClassification
    cur.execute("""
    CREATE TABLE abstract_total_word_counts (
        id INTEGER PRIMARY KEY,
        word TEXT,
        occurrences INTEGER
    );
    """)
    cur.execute("CREATE INDEX idx_abstract_total_word_counts ON abstract_total_word_counts (word, occurrences)")

    # SUGGESTED BY SQLITE: CREATE INDEX abstract_total_word_counts_idx_77e8bc04 ON abstract_total_word_counts(word, occurrences);

    cur.execute("""
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
    cur.execute("CREATE INDEX idx_search_single_finalized_id ON search_single(finalized_id)")
    cur.execute("CREATE INDEX idx_search_single_finalized_year ON search_single(year)")
    cur.execute("CREATE INDEX idx_search_single_finalized_content_marking ON search_single(content_marking)")
    cur.execute("CREATE INDEX idx_search_single_publication_status ON search_single(publication_status)")
    cur.execute("CREATE INDEX idx_search_single_swedish_list ON search_single(swedish_list)")
    cur.execute("CREATE INDEX idx_search_single_open_access ON search_single(open_access)")

    cur.execute("""
    CREATE TABLE search_doi (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_search_doi_finalized_id ON search_doi(finalized_id)")
    cur.execute("CREATE INDEX idx_search_doi_value ON search_doi(value)")

    cur.execute("""
    CREATE TABLE search_genre_form (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_search_genre_form_finalized_id ON search_genre_form(finalized_id)")
    cur.execute("CREATE INDEX idx_search_genre_form_value ON search_genre_form(value)")

    cur.execute("""
    CREATE TABLE search_subject (
        finalized_id INTEGER,
        value INTEGER,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_search_subject_finalized_id ON search_subject(finalized_id)")
    cur.execute("CREATE INDEX idx_search_subject_value ON search_subject(value)")

    cur.execute("""
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
    cur.execute("CREATE INDEX idx_search_creator_finalized_id ON search_creator(finalized_id)")
    cur.execute("CREATE INDEX idx_search_creator_orcid ON search_creator(orcid)")
    cur.execute("CREATE INDEX idx_search_creator_family_name ON search_creator(family_name)")
    cur.execute("CREATE INDEX idx_search_creator_given_name ON search_creator(given_name)")
    cur.execute("CREATE INDEX idx_search_creator_local_id ON search_creator(local_id)")
    cur.execute("CREATE INDEX idx_search_creator_local_id_by ON search_creator(local_id_by)")

    cur.execute("""
    CREATE TABLE search_org (
        finalized_id INTEGER,
        value TEXT,
        FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
    );
    """)
    cur.execute("CREATE INDEX idx_search_org_finalized_id ON search_org(finalized_id)")
    cur.execute("CREATE INDEX idx_search_org_value ON search_org(value)")

    cur.execute("""
    CREATE VIRTUAL TABLE search_fulltext USING FTS5 (
        finalized_id,
        title,
        keywords
    );
    """)

    cur.execute("""
    CREATE TABLE stats_audit_events (
        source TEXT,
        date INT,
        label TEXT,
        valid INT DEFAULT 0,
        invalid INT DEFAULT 0
    );
    """)
    cur.execute("CREATE INDEX idx_stats_audit_events_source ON stats_audit_events(source)")

    cur.execute("""
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

    # When an original is deleted, we *don't* remove the corresponding converted record,
    # because we need to keep information about the deletion for the legacy search sync.
    # However, we can remove most of the data, and set deleted=1, which will trigger the
    # other trigger below.
    # We also bump the `modified` timestamp of any other records belonging to the same
    # cluster, so that these will be properly updated by the legacy search sync.
    cur.execute("""
    CREATE TRIGGER set_deleted_on_converted BEFORE DELETE ON original
    BEGIN
        UPDATE
            converted
        SET
            data = null, original_id = null, events = null, date = null, source = null, is_open_access = null, classification_level = null, modified = (strftime('%s', 'now')), deleted = 1
        WHERE
            original_id = OLD.id;
    END
    """)

    # _Normally_ deletion of the following would be handled by "ON DELETE CASCADE" on the foreign key
    # relationship to converted.id, but since we need to keep track of what has been deleted when
    # updating the legacy search database, we can't remove the entire `converted` record.
    cur.execute("""
    CREATE TRIGGER remove_converted_stuff_on_deleted AFTER UPDATE OF deleted ON converted WHEN NEW.deleted = 1
    BEGIN
        UPDATE
            converted
        SET
            modified = (strftime('%s', 'now'))
        WHERE
            id IN (
                SELECT converted_id FROM cluster WHERE cluster_id IN (
                    SELECT cluster_id FROM cluster WHERE converted_id = OLD.id
                ) AND converted_id != OLD.id
            );

        DELETE FROM converted_audit_events WHERE converted_audit_events.converted_id = OLD.id;
        DELETE FROM converted_record_info WHERE converted_record_info.converted_id = OLD.id;
        DELETE FROM converted_ssif_1 WHERE converted_ssif_1.converted_id = OLD.id;
        DELETE FROM clusteringidentifiers WHERE clusteringidentifiers.converted_id = OLD.id;
        DELETE FROM cluster WHERE cluster.converted_id = OLD.id;
        DELETE FROM abstract_rarest_words WHERE abstract_rarest_words.converted_id = OLD.id;
    END
    """)

    con.commit()


def store_original(oai_id, deleted, original, source, source_subset, accepted, connection, incremental, min_level_errors, harvest_id):
    cursor = connection.cursor()
    if incremental:
        cursor.execute("""
        DELETE FROM original WHERE oai_id = ?;
        """, (oai_id,))

    if deleted:
        connection.commit()
        return None

    if not accepted:
        cursor.execute("""
        INSERT INTO rejected(harvest_id, oai_id, rejection_cause) VALUES(?, ?, ?);
        """, (harvest_id, oai_id, json.dumps(min_level_errors)))

    # It *shouldn't* happen that an OAI ID occurs twice in the same dataset, but it can happen...
    original_rowid = cursor.execute("""
    INSERT INTO
        original(source, source_subset, data, accepted, oai_id)
    VALUES
        (?, ?, ?, ?, ?)
    ON CONFLICT(oai_id) DO UPDATE SET
        source=excluded.source, source_subset=excluded.source_subset, data=excluded.data, accepted=excluded.accepted, oai_id=excluded.oai_id
    """, (source, source_subset, original, accepted, oai_id)).lastrowid

    # ...and in the rare case that it does happen, we don't get a lastrowid, so we have to fetch it separately:
    if not original_rowid:
        original_rowid = cursor.execute("SELECT id FROM original WHERE oai_id = ?", [oai_id]).fetchone()[0]

    connection.commit()
    return original_rowid


def store_converted(original_rowid, converted, audit_events, field_events, record_info, connection):
    cursor = connection.cursor()
    doc = BibframeSource(converted)
    converted_events = {'audit_events': audit_events, 'field_events': field_events}

    converted_rowid = cursor.execute("""
    INSERT INTO
        converted(data, original_id, oai_id, date, source, is_open_access, classification_level, events)
    VALUES
        (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(oai_id) DO UPDATE SET
        data = excluded.data, original_id = excluded.original_id, oai_id = excluded.oai_id, date = excluded.date, source = excluded.source, is_open_access = excluded.is_open_access, classification_level = excluded.classification_level, events = excluded.events, deleted = 0
    """, (
        json.dumps(converted),
        original_rowid,
        doc.record_id,
        doc.publication_year,
        doc.source_org_master,
        doc.open_access,
        doc.level,
        json.dumps(converted_events, default=lambda o: o.__dict__)
    )).lastrowid

    # If we inserted a *new* record into converted above, we could just get .lastrowid; but if
    # the row already exists, that won't work.
    if not converted_rowid:
        converted_rowid = cursor.execute("SELECT id FROM converted WHERE oai_id = ?", [doc.record_id]).fetchone()[0]

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
            if event.get("value"):
                value = json.dumps(event.get("value"))
            else:
                value = None

            cursor.execute("""
            INSERT INTO converted_audit_events(converted_id, code, initial_value, result, name, value) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                converted_rowid,
                event.get("code", None),
                event.get("initial_value", None),
                event.get("result", None),
                name,
                value
            ))

    identifiers = []
    for title in converted["instanceOf"]["hasTitle"]:
        main_title = title.get("mainTitle")
        if main_title is not None and isinstance(main_title, str):
            identifiers.append(main_title)  # TODO: STRIP AWAY WHITESPACE ETC
    
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
    connection = sqlite3.connect(get_sqlite_path())
    cursor = connection.cursor()
    _set_pragmas(cursor)
    return connection


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
