/**
 * 权限守卫组件
 *
 * 此文件为兼容层，重新导出 hooks/usePermission.js 中的实现
 * 推荐直接使用: import { PermissionGuard, useHasPermission } from '../../hooks/usePermission';
 */

// 从 usePermission 重新导出权限守卫组件
export { PermissionGuard } from "../../hooks/usePermission";

/**
 * 条件渲染Hook
 * @deprecated 推荐使用 import { usePermission } from '../../hooks/usePermission'
 * @param {string|string[]} permission - 权限编码或权限编码数组
 * @param {boolean} requireAll - 是否要求所有权限
 * @returns {boolean}
 */
export function useHasPermission(permission, requireAll = false) {
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { hasPermission, hasAnyPermission, hasAllPermissions } = require("../../hooks/usePermission").usePermission();

  if (!permission) {return true;}

  if (Array.isArray(permission)) {
    return requireAll
      ? hasAllPermissions(permission)
      : hasAnyPermission(permission);
  }

  return hasPermission(permission);
}
