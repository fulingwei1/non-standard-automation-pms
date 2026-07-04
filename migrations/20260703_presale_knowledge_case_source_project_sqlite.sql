-- 售前弹药库：给案例库加 source_project_id，关联到 projects 表
-- 用于回溯真实项目成本/技术细节，让"案例"不再与"项目"脱钩
ALTER TABLE presale_knowledge_case ADD COLUMN source_project_id INTEGER;
CREATE INDEX IF NOT EXISTS idx_presale_case_source_project
    ON presale_knowledge_case(source_project_id);
