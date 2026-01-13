-- ================================================
-- 进度预测和依赖检查功能权限配置 (SQLite版本)
-- 创建日期: 2026-01-12
-- 说明: 为进度预测和依赖检查功能添加权限控制
-- ================================================

-- 1. 添加进度预测访问权限
INSERT OR IGNORE INTO permissions (
  permission_code,
  permission_name,
  module,
  description,
  is_active,
  created_at,
  updated_at
) VALUES (
  'progress:forecast',
  '查看进度预测',
  '项目管理',
  '允许查看项目进度预测和执行自动处理操作',
  1,
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP
);

-- 2. 添加依赖检查访问权限
INSERT OR IGNORE INTO permissions (
  permission_code,
  permission_name,
  module,
  description,
  is_active,
  created_at,
  updated_at
) VALUES (
  'progress:dependency_check',
  '检查依赖关系',
  '项目管理',
  '允许检查项目依赖关系和执行自动修复操作',
  1,
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP
);

-- 3. 为所有项目管理相关人员分配这些权限
-- 允许的角色: admin, super_admin, chairman, gm, project_dept_manager, pmc, pm, 
--             tech_dev_manager, me_dept_manager, ee_dept_manager, te_dept_manager
INSERT OR IGNORE INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT 
  r.id, 
  p.id, 
  CURRENT_TIMESTAMP, 
  CURRENT_TIMESTAMP
FROM roles r
CROSS JOIN permissions p
WHERE p.permission_code IN ('progress:forecast', 'progress:dependency_check')
AND r.role_code IN (
  -- 管理层
  'admin',
  'super_admin',
  'chairman',
  'gm',
  
  -- 项目管理
  'project_dept_manager',
  'pmc',
  'pm',
  
  -- 技术开发部
  'tech_dev_manager',
  'me_dept_manager',
  'ee_dept_manager',
  'te_dept_manager'
);

-- 4. 验证权限配置结果
SELECT 
  '权限配置验证' as title,
  p.permission_code,
  p.permission_name,
  p.module,
  r.role_code,
  r.role_name
FROM permissions p
JOIN role_permissions rp ON p.id = rp.permission_id
JOIN roles r ON rp.role_id = r.id
WHERE p.permission_code IN ('progress:forecast', 'progress:dependency_check')
ORDER BY p.permission_code, r.role_name;

-- 5. 统计每个权限分配的角色数量
SELECT 
  '权限分配统计' as title,
  p.permission_code,
  p.permission_name,
  COUNT(rp.id) as role_count
FROM permissions p
LEFT JOIN role_permissions rp ON p.id = rp.permission_id
WHERE p.permission_code IN ('progress:forecast', 'progress:dependency_check')
GROUP BY p.permission_code, p.permission_name
ORDER BY p.permission_code;
