-- 售前工单增加线索上下文 (SQLite)
-- 日期: 2026-06-07
-- 背景: 线索阶段也需要发起/筛选售前技术支持工单，打通销售线索到售前中心。

ALTER TABLE presale_support_ticket ADD COLUMN lead_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_presale_ticket_lead
ON presale_support_ticket(lead_id);
