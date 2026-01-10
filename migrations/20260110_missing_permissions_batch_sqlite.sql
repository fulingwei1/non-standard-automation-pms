-- 补充缺失的权限定义 (SQLite)
-- 日期: 2026-01-10
-- 说明: 为缺失权限的功能模块添加权限定义

BEGIN;

-- ============================================
-- 1. 系统管理模块权限（统一格式）
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('system:user:read', '用户查看', 'system', 'user', 'read'),
('system:user:create', '用户创建', 'system', 'user', 'create'),
('system:user:update', '用户更新', 'system', 'user', 'update'),
('system:user:delete', '用户删除', 'system', 'user', 'delete'),
('system:audit:read', '审计查看', 'system', 'audit', 'read');

-- ============================================
-- 2. 项目管理模块扩展权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('project:project:read', '项目查看', 'project', 'project', 'read'),
('project:project:create', '项目创建', 'project', 'project', 'create'),
('project:project:update', '项目更新', 'project', 'project', 'update'),
('project:project:delete', '项目删除', 'project', 'project', 'delete'),
('project:machine:read', '设备查看', 'project', 'machine', 'read'),
('project:machine:manage', '设备管理', 'project', 'machine', 'manage'),
('project:member:read', '成员查看', 'project', 'member', 'read'),
('project:member:manage', '成员管理', 'project', 'member', 'manage'),
('project:stage:read', '阶段查看', 'project', 'stage', 'read'),
('project:stage:manage', '阶段管理', 'project', 'stage', 'manage'),
('project:cost:read', '成本查看', 'project', 'cost', 'read'),
('project:cost:manage', '成本管理', 'project', 'cost', 'manage'),
('project:document:read', '文档查看', 'project', 'document', 'read'),
('project:document:manage', '文档管理', 'project', 'document', 'manage');

-- ============================================
-- 3. 客户管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('customer:customer:read', '客户查看', 'customer', 'customer', 'read'),
('customer:customer:create', '客户创建', 'customer', 'customer', 'create'),
('customer:customer:update', '客户更新', 'customer', 'customer', 'update'),
('customer:customer:delete', '客户删除', 'customer', 'customer', 'delete');

-- ============================================
-- 4. 供应商管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('supplier:supplier:read', '供应商查看', 'supplier', 'supplier', 'read'),
('supplier:supplier:create', '供应商创建', 'supplier', 'supplier', 'create'),
('supplier:supplier:update', '供应商更新', 'supplier', 'supplier', 'update'),
('supplier:supplier:delete', '供应商删除', 'supplier', 'supplier', 'delete');

-- ============================================
-- 5. 物料管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('material:material:read', '物料查看', 'material', 'material', 'read'),
('material:material:create', '物料创建', 'material', 'material', 'create'),
('material:material:update', '物料更新', 'material', 'material', 'update'),
('material:material:delete', '物料删除', 'material', 'material', 'delete'),
('material:shortage:read', '缺料查看', 'material', 'shortage', 'read'),
('material:shortage:manage', '缺料管理', 'material', 'shortage', 'manage');

-- ============================================
-- 6. 问题管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('issue:issue:read', '问题查看', 'issue', 'issue', 'read'),
('issue:issue:create', '问题创建', 'issue', 'issue', 'create'),
('issue:issue:update', '问题更新', 'issue', 'issue', 'update'),
('issue:issue:delete', '问题删除', 'issue', 'issue', 'delete'),
('issue:issue:resolve', '问题解决', 'issue', 'issue', 'resolve');

-- ============================================
-- 7. 财务管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('finance:budget:read', '预算查看', 'finance', 'budget', 'read'),
('finance:budget:create', '预算创建', 'finance', 'budget', 'create'),
('finance:budget:update', '预算更新', 'finance', 'budget', 'update'),
('finance:budget:approve', '预算审批', 'finance', 'budget', 'approve'),
('finance:cost:read', '成本查看', 'finance', 'cost', 'read'),
('finance:cost:manage', '成本管理', 'finance', 'cost', 'manage'),
('finance:bonus:read', '奖金查看', 'finance', 'bonus', 'read'),
('finance:bonus:manage', '奖金管理', 'finance', 'bonus', 'manage');

-- ============================================
-- 8. 服务管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('service:service:read', '服务查看', 'service', 'service', 'read'),
('service:service:create', '服务创建', 'service', 'service', 'create'),
('service:service:update', '服务更新', 'service', 'service', 'update'),
('service:ticket:read', '工单查看', 'service', 'ticket', 'read'),
('service:ticket:manage', '工单管理', 'service', 'ticket', 'manage');

-- ============================================
-- 9. 业务支持模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('business_support:order:read', '业务订单查看', 'business_support', 'order', 'read'),
('business_support:order:create', '业务订单创建', 'business_support', 'order', 'create'),
('business_support:order:update', '业务订单更新', 'business_support', 'order', 'update'),
('business_support:order:approve', '业务订单审批', 'business_support', 'order', 'approve');

-- ============================================
-- 10. 组织管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('organization:org:read', '组织查看', 'organization', 'org', 'read'),
('organization:org:manage', '组织管理', 'organization', 'org', 'manage'),
('organization:employee:read', '员工查看', 'organization', 'employee', 'read'),
('organization:employee:manage', '员工管理', 'organization', 'employee', 'manage');

-- ============================================
-- 11. 任务中心模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('task_center:task:read', '任务查看', 'task_center', 'task', 'read'),
('task_center:task:create', '任务创建', 'task_center', 'task', 'create'),
('task_center:task:update', '任务更新', 'task_center', 'task', 'update'),
('task_center:task:complete', '任务完成', 'task_center', 'task', 'complete');

-- ============================================
-- 12. 工时管理模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('timesheet:timesheet:read', '工时查看', 'timesheet', 'timesheet', 'read'),
('timesheet:timesheet:create', '工时创建', 'timesheet', 'timesheet', 'create'),
('timesheet:timesheet:update', '工时更新', 'timesheet', 'timesheet', 'update'),
('timesheet:timesheet:approve', '工时审批', 'timesheet', 'timesheet', 'approve');

-- ============================================
-- 13. 报表中心模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('report:report:read', '报表查看', 'report', 'report', 'read'),
('report:report:export', '报表导出', 'report', 'report', 'export'),
('report:report:manage', '报表管理', 'report', 'report', 'manage');

-- ============================================
-- 14. 其他模块权限
-- ============================================
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('notification:notification:read', '通知查看', 'notification', 'notification', 'read'),
('notification:notification:manage', '通知管理', 'notification', 'notification', 'manage'),
('document:document:read', '文档查看', 'document', 'document', 'read'),
('document:document:manage', '文档管理', 'document', 'document', 'manage'),
('technical_spec:spec:read', '技术规格查看', 'technical_spec', 'spec', 'read'),
('technical_spec:spec:manage', '技术规格管理', 'technical_spec', 'spec', 'manage'),
('engineer:engineer:read', '工程师查看', 'engineer', 'engineer', 'read'),
('engineer:engineer:manage', '工程师管理', 'engineer', 'engineer', 'manage'),
('qualification:qualification:read', '任职资格查看', 'qualification', 'qualification', 'read'),
('qualification:qualification:manage', '任职资格管理', 'qualification', 'qualification', 'manage'),
('assembly_kit:kit:read', '装配齐套查看', 'assembly_kit', 'kit', 'read'),
('assembly_kit:kit:manage', '装配齐套管理', 'assembly_kit', 'kit', 'manage'),
('staff_matching:matching:read', '人员匹配查看', 'staff_matching', 'matching', 'read'),
('staff_matching:matching:manage', '人员匹配管理', 'staff_matching', 'matching', 'manage'),
('project_evaluation:evaluation:read', '项目评价查看', 'project_evaluation', 'evaluation', 'read'),
('project_evaluation:evaluation:manage', '项目评价管理', 'project_evaluation', 'evaluation', 'manage'),
('installation_dispatch:dispatch:read', '安装派工查看', 'installation_dispatch', 'dispatch', 'read'),
('installation_dispatch:dispatch:manage', '安装派工管理', 'installation_dispatch', 'dispatch', 'manage'),
('scheduler:scheduler:read', '调度器查看', 'scheduler', 'scheduler', 'read'),
('scheduler:scheduler:manage', '调度器管理', 'scheduler', 'scheduler', 'manage'),
('hr_management:hr:read', 'HR管理查看', 'hr_management', 'hr', 'read'),
('hr_management:hr:manage', 'HR管理', 'hr_management', 'hr', 'manage'),
('presales_integration:presales:read', '售前集成查看', 'presales_integration', 'presales', 'read'),
('presales_integration:presales:manage', '售前集成管理', 'presales_integration', 'presales', 'manage'),
('advantage_products:product:read', '优势产品查看', 'advantage_products', 'product', 'read'),
('advantage_products:product:manage', '优势产品管理', 'advantage_products', 'product', 'manage');

COMMIT;
