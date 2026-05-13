-- Migration: add content hash to chapter_versions and introduce chapter_version_reviews

ALTER TABLE chapter_versions
    ADD COLUMN IF NOT EXISTS content_hash VARCHAR(128) NOT NULL DEFAULT '';

ALTER TABLE chapter_versions
    ADD COLUMN IF NOT EXISTS parent_version_id BIGINT NULL,
    ADD COLUMN IF NOT EXISTS generation_attempt INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS retry_reason_codes JSON NULL,
    ADD COLUMN IF NOT EXISTS retry_directive TEXT NULL,
    ADD COLUMN IF NOT EXISTS validation_summary JSON NULL,
    ADD COLUMN IF NOT EXISTS needs_vector_retry BOOLEAN DEFAULT 0;

ALTER TABLE chapter_versions
    ADD CONSTRAINT fk_versions_parent FOREIGN KEY (parent_version_id) REFERENCES chapter_versions(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS chapter_version_reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chapter_version_id BIGINT NOT NULL,
    content_hash VARCHAR(128) NOT NULL,
    is_stale BOOLEAN NOT NULL DEFAULT 0,
    review_type VARCHAR(64) NOT NULL,
    payload_json JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_reviews_version (chapter_version_id),
    INDEX idx_reviews_version_stale (chapter_version_id, is_stale),
    CONSTRAINT fk_reviews_version FOREIGN KEY (chapter_version_id) REFERENCES chapter_versions(id) ON DELETE CASCADE
);

ALTER TABLE chapter_snapshots
    ADD COLUMN IF NOT EXISTS version_id BIGINT NULL,
    ADD COLUMN IF NOT EXISTS content_hash VARCHAR(128) NULL;

ALTER TABLE chapter_snapshots
    ADD CONSTRAINT fk_snapshot_version FOREIGN KEY (version_id) REFERENCES chapter_versions(id) ON DELETE SET NULL;
