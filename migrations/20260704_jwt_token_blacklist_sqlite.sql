-- PERM-03: persistent JWT revocation fallback for SQLite.
-- Redis remains the preferred blacklist store; this table keeps revoked JTI
-- visible across workers and restarts when Redis is unavailable.

CREATE TABLE IF NOT EXISTS jwt_token_blacklist (
    jti VARCHAR(128) PRIMARY KEY,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jwt_token_blacklist_expires
ON jwt_token_blacklist(expires_at);
