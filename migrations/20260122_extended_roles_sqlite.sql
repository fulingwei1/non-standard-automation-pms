-- ============================================
-- 角色扩展迁移 - SQLite 版本
-- 版本: 2.0
-- 日期: 2026-01-22
-- 说明: 补充前端使用但数据库缺失的角色
-- 注意：不设置 parent_role_id，汇报关系通过 users.reporting_to 动态管理
-- ============================================

-- PRAGMA foreign_keys = ON;  -- Disabled for migration

-- ============================================
-- 1. 新增角色（无固定层级关系）
-- ============================================

INSERT OR REPLACE INTO roles (
    role_code, role_name, role_type, scope_type, data_scope,
    level, is_system, status, description, parent_id
) VALUES
-- 高管扩展角色 (Level 1)
('CHAIRMAN', '董事长', 'SYSTEM', 'GLOBAL', 'ALL', 1, 1, 'ACTIVE',
 '公司最高负责人，战略决策与全局管控', NULL),

('VICE_CHAIRMAN', '副总经理', 'SYSTEM', 'GLOBAL', 'DEPT', 1, 1, 'ACTIVE',
 '分管业务板块，协助总经理管理', NULL),

('DONGMI', '董秘', 'SYSTEM', 'GLOBAL', 'ALL', 1, 1, 'ACTIVE',
 '董事会秘书，负责信息披露与股东关系', NULL),

-- 售前角色 (Level 2-3)
('PRESALES_MGR', '售前经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '售前团队管理，方案审核与资源协调', NULL),

('PRESALES', '售前工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '技术方案设计，售前支持与演示', NULL),

('BUSINESS_SUPPORT', '商务支持', 'BUSINESS', 'GLOBAL', 'DEPT', 3, 0, 'ACTIVE',
 '商务流程支持，合同管理，报价协助', NULL),

-- 客服角色 (Level 2-3)
('CUSTOMER_SERVICE_MGR', '客服经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '客服团队管理，服务质量监控，客户关系维护', NULL),

('CUSTOMER_SERVICE', '客服工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '客户沟通，问题处理，售后支持', NULL),

-- HR 角色 (Level 2-3)
('HR_MGR', 'HR经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '人力资源管理，招聘培训，绩效考核', NULL),

('HR', 'HR专员', 'BUSINESS', 'GLOBAL', 'ALL', 3, 0, 'ACTIVE',
 '人事执行，员工关系，考勤薪酬', NULL),

-- 仓储角色 (Level 2-3)
('WAREHOUSE_MGR', '仓储经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '仓储团队管理，库存控制，出入库审批', NULL),

('WAREHOUSE', '仓储管理员', 'BUSINESS', 'GLOBAL', 'DEPT', 3, 0, 'ACTIVE',
 '物料收发，库存盘点，库位管理', NULL),

-- 生产管理扩展 (Level 1-2)
('MANUFACTURING_DIR', '制造总监', 'SYSTEM', 'GLOBAL', 'DEPT', 1, 0, 'ACTIVE',
 '制造体系管理，生产效率，质量控制', NULL),

('PRODUCTION_MGR', '生产经理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '生产计划执行，团队调度，现场管理', NULL);

-- ============================================
-- 2. 汇报关系管理方式
-- ============================================
--
-- 汇报关系通过 users 表的 reporting_to 字段动态管理：
--
-- 示例：设置某人的直接上级
-- UPDATE users
-- SET reporting_to = (SELECT id FROM users WHERE username = '制造总监的username')
-- WHERE username = '仓储经理的username';
--
-- 可以随时更换上级，无需修改角色定义
-- ============================================

-- ============================================
-- 3. 部门管理方式
-- ============================================
--
-- 部门负责人通过 departments 表的 manager_id 动态管理：
--
-- 示例：设置仓储部负责人
-- UPDATE departments
-- SET manager_id = (SELECT id FROM users WHERE username = '新负责人的username')
-- WHERE dept_code = 'WAREHOUSE';
--
-- 可以随时更换部门负责人，无需修改角色定义
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
--     u.role_code,
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
