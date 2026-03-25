/**
 * useModuleAccess Hook
 *
 * 统一的模块级权限检查，替代分散在各个 ProtectedRoute 中的角色白名单。
 * 采用 fail-closed 策略：权限未加载完成或检查失败时，默认拒绝访问。
 *
 * 用法：
 *   const { hasModuleAccess, isLoading } = useModuleAccess();
 *   if (hasModuleAccess('procurement')) { ... }
 *
 * 迁移：
 *   旧: hasProcurementAccess(role)         → 新: hasModuleAccess('procurement')
 *   旧: hasFinanceAccess(role)             → 新: hasModuleAccess('finance')
 *   旧: hasProductionAccess(role)          → 新: hasModuleAccess('production')
 *   旧: hasProjectReviewAccess(role, ...)  → 新: hasModuleAccess('project_review')
 *   旧: hasStrategyAccess(role, ...)       → 新: hasModuleAccess('strategy')
 */

import { useCallback } from 'react';
import { usePermission } from '../../hooks/usePermission';
import { MODULE_PERMISSIONS } from './constants';

/**
 * 模块级权限检查 Hook
 */
export function useModuleAccess() {
  const {
    hasPermission,
    hasAnyPermission,
    isSuperuser,
    isLoading,
    error,
    permissions,
  } = usePermission();

  /**
   * 检查是否有指定模块的访问权限
   * fail-closed: 权限未加载 → false, 无匹配权限 → false
   *
   * @param {string} moduleKey - 模块标识，如 'procurement', 'finance'
   * @returns {boolean}
   */
  const hasModuleAccess = useCallback((moduleKey) => {
    // 超级管理员始终放行
    if (isSuperuser) return true;

    // fail-closed: 权限未加载完成时拒绝
    if (isLoading) return false;

    const moduleCodes = MODULE_PERMISSIONS[moduleKey];
    if (!moduleCodes) {
      console.warn(`[useModuleAccess] 未知模块: ${moduleKey}`);
      return false;
    }

    return hasAnyPermission(moduleCodes);
  }, [isSuperuser, isLoading, hasAnyPermission]);

  /**
   * 检查是否有指定权限码（透传 usePermission）
   * @param {string} code
   * @returns {boolean}
   */
  const checkPermission = useCallback((code) => {
    if (isSuperuser) return true;
    if (isLoading) return false;
    return hasPermission(code);
  }, [isSuperuser, isLoading, hasPermission]);

  return {
    hasModuleAccess,
    checkPermission,
    isSuperuser,
    isLoading,
    error,
    permissions,
  };
}

export default useModuleAccess;
