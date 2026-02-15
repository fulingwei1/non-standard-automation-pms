-- ================================================================
-- 超级管理员数据一致性约束迁移
-- Team 4: 统一超级管理员判断标准
-- ================================================================

-- 1. 首先修复现有不一致的数据
-- 将所有 is_superuser=TRUE 但 tenant_id 不为空的用户降级为普通用户
UPDATE users 
SET is_superuser = FALSE 
WHERE is_superuser = TRUE AND tenant_id IS NOT NULL;

-- 将所有 tenant_id 为空但 is_superuser=FALSE 的用户设置为超级管理员
-- （假设 tenant_id 为空的用户应该是超级管理员）
UPDATE users 
SET is_superuser = TRUE 
WHERE tenant_id IS NULL AND is_superuser = FALSE;

-- 2. 添加检查约束，强制执行业务规则
-- 规则：超级管理员必须满足 is_superuser=TRUE AND tenant_id IS NULL
-- 反之，租户用户必须满足 is_superuser=FALSE AND tenant_id IS NOT NULL
ALTER TABLE users 
ADD CONSTRAINT chk_superuser_tenant 
    CHECK (
        -- 超级管理员：is_superuser=TRUE 必须 tenant_id IS NULL
        (is_superuser = TRUE AND tenant_id IS NULL) 
        OR 
        -- 租户用户：is_superuser=FALSE 必须 tenant_id IS NOT NULL
        (is_superuser = FALSE AND tenant_id IS NOT NULL)
    );

-- 3. 添加索引以优化超级管理员查询
CREATE INDEX IF NOT EXISTS idx_users_superuser 
ON users (is_superuser, tenant_id) 
WHERE is_superuser = TRUE;

-- 4. 添加注释说明约束规则
COMMENT ON CONSTRAINT chk_superuser_tenant ON users IS 
'确保超级管理员数据一致性：is_superuser=TRUE 必须 tenant_id IS NULL';

-- 验证修复结果
-- 以下查询应该返回 0 条记录
SELECT COUNT(*) as inconsistent_count 
FROM users 
WHERE (is_superuser = TRUE AND tenant_id IS NOT NULL)
   OR (is_superuser = FALSE AND tenant_id IS NULL);

-- 输出修复报告
SELECT 
    '数据修复完成' as status,
    (SELECT COUNT(*) FROM users WHERE is_superuser = TRUE AND tenant_id IS NULL) as superuser_count,
    (SELECT COUNT(*) FROM users WHERE is_superuser = FALSE AND tenant_id IS NOT NULL) as tenant_user_count,
    (SELECT COUNT(*) FROM users WHERE 
        (is_superuser = TRUE AND tenant_id IS NOT NULL) 
        OR (is_superuser = FALSE AND tenant_id IS NULL)
    ) as inconsistent_count;
