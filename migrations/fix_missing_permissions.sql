-- 添加缺失的API权限（实际代码中使用的权限码）

-- 用户管理权限（代码中使用的是 user:read，不是 user:view）
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'user:read', '查看用户', 'USER', 'VIEW', 'API', 1, 1);

-- 角色管理权限（代码中也可能使用 role:read）
INSERT OR IGNORE INTO api_permissions (tenant_id, perm_code, perm_name, module, action, permission_type, is_active, is_system) VALUES
(NULL, 'role:read', '查看角色', 'ROLE', 'VIEW', 'API', 1, 1);

-- 为ADMIN角色分配这些新权限
INSERT OR IGNORE INTO role_api_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN api_permissions p
WHERE r.role_code = 'ADMIN'
AND p.perm_code IN ('user:read', 'role:read');

-- 验证
SELECT 'User Read Permission:' as info, COUNT(*) as count FROM api_permissions WHERE perm_code = 'user:read';
SELECT 'Role Read Permission:' as info, COUNT(*) as count FROM api_permissions WHERE perm_code = 'role:read';
SELECT 'ADMIN has user:read:' as info, COUNT(*) as count 
FROM role_api_permissions rap
JOIN roles r ON rap.role_id = r.id
JOIN api_permissions p ON rap.permission_id = p.id
WHERE r.role_code = 'ADMIN' AND p.perm_code = 'user:read';
