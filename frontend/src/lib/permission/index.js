/**
 * 统一权限适配层
 *
 * 新代码统一从此模块导入权限相关功能：
 *   import { useModuleAccess, ModuleProtectedRoute, MODULE_PERMISSIONS } from '../lib/permission';
 *
 * 旧代码迁移路径：
 *   - ProtectedRoute + hasProcurementAccess  →  ModuleProtectedRoute module="procurement"
 *   - permissionUtils.hasPermission           →  usePermission().hasPermission (hooks)
 *   - roleConfig/permissions                  →  useModuleAccess().hasModuleAccess
 */

export { useModuleAccess } from './useModuleAccess';
export { ModuleProtectedRoute } from './ModuleProtectedRoute';
export { MODULE_PERMISSIONS, MODULE_LABELS } from './constants';
