-- 权限表结构升级迁移脚本 (MySQL)
-- 版本: 1.0
-- 日期: 2025-01-20
-- 说明: 统一权限表结构，添加 resource, description, is_active, created_at, updated_at 字段
-- 注意: 保持 perm_code 和 perm_name 字段名不变，通过模型映射处理

SET NAMES utf8mb4;

-- ============================================
-- 1. 检查并添加缺失的字段
-- ============================================

-- 添加 resource 字段（如果不存在）
ALTER TABLE permissions 
ADD COLUMN IF NOT EXISTS resource VARCHAR(50) COMMENT '资源类型';

-- 添加 description 字段（如果不存在）
ALTER TABLE permissions 
ADD COLUMN IF NOT EXISTS description TEXT COMMENT '权限描述';

-- 添加 is_active 字段（如果不存在）
ALTER TABLE permissions 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用';

-- 添加 created_at 字段（如果不存在）
ALTER TABLE permissions 
ADD COLUMN IF NOT EXISTS created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间';

-- 添加 updated_at 字段（如果不存在）
ALTER TABLE permissions 
ADD COLUMN IF NOT EXISTS updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间';

-- ============================================
-- 2. 更新现有数据的默认值
-- ============================================

-- 为所有现有权限设置 is_active = 1（启用）
UPDATE permissions SET is_active = TRUE WHERE is_active IS NULL;

-- 为所有现有权限设置 created_at（如果为空）
UPDATE permissions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- 为所有现有权限设置 updated_at（如果为空）
UPDATE permissions SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- ============================================
-- 3. 根据 permission_code 推断 resource 字段值（可选）
-- ============================================

-- 从 permission_code 中提取 resource（格式：module:resource:action）
-- 例如：'project:project:read' -> resource = 'project'
-- 例如：'ecn:ecn:create' -> resource = 'ecn'
UPDATE permissions 
SET resource = CASE 
    WHEN perm_code REGEXP '^[^:]+:[^:]+:[^:]+$' THEN 
        SUBSTRING_INDEX(SUBSTRING_INDEX(perm_code, ':', 2), ':', -1)
    WHEN perm_code REGEXP '^[^:]+:[^:]+$' THEN 
        SUBSTRING_INDEX(perm_code, ':', 1)
    ELSE module
END
WHERE resource IS NULL OR resource = '';

-- 如果提取失败，使用 module 作为 resource
UPDATE permissions 
SET resource = module 
WHERE resource IS NULL OR resource = '';

-- ============================================
-- 验证脚本
-- ============================================
-- 执行后可以运行以下查询验证：
-- SELECT 
--     id, 
--     perm_code, 
--     perm_name, 
--     module, 
--     resource, 
--     action, 
--     description, 
--     is_active, 
--     created_at, 
--     updated_at 
-- FROM permissions 
-- LIMIT 5;
