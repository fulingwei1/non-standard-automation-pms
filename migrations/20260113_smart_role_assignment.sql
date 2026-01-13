-- ============================================
-- 智能角色分配脚本 - 根据岗位自动分配角色
-- 生成日期: 2026-01-13
-- ============================================

BEGIN TRANSACTION;

-- ============================================
-- 1. 确保所有用户至少有 USER 角色
-- ============================================
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'USER')
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
WHERE u.is_active = 1 AND ur.id IS NULL;

-- ============================================
-- 2. 根据部门关键字分配角色
-- ============================================

-- 人事部门 → HR_MGR 或相关角色
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'HR_MGR')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%人事%' OR u.department LIKE '%人力%' OR u.position LIKE '%人事%')
AND u.position LIKE '%主管%' OR u.position LIKE '%经理%';

-- 财务部门 → FINANCE
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'FINANCE')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%财务%' OR u.position LIKE '%财务%' OR u.position LIKE '%会计%');

-- 采购部门 → PU
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'PU')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%采购%' OR u.position LIKE '%采购%')
AND NOT EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = u.id AND r.role_code IN ('PU', 'PU_MGR', 'PU_ENGINEER'));

-- 采购经理 → PU_MGR
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'PU_MGR')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%采购%' OR u.position LIKE '%采购%')
AND (u.position LIKE '%经理%' OR u.position LIKE '%主管%');

-- 销售部门 → SALES
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'SALES')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%销售%' OR u.department LIKE '%市场%' OR u.position LIKE '%销售%')
AND NOT EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = u.id AND r.role_code IN ('SALES', 'SA', 'SALES_DIR'));

-- 销售总监/经理 → SALES_DIR
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'SALES_DIR')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%销售%' OR u.position LIKE '%销售%')
AND (u.position LIKE '%总监%' OR u.position LIKE '%经理%');

-- ============================================
-- 3. 根据岗位关键字分配角色
-- ============================================

-- 项目经理 → PROJECT_MANAGER
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'PROJECT_MANAGER')
FROM users u
WHERE u.is_active = 1
AND (u.position LIKE '%项目经理%' OR u.position LIKE '%PM%');

-- 工程师 → ENGINEER (如果还没有更具体的工程师角色)
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'ENGINEER')
FROM users u
WHERE u.is_active = 1
AND u.position LIKE '%工程师%'
AND NOT EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = u.id AND r.role_code IN ('ME', 'EE', 'SW', 'QA', 'ENGINEER'));

-- 测试工程师 → QA
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'QA')
FROM users u
WHERE u.is_active = 1
AND (u.position LIKE '%测试%' OR u.position LIKE '%品质%' OR u.position LIKE '%质量%')
AND NOT EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = u.id AND r.role_code IN ('QA', 'QA_MGR'));

-- 质量主管/经理 → QA_MGR
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'QA_MGR')
FROM users u
WHERE u.is_active = 1
AND (u.position LIKE '%品质%' OR u.position LIKE '%质量%')
AND (u.position LIKE '%主管%' OR u.position LIKE '%经理%');

-- 售前 → PRESALES
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'PRESALES')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%售前%' OR u.position LIKE '%售前%');

-- 生产相关 → PRODUCTION
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'PRODUCTION')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%生产%' AND NOT u.department LIKE '%装配%')
AND (u.position LIKE '%经理%' OR u.position LIKE '%主管%');

-- 装配/调试 → ASSEMBLER 或 DEBUG
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'ASSEMBLER')
FROM users u
WHERE u.is_active = 1
AND (u.position LIKE '%装配%' OR u.position LIKE '%钳工%' OR u.position LIKE '%电工%' OR u.position LIKE '%接线%')
AND NOT EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = u.id AND r.role_code = 'ASSEMBLER');

INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'DEBUG')
FROM users u
WHERE u.is_active = 1
AND u.position LIKE '%调试%';

-- 仓储/物料 → PMC
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'PMC')
FROM users u
WHERE u.is_active = 1
AND (u.department LIKE '%仓储%' OR u.position LIKE '%仓储%' OR u.position LIKE '%物料%' OR u.position LIKE '%计划%')
AND (u.position LIKE '%主管%' OR u.position LIKE '%经理%');

-- ============================================
-- 4. 根据职级分配管理角色
-- ============================================

-- 总经理/副总 → GM
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'GM')
FROM users u
WHERE u.is_active = 1
AND (u.position LIKE '%总经理%' OR u.position LIKE '%副总%' OR u.position LIKE '%总监%')
AND NOT EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = u.id AND r.role_code = 'GM');

-- 部门经理/主管 → DEPT_MGR
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, (SELECT id FROM roles WHERE role_code = 'DEPT_MGR')
FROM users u
WHERE u.is_active = 1
AND (u.position LIKE '%经理%' OR u.position LIKE '%主管%' OR u.position LIKE '%组长%')
AND NOT EXISTS (SELECT 1 FROM user_roles ur JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = u.id AND r.role_code = 'DEPT_MGR');

-- ============================================
-- 5. 特殊处理：综合管理部、行政等 → USER
-- ============================================
-- 已通过步骤1确保有USER角色

COMMIT;

-- ============================================
-- 验证结果
-- ============================================
SELECT '角色分配完成，统计结果:' as message;

SELECT '无角色用户数' as item,
       (SELECT COUNT(*) FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        WHERE u.is_active = 1 AND ur.id IS NULL) as count
UNION ALL
SELECT '有角色用户数',
       (SELECT COUNT(DISTINCT u.id) FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        WHERE u.is_active = 1)
UNION ALL
SELECT '总用户数',
       (SELECT COUNT(*) FROM users WHERE is_active = 1);
