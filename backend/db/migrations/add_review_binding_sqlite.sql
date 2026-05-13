-- SQLite migration for PR-4 review binding
-- Adds content_hash & review binding tables for chapter_versions

PRAGMA foreign_keys = ON;

ALTER TABLE chapter_versions
    ADD COLUMN content_hash TEXT NOT NULL DEFAULT '';

ALTER TABLE chapter_versions
    ADD COLUMN parent_version_id INTEGER NULL;

ALTER TABLE chapter_versions
    ADD COLUMN generation_attempt INTEGER DEFAULT 0;

ALTER TABLE chapter_versions
    ADD COLUMN retry_reason_codes JSON NULL;

ALTER TABLE chapter_versions
    ADD COLUMN retry_directive TEXT NULL;

ALTER TABLE chapter_versions
    ADD COLUMN validation_summary JSON NULL;

ALTER TABLE chapter_versions
    ADD COLUMN needs_vector_retry BOOLEAN DEFAULT 0;

CREATE TABLE IF NOT EXISTS chapter_version_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_version_id INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    is_stale BOOLEAN NOT NULL DEFAULT 0,
    review_type TEXT NOT NULL,
    payload_json JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_version_id) REFERENCES chapter_versions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reviews_version
    ON chapter_version_reviews (chapter_version_id);

CREATE INDEX IF NOT EXISTS idx_reviews_version_stale
    ON chapter_version_reviews (chapter_version_id, is_stale);

CREATE TABLE IF NOT EXISTS chapter_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    chapter_number INTEGER NOT NULL,
    version_id INTEGER NULL,
    content_hash TEXT NULL,
    global_summary_snapshot TEXT NULL,
    character_states_snapshot JSON NULL,
    plot_arcs_snapshot JSON NULL,
    chapter_summary TEXT NULL,
    word_count INTEGER DEFAULT 0,
    extra JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES novel_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES chapter_versions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshot_project
    ON chapter_snapshots (project_id, chapter_number);
