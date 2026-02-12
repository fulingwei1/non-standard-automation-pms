/**
 * 权限管理工具
 * 提供细粒度权限检查功能
 *
 * @deprecated 此模块使用 localStorage 直接读取权限，不推荐在新代码中使用
 * 推荐使用: import { usePermission, PermissionGuard, PERMISSIONS } from '../hooks/usePermission';
 *
 * 迁移指南:
 * - hasPermission(code) -> usePermission().hasPermission(code)
 * - hasAnyPermission(codes) -> usePermission().hasAnyPermission(codes)
 * - hasAllPermissions(codes) -> usePermission().hasAllPermissions(codes)
 * - PermissionGuard 组件 -> import { PermissionGuard } from '../hooks/usePermission'
 */

/**
 * 从localStorage获取用户权限列表
 * @returns {string[]} 权限编码数组
 */
export function getUserPermissions() {
  try {
    const userStr = localStorage.getItem("user");
    if (!userStr) {return [];}

    const user = JSON.parse(userStr);
    return user.permissions || [];
  } catch (e) {
    console.warn("Failed to parse user permissions:", e);
    return [];
  }
}

/**
 * 检查用户是否有指定权限
 * @param {string} permissionCode - 权限编码，如 'purchase:order:read'
 * @returns {boolean}
 */
export function hasPermission(permissionCode) {
  if (!permissionCode) {return false;}

  const userStr = localStorage.getItem("user");
  if (!userStr) {return false;}

  try {
    const user = JSON.parse(userStr);

    // 超级管理员拥有所有权限
    if (user.is_superuser === true || user.isSuperuser === true) {
      return true;
    }

    // 检查权限列表
    const permissions = user.permissions || [];
    return permissions.includes(permissionCode);
  } catch (e) {
    console.warn("Failed to check permission:", e);
    return false;
  }
}

/**
 * 检查用户是否有任意一个权限
 * @param {string[]} permissionCodes - 权限编码数组
 * @returns {boolean}
 */
export function hasAnyPermission(permissionCodes) {
  if (!Array.isArray(permissionCodes) || permissionCodes.length === 0) {
    return false;
  }

  return permissionCodes.some((code) => hasPermission(code));
}

/**
 * 检查用户是否有所有权限
 * @param {string[]} permissionCodes - 权限编码数组
 * @returns {boolean}
 */
export function hasAllPermissions(permissionCodes) {
  if (!Array.isArray(permissionCodes) || permissionCodes.length === 0) {
    return false;
  }

  return permissionCodes.every((code) => hasPermission(code));
}

/**
 * Purchase模块权限检查函数
 */

// 采购订单权限
export function hasPurchaseOrderRead() {
  return hasPermission("purchase:order:read");
}

export function hasPurchaseOrderCreate() {
  return hasPermission("purchase:order:create");
}

export function hasPurchaseOrderUpdate() {
  return hasPermission("purchase:order:update");
}

export function hasPurchaseOrderDelete() {
  return hasPermission("purchase:order:delete");
}

export function hasPurchaseOrderSubmit() {
  return hasPermission("purchase:order:submit");
}

export function hasPurchaseOrderApprove() {
  return hasPermission("purchase:order:approve");
}

export function hasPurchaseOrderReceive() {
  return hasPermission("purchase:order:receive");
}

// 收货单权限
export function hasPurchaseReceiptRead() {
  return hasPermission("purchase:receipt:read");
}

export function hasPurchaseReceiptCreate() {
  return hasPermission("purchase:receipt:create");
}

export function hasPurchaseReceiptUpdate() {
  return hasPermission("purchase:receipt:update");
}

export function hasPurchaseReceiptInspect() {
  return hasPermission("purchase:receipt:inspect");
}

// 采购申请权限
export function hasPurchaseRequestRead() {
  return hasPermission("purchase:request:read");
}

export function hasPurchaseRequestCreate() {
  return hasPermission("purchase:request:create");
}

export function hasPurchaseRequestUpdate() {
  return hasPermission("purchase:request:update");
}

export function hasPurchaseRequestDelete() {
  return hasPermission("purchase:request:delete");
}

export function hasPurchaseRequestSubmit() {
  return hasPermission("purchase:request:submit");
}

export function hasPurchaseRequestApprove() {
  return hasPermission("purchase:request:approve");
}

export function hasPurchaseRequestGenerate() {
  return hasPermission("purchase:request:generate");
}

// BOM相关权限
export function hasPurchaseBomGenerate() {
  return hasPermission("purchase:bom:generate");
}

/**
 * 检查是否有任何purchase模块权限（用于路由保护）
 * @returns {boolean}
 */
export function hasAnyPurchasePermission() {
  return hasAnyPermission([
    "purchase:order:read",
    "purchase:order:create",
    "purchase:receipt:read",
    "purchase:receipt:create",
    "purchase:request:read",
    "purchase:request:create",
    "purchase:bom:generate",
  ]);
}

/**
 * 权限检查Hook（用于React组件）
 * @param {string|string[]} permissionCodes - 权限编码或编码数组
 * @returns {boolean}
 */
export function usePermission(permissionCodes) {
  if (Array.isArray(permissionCodes)) {
    return hasAnyPermission(permissionCodes);
  }
  return hasPermission(permissionCodes);
}
