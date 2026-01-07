-- ============================================
-- O2C流程完善：发票收款字段迁移
-- 添加发票收款相关字段
-- ============================================

-- 添加发票收款相关字段
ALTER TABLE invoices ADD COLUMN tax_amount DECIMAL(12,2);
ALTER TABLE invoices ADD COLUMN total_amount DECIMAL(12,2);
ALTER TABLE invoices ADD COLUMN payment_status VARCHAR(20);
ALTER TABLE invoices ADD COLUMN due_date DATE;
ALTER TABLE invoices ADD COLUMN paid_amount DECIMAL(12,2) DEFAULT 0;
ALTER TABLE invoices ADD COLUMN paid_date DATE;
ALTER TABLE invoices ADD COLUMN remark TEXT;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_paid_date ON invoices(paid_date);



