-- 修复通知权限问题
-- 1. 确保 notification:read 权限存在
-- 2. 将 notification:read 权限分配给所有角色

BEGIN;

-- 确保 notification:read 权限存在（如果不存在则创建）
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action, description) 
VALUES ('notification:read', '通知查看', 'notification', 'notification', 'read', '可以查看通知列表');

-- 将 notification:read 权限分配给所有角色
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r 
CROSS JOIN permissions p 
WHERE p.perm_code = 'notification:read'
AND NOT EXISTS (
    SELECT 1 FROM role_permissions rp 
    WHERE rp.role_id = r.id AND rp.permission_id = p.id
);

COMMIT;
