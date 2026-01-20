/**
 * 权限守卫组件
 * 用于在组件内部进行细粒度权限检查
 */

import { useMemo } from "react";
import {
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
} from "../../lib/permissionUtils";

/**
 * 权限守卫组件
 * @param {Object} props
 * @param {React.ReactNode} props.children - 有权限时显示的内容
 * @param {string|string[]} props.permission - 权限编码或权限编码数组
 * @param {boolean} props.requireAll - 如果permission是数组，是否要求所有权限（默认：false，任意一个即可）
 * @param {React.ReactNode} props.fallback - 无权限时显示的内容（可选）
 */
export function PermissionGuard({
  children,
  permission,
  requireAll = false,
  fallback = null,
}) {
  const hasAccess = useMemo(() => {
    if (!permission) {return true;}

    if (Array.isArray(permission)) {
      return requireAll
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }

    return hasPermission(permission);
  }, [permission, requireAll]);

  if (!hasAccess) {
    return fallback;
  }

  return children;
}

/**
 * 条件渲染Hook
 * @param {string|string[]} permission - 权限编码或权限编码数组
 * @param {boolean} requireAll - 是否要求所有权限
 * @returns {boolean}
 */
export function useHasPermission(permission, requireAll = false) {
  return useMemo(() => {
    if (!permission) {return true;}

    if (Array.isArray(permission)) {
      return requireAll
        ? hasAllPermissions(permission)
        : hasAnyPermission(permission);
    }

    return hasPermission(permission);
  }, [permission, requireAll]);
}
