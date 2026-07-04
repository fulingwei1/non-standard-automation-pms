-- PERM-13: cross-worker permission cache revision table for SQLite.
-- Permission/role changes bump this revision so workers using local memory
-- cache can detect stale permission payloads immediately.

CREATE TABLE IF NOT EXISTS permission_cache_revisions (
    scope VARCHAR(64) PRIMARY KEY,
    revision INTEGER NOT NULL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
