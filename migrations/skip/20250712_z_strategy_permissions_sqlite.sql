-- 战略管理和概览权限配置
-- 创建日期: 2025-01-22
-- 功能: 为所有角色添加概览权限，为总经理、副总经理、系统管理员添加战略管理权限

-- 1. 创建战略管理相关权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, action, resource, description, is_active, permission_type) VALUES
('executive:dashboard:read', '决策驾驶舱', 'executive', 'read', 'dashboard', '查看决策驾驶舱', 1, 'API'),
('strategy:dashboard:read', '战略分析', 'strategy', 'read', 'dashboard', '查看战略分析', 1, 'API'),
('executive:decision:read', '关键决策', 'executive', 'read', 'decision', '查看关键决策', 1, 'API'),
('pmo:rhythm:read', '管理节拍', 'pmo', 'read', 'rhythm', '查看管理节拍', 1, 'API');

-- 2. 创建概览相关权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, action, resource, description, is_active, permission_type) VALUES
('operation:dashboard:read', '运营大屏', 'operation', 'read', 'dashboard', '查看运营大屏', 1, 'API'),
('alert:read', '预警管理', 'alert', 'read', 'alert', '查看预警管理', 1, 'API'),
('approval:read', '审批中心', 'approval', 'read', 'approval', '查看审批中心', 1, 'API'),
('knowledge:read', '知识文档', 'knowledge', 'read', 'knowledge', '查看知识文档', 1, 'API');

-- 3. 为所有角色分配概览权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE p.perm_code IN ('operation:dashboard:read', 'alert:read', 'issue:read', 'approval:read', 'knowledge:read');

-- 4. 为总经理 (GM) 分配战略管理权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'GM'
AND p.perm_code IN ('executive:dashboard:read', 'strategy:dashboard:read', 'executive:decision:read', 'pmo:rhythm:read');

-- 5. 为副总经理 (VP) 分配战略管理权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'VP'
AND p.perm_code IN ('executive:dashboard:read', 'strategy:dashboard:read', 'executive:decision:read', 'pmo:rhythm:read');

-- 6. 为系统管理员 (ADMIN) 分配战略管理权限
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'ADMIN'
AND p.perm_code IN ('executive:dashboard:read', 'strategy:dashboard:read', 'executive:decision:read', 'pmo:rhythm:read');
