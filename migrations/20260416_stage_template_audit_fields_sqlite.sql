-- 为 stage_templates 补齐审计字段（兼容旧 SQLite 库）
-- 创建日期: 2026-04-16

ALTER TABLE stage_templates ADD COLUMN updated_by INTEGER REFERENCES users(id);
ALTER TABLE stage_templates ADD COLUMN change_description TEXT;
