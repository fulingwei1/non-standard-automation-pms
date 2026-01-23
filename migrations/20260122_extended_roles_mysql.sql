-- ============================================
-- 角色扩展迁移 - MySQL 版本
-- 版本: 2.0
-- 日期: 2026-01-22
-- 说明: 补充前端使用但数据库缺失的角色
-- 注意：不设置 parent_role_id，汇报关系通过 users.reporting_to 动态管理
-- ============================================

-- ============================================
-- 1. 新增角色（无固定层级关系）
-- ============================================

INSERT INTO roles (
    role_code, role_name, role_type, scope_type, data_scope,
    level, is_system, status, description, parent_id,
    created_at, updated_at
) VALUES
-- 高管扩展角色 (Level 1)
('CHAIRMAN', '董事长', 'SYSTEM', 'GLOBAL', 'ALL', 1, 1, 'ACTIVE',
 '公司最高负责人，战略决策与全局管控', NULL, NOW(), NOW()),

('VICE_CHAIRMAN', '副总经理', 'SYSTEM', 'GLOBAL', 'DEPT', 1, 1, 'ACTIVE',
 '分管业务板块，协助总经理管理', NULL, NOW(), NOW()),

('DONGMI', '董秘', 'SYSTEM', 'GLOBAL', 'ALL', 1, 1, 'ACTIVE',
 '董事会秘书，负责信息披露与股东关系', NULL, NOW(), NOW()),

-- 售前角色 (Level 2-3)
('PRESALES_MGR', '售前经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '售前团队管理，方案审核与资源协调', NULL, NOW(), NOW()),

('PRESALES', '售前工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '技术方案设计，售前支持与演示', NULL, NOW(), NOW()),

('BUSINESS_SUPPORT', '商务支持', 'BUSINESS', 'GLOBAL', 'DEPT', 3, 0, 'ACTIVE',
 '商务流程支持，合同管理，报价协助', NULL, NOW(), NOW()),

-- 客服角色 (Level 2-3)
('CUSTOMER_SERVICE_MGR', '客服经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '客服团队管理，服务质量监控，客户关系维护', NULL, NOW(), NOW()),

('CUSTOMER_SERVICE', '客服工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '客户沟通，问题处理，售后支持', NULL, NOW(), NOW()),

-- HR 角色 (Level 2-3)
('HR_MGR', 'HR经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '人力资源管理，招聘培训，绩效考核', NULL, NOW(), NOW()),

('HR', 'HR专员', 'BUSINESS', 'GLOBAL', 'ALL', 3, 0, 'ACTIVE',
 '人事执行，员工关系，考勤薪酬', NULL, NOW(), NOW()),

-- 仓储角色 (Level 2-3)
('WAREHOUSE_MGR', '仓储经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '仓储团队管理，库存控制，出入库审批', NULL, NOW(), NOW()),

('WAREHOUSE', '仓储管理员', 'BUSINESS', 'GLOBAL', 'DEPT', 3, 0, 'ACTIVE',
 '物料收发，库存盘点，库位管理', NULL, NOW(), NOW()),

-- 生产管理扩展 (Level 1-2)
('MANUFACTURING_DIR', '制造总监', 'SYSTEM', 'GLOBAL', 'DEPT', 1, 0, 'ACTIVE',
 '制造体系管理，生产效率，质量控制', NULL, NOW(), NOW()),

('PRODUCTION_MGR', '生产经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '生产计划执行，团队调度，现场管理', NULL, NOW(), NOW())

ON DUPLICATE KEY UPDATE
    role_name = VALUES(role_name),
    description = VALUES(description),
    parent_id = NULL,
    updated_at = NOW();

-- ============================================
-- 2. 汇报关系管理方式
-- ============================================
--
-- 汇报关系通过 users 表的 reporting_to 字段动态管理：
--
-- 示例：设置某人的直接上级
-- UPDATE users u
-- JOIN users m ON m.username = '制造总监的username'
-- SET u.reporting_to = m.id,
--     u.updated_at = NOW()
-- WHERE u.username = '仓储经理的username';
--
-- 示例：更换上级（随时可以调整）
-- UPDATE users u
-- JOIN users m ON m.username = '财务总监的username'
-- SET u.reporting_to = m.id,
--     u.updated_at = NOW()
-- WHERE u.username = '仓储经理的username';
--
-- ============================================

-- ============================================
-- 3. 部门管理方式
-- ============================================
--
-- 部门负责人通过 departments 表的 manager_id 动态管理：
--
-- 示例：设置仓储部负责人
-- UPDATE departments d
-- JOIN users u ON u.username = '制造总监的username'
-- SET d.manager_id = u.id,
--     d.updated_at = NOW()
-- WHERE d.dept_code = 'WAREHOUSE';
--
-- 示例：更换部门负责人
-- UPDATE departments d
-- JOIN users u ON u.username = '财务总监的username'
-- SET d.manager_id = u.id,
--     d.updated_at = NOW()
-- WHERE d.dept_code = 'WAREHOUSE';
--
-- ============================================

-- ============================================
-- 4. 验证查询
-- ============================================

-- 查看所有新增角色
-- SELECT role_code, role_name, level, data_scope
-- FROM roles
-- WHERE role_code IN (
--     'CHAIRMAN', 'VICE_CHAIRMAN', 'DONGMI',
--     'PRESALES', 'PRESALES_MGR', 'BUSINESS_SUPPORT',
--     'CUSTOMER_SERVICE', 'CUSTOMER_SERVICE_MGR',
--     'HR', 'HR_MGR',
--     'WAREHOUSE', 'WAREHOUSE_MGR',
--     'MANUFACTURING_DIR', 'PRODUCTION_MGR'
-- )
-- ORDER BY level, role_code;

-- 查看用户的汇报关系（动态）
-- SELECT
--     u.username,
--     u.real_name,
--     u.department,
--     u.position,
--     m.username AS manager_username,
--     m.real_name AS manager_name
-- FROM users u
-- LEFT JOIN users m ON u.reporting_to = m.id
-- ORDER BY u.department, u.real_name;

-- 查看部门负责人（动态）
-- SELECT
--     d.dept_code,
--     d.dept_name,
--     u.username AS manager_username,
--     u.real_name AS manager_name
-- FROM departments d
-- LEFT JOIN users u ON d.manager_id = u.id
-- ORDER BY d.dept_code;

-- 查看某部门的所有员工及其汇报关系
-- SELECT
--     e.employee_no,
--     e.name AS employee_name,
--     e.position,
--     u.username,
--     m.username AS manager_username,
--     m.real_name AS manager_name
-- FROM employees e
-- LEFT JOIN users u ON e.id = u.employee_id
-- LEFT JOIN users m ON u.reporting_to = m.id
-- WHERE e.dept_id = (SELECT id FROM departments WHERE dept_code = 'WAREHOUSE')
-- ORDER BY e.position, e.name;
