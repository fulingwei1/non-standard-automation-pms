-- 权限表结构升级迁移脚本 (SQLite)
-- 版本: 1.0
-- 日期: 2025-01-20
-- 说明: 统一权限表结构，添加 resource, description, is_active, created_at, updated_at 字段
-- 注意: 保持 perm_code 和 perm_name 字段名不变，通过模型映射处理

BEGIN;

-- ============================================
-- 1. 检查并添加缺失的字段
-- ============================================

-- 添加 resource 字段（如果不存在）
-- SQLite 不支持直接检查字段是否存在，使用 try-catch 方式
-- 这里使用 ALTER TABLE ADD COLUMN IF NOT EXISTS（SQLite 3.38+）
-- 如果版本较旧，需要手动检查

-- 添加 resource 字段
-- 注意：SQLite 的 ALTER TABLE ADD COLUMN 不支持 IF NOT EXISTS（SQLite 3.38+才支持）
-- 使用 Python 脚本或手动执行前检查
ALTER TABLE permissions ADD COLUMN resource VARCHAR(50);

-- 添加 description 字段
ALTER TABLE permissions ADD COLUMN description TEXT;

-- 添加 is_active 字段
ALTER TABLE permissions ADD COLUMN is_active BOOLEAN DEFAULT 1;

-- 添加 created_at 字段（如果不存在）
-- 注意：SQLite 不支持在 ADD COLUMN 时使用 CURRENT_TIMESTAMP，先添加字段，后更新数据
ALTER TABLE permissions ADD COLUMN created_at DATETIME;

-- 添加 updated_at 字段（如果不存在）
-- 注意：SQLite 不支持在 ADD COLUMN 时使用 CURRENT_TIMESTAMP，先添加字段，后更新数据
ALTER TABLE permissions ADD COLUMN updated_at DATETIME;

-- ============================================
-- 2. 更新现有数据的默认值
-- ============================================

-- 为所有现有权限设置 is_active = 1（启用）
UPDATE permissions SET is_active = 1 WHERE is_active IS NULL;

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
    WHEN perm_code LIKE '%:%:%' THEN 
        SUBSTR(perm_code, INSTR(perm_code, ':') + 1, 
               INSTR(SUBSTR(perm_code, INSTR(perm_code, ':') + 1), ':') - 1)
    WHEN perm_code LIKE '%:%' THEN 
        SUBSTR(perm_code, 1, INSTR(perm_code, ':') - 1)
    ELSE module
END
WHERE resource IS NULL;

-- 如果提取失败，使用 module 作为 resource
UPDATE permissions 
SET resource = module 
WHERE resource IS NULL OR resource = '';

COMMIT;

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
