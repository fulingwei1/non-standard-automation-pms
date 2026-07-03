-- 销售活动挂钩：给客户沟通记录补 customer_id/opportunity_id/lead_id/project_id（原来只靠名字文本）
ALTER TABLE customer_communications ADD COLUMN customer_id INTEGER;
ALTER TABLE customer_communications ADD COLUMN opportunity_id INTEGER;
ALTER TABLE customer_communications ADD COLUMN lead_id INTEGER;
ALTER TABLE customer_communications ADD COLUMN project_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_comm_customer ON customer_communications(customer_id);
CREATE INDEX IF NOT EXISTS idx_comm_opportunity ON customer_communications(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_comm_lead ON customer_communications(lead_id);
