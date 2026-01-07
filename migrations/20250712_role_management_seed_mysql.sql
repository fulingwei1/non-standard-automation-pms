-- ============================================
-- 角色管理模块 - MySQL 种子数据
-- 版本: 1.0
-- 日期: 2025-07-12
-- 说明: 预设角色、角色模板、互斥规则初始化
-- ============================================

SET NAMES utf8mb4;

-- ============================================
-- 1. 预设角色
-- ============================================

-- 插入预设角色（使用 INSERT ... ON DUPLICATE KEY UPDATE）
INSERT INTO roles (
    role_code, role_name, role_type, scope_type, data_scope,
    level, is_system, status, description
) VALUES
-- 系统角色（Level 0）
('ADMIN', '系统管理员', 'SYSTEM', 'GLOBAL', 'ALL', 0, 1, 'ACTIVE',
 '系统最高权限，可管理所有功能和数据'),

-- 管理层角色（Level 1）
('GM', '总经理', 'SYSTEM', 'GLOBAL', 'ALL', 1, 1, 'ACTIVE',
 '全局数据只读，关键审批权限'),

('CFO', '财务总监', 'BUSINESS', 'GLOBAL', 'ALL', 1, 0, 'ACTIVE',
 '财务相关全局权限，成本与回款管理'),

('CTO', '技术总监', 'BUSINESS', 'GLOBAL', 'ALL', 1, 0, 'ACTIVE',
 '技术相关全局权限，研发管理'),

('SALES_DIR', '销售总监', 'BUSINESS', 'GLOBAL', 'DEPT', 1, 0, 'ACTIVE',
 '销售部门全局权限，商机与合同管理'),

-- 主管级角色（Level 2）
('PM', '项目经理', 'BUSINESS', 'GLOBAL', 'PROJECT', 2, 0, 'ACTIVE',
 '项目全权管理，进度/变更/验收/成本'),

('PMC', '计划管理', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '生产计划、物料齐套、进度协调'),

('QA_MGR', '质量主管', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '质量管理、验收审批、问题闭环'),

('PU_MGR', '采购主管', 'BUSINESS', 'GLOBAL', 'DEPT', 2, 0, 'ACTIVE',
 '采购管理、供应商管理、成本控制'),

-- 专员级角色（Level 3）
('ME', '机械工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '机械设计任务执行、交付物提交'),

('EE', '电气工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '电气设计任务执行、交付物提交'),

('SW', '软件工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '软件开发任务执行、交付物提交'),

('QA', '质量工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '质量检验、验收执行、问题记录'),

('PU', '采购专员', 'BUSINESS', 'GLOBAL', 'DEPT', 3, 0, 'ACTIVE',
 '采购执行、到货跟踪、外协管理'),

('FI', '财务专员', 'BUSINESS', 'GLOBAL', 'ALL', 3, 0, 'ACTIVE',
 '开票、收款登记、成本核算'),

('SA', '销售专员', 'BUSINESS', 'GLOBAL', 'OWN', 3, 0, 'ACTIVE',
 '商机跟进、报价、合同、回款跟踪'),

('ASSEMBLER', '装配技师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '装配任务执行、工时记录'),

('DEBUG', '调试工程师', 'BUSINESS', 'GLOBAL', 'PROJECT', 3, 0, 'ACTIVE',
 '设备调试、问题记录、调试报告'),

-- 外部角色（Level 4）
('CUSTOMER', '客户', 'SYSTEM', 'GLOBAL', 'CUSTOMER', 4, 1, 'ACTIVE',
 '客户门户，仅查看自身项目进度与验收'),

('SUPPLIER', '供应商', 'SYSTEM', 'GLOBAL', 'OWN', 4, 1, 'ACTIVE',
 '供应商门户，查看订单与交货要求')

ON DUPLICATE KEY UPDATE
    role_name = VALUES(role_name),
    role_type = VALUES(role_type),
    scope_type = VALUES(scope_type),
    data_scope = VALUES(data_scope),
    level = VALUES(level),
    status = VALUES(status),
    description = VALUES(description),
    updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- 2. 设置角色层级关系
-- ============================================

-- PM 归属于 CTO
UPDATE roles r1
JOIN roles r2 ON r2.role_code = 'CTO'
SET r1.parent_role_id = r2.id
WHERE r1.role_code = 'PM';

-- 工程师归属于 PM
UPDATE roles r1
JOIN roles r2 ON r2.role_code = 'PM'
SET r1.parent_role_id = r2.id
WHERE r1.role_code IN ('ME', 'EE', 'SW', 'DEBUG');

-- 质量归属于 QA_MGR
UPDATE roles r1
JOIN roles r2 ON r2.role_code = 'QA_MGR'
SET r1.parent_role_id = r2.id
WHERE r1.role_code = 'QA';

-- 采购归属于 PU_MGR
UPDATE roles r1
JOIN roles r2 ON r2.role_code = 'PU_MGR'
SET r1.parent_role_id = r2.id
WHERE r1.role_code = 'PU';

-- 销售归属于 SALES_DIR
UPDATE roles r1
JOIN roles r2 ON r2.role_code = 'SALES_DIR'
SET r1.parent_role_id = r2.id
WHERE r1.role_code = 'SA';

-- 财务归属于 CFO
UPDATE roles r1
JOIN roles r2 ON r2.role_code = 'CFO'
SET r1.parent_role_id = r2.id
WHERE r1.role_code = 'FI';

-- ============================================
-- 3. 角色模板
-- ============================================

INSERT INTO role_templates (
    template_code, template_name, role_type, scope_type, data_scope,
    level, description, is_active
) VALUES
('TPL_PM', '项目经理模板', 'BUSINESS', 'GLOBAL', 'PROJECT', 2,
 '标准项目经理权限模板，包含项目管理全套权限', 1),

('TPL_ENGINEER', '工程师模板', 'BUSINESS', 'GLOBAL', 'PROJECT', 3,
 '标准工程师权限模板，包含任务执行与交付物权限', 1),

('TPL_PMC', 'PMC模板', 'BUSINESS', 'GLOBAL', 'DEPT', 2,
 '计划管理权限模板，包含计划与物料管理权限', 1),

('TPL_SALES', '销售模板', 'BUSINESS', 'GLOBAL', 'OWN', 3,
 '销售专员权限模板，包含商机与合同权限', 1),

('TPL_FINANCE', '财务模板', 'BUSINESS', 'GLOBAL', 'ALL', 3,
 '财务专员权限模板，包含开票与收款权限', 1),

('TPL_QA', '质量模板', 'BUSINESS', 'GLOBAL', 'PROJECT', 3,
 '质量工程师权限模板，包含验收与问题管理权限', 1),

('TPL_PURCHASE', '采购模板', 'BUSINESS', 'GLOBAL', 'DEPT', 3,
 '采购专员权限模板，包含采购与外协权限', 1),

('TPL_VIEWER', '只读模板', 'CUSTOM', 'GLOBAL', 'ALL', 4,
 '只读权限模板，仅包含查看权限', 1)

ON DUPLICATE KEY UPDATE
    template_name = VALUES(template_name),
    role_type = VALUES(role_type),
    scope_type = VALUES(scope_type),
    data_scope = VALUES(data_scope),
    level = VALUES(level),
    description = VALUES(description),
    updated_at = CURRENT_TIMESTAMP;

-- ============================================
-- 4. 角色互斥规则
-- ============================================

-- 采购专员与财务专员互斥
INSERT INTO role_exclusions (role_id_a, role_id_b, exclusion_type, reason, is_active)
SELECT a.id, b.id, 'MUTUAL', '职责分离：采购与财务不得兼任，防止舞弊风险', 1
FROM roles a, roles b
WHERE a.role_code = 'PU' AND b.role_code = 'FI'
ON DUPLICATE KEY UPDATE reason = VALUES(reason);

-- 采购主管与财务专员互斥
INSERT INTO role_exclusions (role_id_a, role_id_b, exclusion_type, reason, is_active)
SELECT a.id, b.id, 'MUTUAL', '职责分离：采购主管与财务专员不得兼任', 1
FROM roles a, roles b
WHERE a.role_code = 'PU_MGR' AND b.role_code = 'FI'
ON DUPLICATE KEY UPDATE reason = VALUES(reason);

-- 采购专员与财务总监互斥
INSERT INTO role_exclusions (role_id_a, role_id_b, exclusion_type, reason, is_active)
SELECT a.id, b.id, 'MUTUAL', '职责分离：采购专员与财务总监不得兼任', 1
FROM roles a, roles b
WHERE a.role_code = 'PU' AND b.role_code = 'CFO'
ON DUPLICATE KEY UPDATE reason = VALUES(reason);

-- 质量主管与项目经理互斥（同项目维度）
INSERT INTO role_exclusions (role_id_a, role_id_b, exclusion_type, reason, is_active)
SELECT a.id, b.id, 'MUTUAL', '验收独立性：同一项目内质量主管与项目经理不得兼任（项目维度）', 1
FROM roles a, roles b
WHERE a.role_code = 'QA_MGR' AND b.role_code = 'PM'
ON DUPLICATE KEY UPDATE reason = VALUES(reason);

-- ============================================
-- 5. 示例部门数据
-- ============================================

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active) VALUES
('ROOT', '公司', NULL, 0, 0, 1)
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

-- 一级部门
INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'TECH', '技术中心', id, 1, 1, 1 FROM departments WHERE dept_code = 'ROOT'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'SALES', '销售部', id, 1, 2, 1 FROM departments WHERE dept_code = 'ROOT'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'FINANCE', '财务部', id, 1, 3, 1 FROM departments WHERE dept_code = 'ROOT'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'PURCHASE', '采购部', id, 1, 4, 1 FROM departments WHERE dept_code = 'ROOT'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'QA', '质量部', id, 1, 5, 1 FROM departments WHERE dept_code = 'ROOT'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'PMC', '计划部', id, 1, 6, 1 FROM departments WHERE dept_code = 'ROOT'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

-- 技术中心下属部门
INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'MECH', '机械部', id, 2, 1, 1 FROM departments WHERE dept_code = 'TECH'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'ELEC', '电气部', id, 2, 2, 1 FROM departments WHERE dept_code = 'TECH'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'SOFT', '软件部', id, 2, 3, 1 FROM departments WHERE dept_code = 'TECH'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

INSERT INTO departments (dept_code, dept_name, parent_id, level, sort_order, is_active)
SELECT 'DEBUG', '调试部', id, 2, 4, 1 FROM departments WHERE dept_code = 'TECH'
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

-- ============================================
-- 6. 部门默认角色配置
-- ============================================

-- 机械部默认角色：机械工程师
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'MECH' AND r.role_code = 'ME'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 电气部默认角色：电气工程师
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'ELEC' AND r.role_code = 'EE'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 软件部默认角色：软件工程师
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'SOFT' AND r.role_code = 'SW'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 调试部默认角色：调试工程师
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'DEBUG' AND r.role_code = 'DEBUG'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 采购部默认角色：采购专员
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'PURCHASE' AND r.role_code = 'PU'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 财务部默认角色：财务专员
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'FINANCE' AND r.role_code = 'FI'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 销售部默认角色：销售专员
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'SALES' AND r.role_code = 'SA'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 质量部默认角色：质量工程师
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'QA' AND r.role_code = 'QA'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- 计划部默认角色：PMC
INSERT INTO department_default_roles (department_id, role_id, is_primary)
SELECT d.id, r.id, 1
FROM departments d, roles r
WHERE d.dept_code = 'PMC' AND r.role_code = 'PMC'
ON DUPLICATE KEY UPDATE is_primary = VALUES(is_primary);

-- ============================================
-- 完成
-- ============================================
