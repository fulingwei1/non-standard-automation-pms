-- PROD-06: 允许同一 BOM 编号保留多个版本。
-- SQLite 不能直接 DROP UNIQUE 约束，需重建 bom_headers 表。

PRAGMA foreign_keys=OFF;

DROP TABLE IF EXISTS bom_headers_new;

CREATE TABLE bom_headers_new (
    id INTEGER NOT NULL,
    bom_no VARCHAR(50) NOT NULL,
    bom_name VARCHAR(200) NOT NULL,
    project_id INTEGER NOT NULL,
    machine_id INTEGER,
    version VARCHAR(20),
    is_latest BOOLEAN,
    status VARCHAR(20),
    total_items INTEGER,
    total_amount NUMERIC(14, 2),
    approved_by INTEGER,
    approved_at DATETIME,
    remark TEXT,
    created_by INTEGER,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(project_id) REFERENCES projects (id),
    FOREIGN KEY(machine_id) REFERENCES machines (id),
    FOREIGN KEY(approved_by) REFERENCES users (id),
    FOREIGN KEY(created_by) REFERENCES users (id)
);

INSERT INTO bom_headers_new (
    id,
    bom_no,
    bom_name,
    project_id,
    machine_id,
    version,
    is_latest,
    status,
    total_items,
    total_amount,
    approved_by,
    approved_at,
    remark,
    created_by,
    created_at,
    updated_at
)
SELECT
    id,
    bom_no,
    bom_name,
    project_id,
    machine_id,
    version,
    is_latest,
    status,
    total_items,
    total_amount,
    approved_by,
    approved_at,
    remark,
    created_by,
    created_at,
    updated_at
FROM bom_headers;

DROP TABLE bom_headers;
ALTER TABLE bom_headers_new RENAME TO bom_headers;

CREATE INDEX IF NOT EXISTS idx_bom_machine ON bom_headers (machine_id);
CREATE INDEX IF NOT EXISTS idx_bom_no ON bom_headers (bom_no);
CREATE INDEX IF NOT EXISTS idx_bom_project ON bom_headers (project_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_bom_no_version ON bom_headers (bom_no, version);

PRAGMA foreign_keys=ON;
