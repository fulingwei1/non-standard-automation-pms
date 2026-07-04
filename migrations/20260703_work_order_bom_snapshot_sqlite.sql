-- PROD-08: 工单关联 BOM 版本并保存 BOM 快照信息。

ALTER TABLE work_order ADD COLUMN bom_id INTEGER REFERENCES bom_headers(id);
ALTER TABLE work_order ADD COLUMN bom_no VARCHAR(50);
ALTER TABLE work_order ADD COLUMN bom_version VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_work_order_bom ON work_order (bom_id);
