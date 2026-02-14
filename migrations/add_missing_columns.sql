-- 为users表添加缺失的列
-- 检查并添加，SQLite不支持IF NOT EXISTS，所以我们用OR IGNORE

-- 添加reporting_to列
ALTER TABLE users ADD COLUMN reporting_to INTEGER;

-- 添加solution_credits列
ALTER TABLE users ADD COLUMN solution_credits INTEGER DEFAULT 100;
ALTER TABLE users ADD COLUMN credits_updated_at TIMESTAMP;

-- 为roles表添加缺失的列（如果需要）
-- 检查roles表是否缺少source_template_id
-- ALTER TABLE roles ADD COLUMN source_template_id INTEGER;

-- 验证
SELECT 'Columns added successfully' as result;
