-- 售前案例库：对齐金凯博智能报价系统字段口径（2026-06 设计文档）
-- 加工程参数（相似度匹配用）+ 成本闭环（报价vs实际偏差）+ 风险标签
ALTER TABLE presale_knowledge_case ADD COLUMN workpiece_type VARCHAR(100);
ALTER TABLE presale_knowledge_case ADD COLUMN process_flow TEXT;
ALTER TABLE presale_knowledge_case ADD COLUMN cycle_time VARCHAR(100);
ALTER TABLE presale_knowledge_case ADD COLUMN automation_level VARCHAR(50);
ALTER TABLE presale_knowledge_case ADD COLUMN station_count INTEGER;
ALTER TABLE presale_knowledge_case ADD COLUMN robot_count INTEGER;
ALTER TABLE presale_knowledge_case ADD COLUMN vision_count INTEGER;
ALTER TABLE presale_knowledge_case ADD COLUMN plc_requirement VARCHAR(200);
ALTER TABLE presale_knowledge_case ADD COLUMN initial_quote DECIMAL(14, 2);
ALTER TABLE presale_knowledge_case ADD COLUMN final_price DECIMAL(14, 2);
ALTER TABLE presale_knowledge_case ADD COLUMN actual_total_cost DECIMAL(14, 2);
ALTER TABLE presale_knowledge_case ADD COLUMN quote_cost DECIMAL(14, 2);
ALTER TABLE presale_knowledge_case ADD COLUMN actual_margin DECIMAL(5, 2);
ALTER TABLE presale_knowledge_case ADD COLUMN deal_discount DECIMAL(5, 2);
ALTER TABLE presale_knowledge_case ADD COLUMN cost_deviation DECIMAL(5, 2);
ALTER TABLE presale_knowledge_case ADD COLUMN risk_tags JSON;
ALTER TABLE presale_knowledge_case ADD COLUMN reusable_modules JSON;
ALTER TABLE presale_knowledge_case ADD COLUMN is_won VARCHAR(20);
CREATE INDEX IF NOT EXISTS idx_presale_case_equipment ON presale_knowledge_case(equipment_type);
CREATE INDEX IF NOT EXISTS idx_presale_case_industry ON presale_knowledge_case(industry);
CREATE INDEX IF NOT EXISTS idx_presale_case_workpiece ON presale_knowledge_case(workpiece_type);
