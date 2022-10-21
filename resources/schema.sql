-- To allow incremental updates, we must know the last successful (start of-) harvest time
-- for each source
CREATE TABLE last_harvest (
    source TEXT PRIMARY KEY,
    last_successful_harvest DATETIME
);


CREATE TABLE harvest_history (
    id TEXT PRIMARY KEY, -- uuid4
    source TEXT,
    harvest_start DATETIME,
    harvest_completed DATETIME,
    harvest_succeeded INT,
    successes INT,
    rejected INT,
    deleted INT,
    failures INT
);
CREATE INDEX idx_harvest_history_source ON harvest_history (source);


-- Because Swepub APIs expose publications as originally harvested, these must be kept.
CREATE TABLE original (
    id INTEGER PRIMARY KEY,
    source TEXT,
    source_subset TEXT,
    oai_id TEXT UNIQUE, -- NOTE: if you remove UNIQUE for whatever reason, _do_ create an index on oai_id
    accepted INTEGER, -- (fake boolean 1/0)
    data TEXT
);
CREATE INDEX idx_original_source ON original (source);


CREATE TABLE rejected (
    id INTEGER PRIMARY KEY,
    harvest_id TEXT,
    oai_id TEXT,
    rejection_cause,
    FOREIGN KEY (harvest_id) REFERENCES harvest_history(id) ON DELETE CASCADE
);
CREATE INDEX idx_rejected_harvest_id ON rejected(harvest_id);


-- This table is used to store log entries (validation/normalization errors etc.) for
-- each publication
CREATE TABLE converted_record_info (
    converted_id INTEGER,
    source TEXT,
    date INTEGER,
    field_name TEXT,
    validation_status INTEGER,
    enrichment_status INTEGER,
    normalization_status INTEGER,
    audit_name TEXT,
    audit_code TEXT,
    audit_result INTEGER,
    FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
);
CREATE INDEX idx_converted_record_info_converted_id ON converted_record_info(converted_id);
CREATE INDEX idx_converted_record_info_field_name ON converted_record_info(field_name);
CREATE INDEX idx_converted_record_info_validation_status ON converted_record_info(validation_status);
CREATE INDEX idx_converted_record_info_enrichment_status ON converted_record_info(enrichment_status);
CREATE INDEX idx_converted_record_info_normalization_status ON converted_record_info(normalization_status);
CREATE INDEX idx_converted_record_info_source_field_name ON converted_record_info(source, field_name);
CREATE INDEX idx_converted_record_info_source_date_field_name ON converted_record_info(source, date, field_name);
CREATE INDEX idx_converted_record_info_audit_code ON converted_record_info(audit_code);
CREATE INDEX idx_converted_record_info_source_audit_code ON converted_record_info(source, audit_code);
CREATE INDEX idx_converted_record_info_source_date_audit_code ON converted_record_info(source, date, audit_code);


-- After conversion, validation and normalization each publication is stored in this
-- form, for later in use in deduplication.
-- The original_id foreign key is *NOT* ON DELETE CASCADE, because we need to keep the
-- (mostly-emptied) converted record around. See triggers below.
CREATE TABLE converted (
    id INTEGER PRIMARY KEY,
    oai_id TEXT UNIQUE, -- e.g. "oai:DiVA.org:ri-6513"
    data TEXT, -- JSON
    original_id INTEGER,
    date INTEGER, -- year
    source TEXT, -- source code, e.g. "kth", "ltu"
    is_open_access INTEGER,
    classification_level INT, -- 0 = https://id.kb.se/term/swepub/swedishlist/non-peer-reviewed, 1 = peer-reviewed (1 also means "is_swedishlist;
    has_ssif_1 INTEGER,
    events TEXT,
    modified INTEGER DEFAULT (strftime('%s', 'now')), -- seconds since epoch
    deleted INTEGER DEFAULT 0,-- bool
    FOREIGN KEY (original_id) REFERENCES original(id)
);
CREATE INDEX idx_converted_oai_id ON converted(oai_id);
CREATE INDEX idx_converted_date ON converted(date);
CREATE INDEX idx_converted_source ON converted(source);
CREATE INDEX idx_converted_is_open_access ON converted(is_open_access);
CREATE INDEX idx_converted_classification_level ON converted(classification_level);
CREATE INDEX idx_converted_has_ssif_1 ON converted(has_ssif_1);
CREATE INDEX idx_converted_modified ON converted(modified);
CREATE INDEX idx_converted_deleted ON converted(deleted);
CREATE INDEX idx_converted_original_id ON converted(original_id);
CREATE INDEX idx_converted_source_deleted ON converted(source, deleted);
CREATE INDEX idx_converted_source_deleted_date ON converted(source, deleted, date);


CREATE TABLE converted_ssif_1 (
    converted_id INTEGER,
    value INTEGER,
    FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
);
CREATE INDEX idx_converted_ssif_1_converted_id ON converted_ssif_1(converted_id);
CREATE INDEX idx_converted_ssif_1_value ON converted_ssif_1(value);

-- To facilitate deduplication, store all of each publication's ids (regardless of type)
-- in this table. This includes (a mangled form of) mainTitles. Grouping on
-- 'identifier' in this table, will produce the raw candidates for deduplication.
-- These, to be clear, will overlap. But overlapping clusters will be joined in a later
-- step. This table should be considered temporary and dropped after deduplication.
CREATE TABLE clusteringidentifiers (
    id INTEGER PRIMARY KEY,
    identifier TEXT,
    converted_id INTEGER,
    FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
);
CREATE INDEX idx_clusteringidentifiers_convertedid ON clusteringidentifiers(converted_id);


-- Deduplicated clusters, multiple rows per cluster. So for example, a cluster consisting
-- of publications A, B and C would look something like:
-- cluster_id | converted_id
-- ---------------------------
-- 123        | A
-- 123        | B
-- 123        | C
-- ---------------------------
-- These may initially overlap (publication A may be in more than one cluster).
-- But any overlaps should have been joined into a single cluster by the end of deduplication.
CREATE TABLE cluster (
    cluster_id INTEGER,
    converted_id INTEGER,
    FOREIGN KEY (converted_id) REFERENCES converted(id) ON DELETE CASCADE
);
CREATE INDEX idx_clusters_clusterid ON cluster (cluster_id);
CREATE INDEX idx_clusters_convertedid ON cluster (converted_id);


-- The final form of a publication in swepub. Each row in this table contains a merged
-- publication, that represents one of the clusters found in the deduplication process.
-- cluster_id references into the cluster table, but cannot acutally be a formal
-- foreign key, because cluster_id is not (and cannot be) unique. See the cluster
-- definition above.
CREATE TABLE finalized (
    id INTEGER PRIMARY KEY,
    cluster_id INTEGER,
    oai_id TEXT UNIQUE,
    data TEXT
);
CREATE INDEX idx_finalized_oai_id ON finalized(oai_id);
CREATE INDEX idx_finalized_cluster_id ON finalized(cluster_id);


CREATE TABLE search_single (
    id INTEGER PRIMARY KEY,
    finalized_id INTEGER,
    year INTEGER,
    content_marking TEXT,
    publication_status TEXT,
    swedish_list INTEGER,
    open_access INTEGER,
    autoclassified INTEGER,
    doaj INTEGER,
    FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
);
CREATE INDEX idx_search_single_finalized_id ON search_single(finalized_id);
CREATE INDEX idx_search_single_finalized_year ON search_single(year);
CREATE INDEX idx_search_single_finalized_id_year ON search_single(finalized_id, year);
CREATE INDEX idx_search_single_finalized_content_marking ON search_single(content_marking);
CREATE INDEX idx_search_single_publication_status ON search_single(publication_status);
CREATE INDEX idx_search_single_swedish_list ON search_single(swedish_list);
CREATE INDEX idx_search_single_open_access ON search_single(open_access);
CREATE INDEX idx_search_single_autoclassified ON search_single(autoclassified);
CREATE INDEX idx_search_single_doaj ON search_single(doaj);


CREATE TABLE search_doi (
    finalized_id INTEGER,
    value TEXT,
    FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
);
CREATE INDEX idx_search_doi_finalized_id ON search_doi(finalized_id);
CREATE INDEX idx_search_doi_value ON search_doi(value);


CREATE TABLE search_genre_form (
    finalized_id INTEGER,
    value TEXT,
    FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
);
CREATE INDEX idx_search_genre_form_finalized_id ON search_genre_form(finalized_id);
CREATE INDEX idx_search_genre_form_value ON search_genre_form(value);
-- case-insensitive index needed for LIKE searches
CREATE INDEX idx_search_genre_form_value_nocase ON search_genre_form(value COLLATE NOCASE);


CREATE TABLE search_subject (
    finalized_id INTEGER,
    value INTEGER,
    FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
);
CREATE INDEX idx_search_subject_finalized_id ON search_subject(finalized_id);
CREATE INDEX idx_search_subject_value ON search_subject(value);


CREATE TABLE search_creator (
    finalized_id INTEGER,
    orcid TEXT,
    family_name TEXT,
    given_name TEXT,
    local_id TEXT,
    local_id_by TEXT,
    FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
);
CREATE INDEX idx_search_creator_finalized_id ON search_creator(finalized_id);
CREATE INDEX idx_search_creator_orcid ON search_creator(orcid);
CREATE INDEX idx_search_creator_family_name ON search_creator(family_name);
CREATE INDEX idx_search_creator_given_name ON search_creator(given_name);
CREATE INDEX idx_search_creator_local_id ON search_creator(local_id);
CREATE INDEX idx_search_creator_local_id_by ON search_creator(local_id_by);


CREATE TABLE search_org (
    finalized_id INTEGER,
    value TEXT,
    FOREIGN KEY (finalized_id) REFERENCES finalized(id) ON DELETE CASCADE
);
CREATE INDEX idx_search_org_finalized_id ON search_org(finalized_id);
CREATE INDEX idx_search_org_value ON search_org(value);
CREATE INDEX idx_search_org_value_finalized_id ON search_org(value, finalized_id);


CREATE VIRTUAL TABLE search_fulltext USING FTS5 (
    finalized_id,
    title,
    keywords
);


CREATE TABLE stats_audit_events (
    source TEXT,
    date INT,
    label TEXT,
    valid INT DEFAULT 0,
    invalid INT DEFAULT 0
);
CREATE INDEX idx_stats_audit_events_source ON stats_audit_events(source);


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


CREATE TABLE stats_converted (
    source TEXT,
    date INT,
    total INT,
    open_access INT DEFAULT 0,
    swedishlist INT DEFAULT 0,
    has_ssif_1 INT DEFAULT 0
);
CREATE INDEX idx_stats_converted ON stats_converted(source);


CREATE TABLE stats_ssif_1 (
    source TEXT,
    date INT,
    ssif_1 INT,
    total INT
);
CREATE INDEX idx_stats_ssif_1_source ON stats_ssif_1(source);


-- When an original is deleted, we *don't* remove the corresponding converted record,
-- because we need to keep information about the deletion for the legacy search sync.
-- However, we can remove most of the data, and set deleted=1, which will trigger the
-- other trigger below.
-- We also bump the `modified` timestamp of any other records belonging to the same
-- cluster, so that these will be properly updated by the legacy search sync.
CREATE TRIGGER set_deleted_on_converted BEFORE DELETE ON original
BEGIN
    UPDATE
        converted
    SET
        data = null, original_id = null, events = null, date = null, source = null, is_open_access = null, has_ssif_1 = null, classification_level = null, modified = (strftime('%s', 'now')), deleted = 1
    WHERE
        original_id = OLD.id;
END;

-- _Normally_ deletion of the following would be handled by "ON DELETE CASCADE" on the foreign key
-- relationship to converted.id, but since we need to keep track of what has been deleted when
-- updating the legacy search database, we can't remove the entire `converted` record.

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

    DELETE FROM converted_record_info WHERE converted_record_info.converted_id = OLD.id;
    DELETE FROM converted_ssif_1 WHERE converted_ssif_1.converted_id = OLD.id;
    DELETE FROM clusteringidentifiers WHERE clusteringidentifiers.converted_id = OLD.id;
    DELETE FROM cluster WHERE cluster.converted_id = OLD.id;
END;
