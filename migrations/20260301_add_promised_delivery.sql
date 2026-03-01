-- 采购订单明细表添加承诺交期字段
ALTER TABLE purchase_order_items ADD COLUMN promised_delivery_date DATE;
ALTER TABLE purchase_order_items ADD COLUMN actual_delivery_date DATE;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_po_promised_date ON purchase_order_items(promised_delivery_date);
CREATE INDEX IF NOT EXISTS idx_po_actual_date ON purchase_order_items(actual_delivery_date);
