-- 采购申请自动下单能力增强（SQLite）

ALTER TABLE purchase_requests ADD COLUMN supplier_id INTEGER;
ALTER TABLE purchase_requests ADD COLUMN source_type VARCHAR(20) DEFAULT 'MANUAL';
ALTER TABLE purchase_requests ADD COLUMN source_id INTEGER;
ALTER TABLE purchase_requests ADD COLUMN auto_po_created BOOLEAN DEFAULT 0;
ALTER TABLE purchase_requests ADD COLUMN auto_po_created_at DATETIME;
ALTER TABLE purchase_requests ADD COLUMN auto_po_created_by INTEGER;

ALTER TABLE purchase_orders ADD COLUMN source_request_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_purchase_requests_supplier ON purchase_requests(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_requests_source ON purchase_requests(source_type);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_source_request ON purchase_orders(source_request_id);
