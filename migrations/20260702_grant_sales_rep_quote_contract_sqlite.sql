-- UX#2: 销售员菜单缺"报价/合同"入口——补授 sales_rep 报价/合同 读+建 权限(菜单权限驱动)
INSERT INTO role_api_permissions(role_id,permission_id)
 SELECT r.id,p.id FROM roles r,api_permissions p
 WHERE r.role_code='sales_rep'
 AND p.perm_code IN ('sales:quote:read','sales:quote:create','sales:contract:read','sales:contract:create')
 AND NOT EXISTS(SELECT 1 FROM role_api_permissions x WHERE x.role_id=r.id AND x.permission_id=p.id);
-- 修复根因：这些权限码 is_active=0 被权限引擎过滤，激活后授权才生效
UPDATE api_permissions SET is_active=1 WHERE perm_code IN ('sales:quote:read','sales:quote:create','sales:quote:approve','sales:contract:read','sales:contract:create') AND is_active=0;
