-- ============================================================================
-- Lead 表增加优势产品字段 (SQLite)
-- 日期: 2026-01-13
-- 描述: 为线索表添加优势产品选择和匹配字段
-- ============================================================================
--
-- 功能说明：
-- 1. 记录线索选择的优势产品列表
-- 2. 标记线索是否涉及优势产品
-- 3. 记录产品匹配类型（优势产品/新产品/未知）
-- 4. 支持产品匹配度分析和中标率预测
--
-- 执行方式：
--   sqlite3 data/app.db < migrations/20260113_add_advantage_product_to_lead_sqlite.sql
--
-- ============================================================================

-- 1. 为 leads 表添加优势产品相关字段
ALTER TABLE leads ADD COLUMN selected_advantage_products TEXT;
ALTER TABLE leads ADD COLUMN product_match_type VARCHAR(20) DEFAULT 'UNKNOWN';
ALTER TABLE leads ADD COLUMN is_advantage_product INTEGER DEFAULT 0;

-- 2. 添加注释说明（SQLite 不支持 COMMENT，这里仅作记录）
-- selected_advantage_products: 选择的优势产品ID列表 (JSON Array)，例如: [1,2,3]
-- product_match_type: 产品匹配类型，可选值:
--   - 'ADVANTAGE': 匹配到优势产品
--   - 'NEW': 新产品（未匹配到优势产品）
--   - 'UNKNOWN': 未知（未进行匹配检查）
-- is_advantage_product: 是否涉及优势产品 (0=否, 1=是)

-- 3. 创建索引以提升查询性能
CREATE INDEX IF NOT EXISTS idx_leads_advantage_product ON leads(is_advantage_product);
CREATE INDEX IF NOT EXISTS idx_leads_product_match_type ON leads(product_match_type);

-- 4. 数据完整性验证
-- 检查字段是否添加成功
SELECT
    name,
    type
FROM pragma_table_info('leads')
WHERE name IN ('selected_advantage_products', 'product_match_type', 'is_advantage_product');

-- 5. 统计现有线索数据
SELECT
    '总线索数' AS metric,
    COUNT(*) AS count
FROM leads
UNION ALL
SELECT
    '已标记优势产品线索' AS metric,
    COUNT(*) AS count
FROM leads
WHERE is_advantage_product = 1
UNION ALL
SELECT
    '匹配类型分布: ADVANTAGE' AS metric,
    COUNT(*) AS count
FROM leads
WHERE product_match_type = 'ADVANTAGE'
UNION ALL
SELECT
    '匹配类型分布: NEW' AS metric,
    COUNT(*) AS count
FROM leads
WHERE product_match_type = 'NEW'
UNION ALL
SELECT
    '匹配类型分布: UNKNOWN' AS metric,
    COUNT(*) AS count
FROM leads
WHERE product_match_type = 'UNKNOWN';

-- ============================================================================
-- 完成提示
-- ============================================================================
--
-- 迁移完成！
--
-- 新增字段：
-- 1. selected_advantage_products (TEXT) - 存储优势产品ID列表的JSON
-- 2. product_match_type (VARCHAR) - 产品匹配类型
-- 3. is_advantage_product (INTEGER) - 是否优势产品标记
--
-- 新增索引：
-- - idx_leads_advantage_product
-- - idx_leads_product_match_type
--
-- 后续操作：
-- 1. 更新 Lead 数据模型 (app/models/sales.py)
-- 2. 更新 Lead Schema (app/schemas/sales.py)
-- 3. 增强 Lead API 端点 (app/api/v1/endpoints/sales/leads.py)
-- 4. 实现产品匹配检查逻辑
--
-- ============================================================================
