BEGIN;

CREATE TABLE IF NOT EXISTS sales_ranking_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metrics TEXT NOT NULL,
    created_by INTEGER,
    updated_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_sales_ranking_config_updated_at
    ON sales_ranking_configs (updated_at);

COMMIT;
