-- EBC-2: ecn_bom_changes.ecn_id 外键误指向遗留表 ecn_records，应指向 ecn(id)。重建表修正。
PRAGMA foreign_keys=OFF;
CREATE TABLE ecn_bom_changes_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ecn_id INTEGER NOT NULL,
    bom_id INTEGER,
    project_id INTEGER,
    material_code VARCHAR(100),
    change_action VARCHAR(20) NOT NULL,
    old_value JSON,
    new_value JSON,
    cost_impact DECIMAL(14,2) DEFAULT 0,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecn_id) REFERENCES ecn(id)
);
INSERT INTO ecn_bom_changes_new
    SELECT * FROM ecn_bom_changes WHERE ecn_id IN (SELECT id FROM ecn);
DROP TABLE ecn_bom_changes;
ALTER TABLE ecn_bom_changes_new RENAME TO ecn_bom_changes;
CREATE INDEX idx_bom_change_ecn ON ecn_bom_changes(ecn_id);
CREATE INDEX idx_bom_change_bom ON ecn_bom_changes(bom_id);
PRAGMA foreign_keys=ON;
