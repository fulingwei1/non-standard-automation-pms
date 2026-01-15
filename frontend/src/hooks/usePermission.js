/**
 * usePermission Hook
 *
 * 统一的前端权限检查 Hook，替代分散的硬编码角色检查
 *
 * 使用方式：
 * const { hasPermission, hasAnyPermission, hasAllPermissions, canAccessMenu } = usePermission();
 *
 * // 检查单个权限
 * if (hasPermission('project:create')) { ... }
 *
 * // 检查任一权限
 * if (hasAnyPermission(['project:read', 'project:create'])) { ... }
 *
 * // 检查所有权限
 * if (hasAllPermissions(['project:read', 'project:update'])) { ... }
 */

import { useCallback, useMemo } from 'react';
import { usePermissionContext } from '../context/PermissionContext';

/**
 * 权限检查 Hook
 */
export function usePermission() {
  const {
    permissions,
    menus,
    dataScopes,
    isSuperuser,
    isLoading,
    error
  } = usePermissionContext();

  /**
   * 检查是否有指定权限
   * @param {string} permissionCode - 权限编码，如 'project:create'
   * @returns {boolean}
   */
  const hasPermission = useCallback((permissionCode) => {
    // 超级管理员拥有所有权限
    if (isSuperuser) return true;

    // 检查权限列表
    if (!permissions || !Array.isArray(permissions)) return false;

    return permissions.includes(permissionCode);
  }, [permissions, isSuperuser]);

  /**
   * 检查是否有任一权限
   * @param {string[]} permissionCodes - 权限编码数组
   * @returns {boolean}
   */
  const hasAnyPermission = useCallback((permissionCodes) => {
    if (isSuperuser) return true;
    if (!permissions || !Array.isArray(permissions)) return false;
    if (!permissionCodes || !Array.isArray(permissionCodes)) return false;

    return permissionCodes.some(code => permissions.includes(code));
  }, [permissions, isSuperuser]);

  /**
   * 检查是否有所有权限
   * @param {string[]} permissionCodes - 权限编码数组
   * @returns {boolean}
   */
  const hasAllPermissions = useCallback((permissionCodes) => {
    if (isSuperuser) return true;
    if (!permissions || !Array.isArray(permissions)) return false;
    if (!permissionCodes || !Array.isArray(permissionCodes)) return true;

    return permissionCodes.every(code => permissions.includes(code));
  }, [permissions, isSuperuser]);

  /**
   * 检查是否可以访问指定菜单
   * @param {string} menuCode - 菜单编码
   * @returns {boolean}
   */
  const canAccessMenu = useCallback((menuCode) => {
    if (isSuperuser) return true;
    if (!menus || !Array.isArray(menus)) return false;

    // 递归检查菜单树
    const findMenu = (menuList, code) => {
      for (const menu of menuList) {
        if (menu.code === code) return true;
        if (menu.children && findMenu(menu.children, code)) return true;
      }
      return false;
    };

    return findMenu(menus, menuCode);
  }, [menus, isSuperuser]);

  /**
   * 获取指定资源的数据权限范围
   * @param {string} resourceType - 资源类型，如 'project', 'customer'
   * @returns {string|null} - 权限范围：ALL, BUSINESS_UNIT, DEPARTMENT, TEAM, PROJECT, OWN, null
   */
  const getDataScope = useCallback((resourceType) => {
    if (isSuperuser) return 'ALL';
    if (!dataScopes || typeof dataScopes !== 'object') return null;

    return dataScopes[resourceType] || null;
  }, [dataScopes, isSuperuser]);

  /**
   * 检查是否可以访问指定数据
   * @param {string} resourceType - 资源类型
   * @param {Object} data - 数据对象，需要包含 org_unit_id, created_by 等字段
   * @param {number} currentUserId - 当前用户ID
   * @param {number[]} userOrgUnitIds - 用户所属组织单元ID列表
   * @returns {boolean}
   */
  const canAccessData = useCallback((resourceType, data, currentUserId, userOrgUnitIds = []) => {
    if (isSuperuser) return true;

    const scope = getDataScope(resourceType);
    if (!scope) return false;

    switch (scope) {
      case 'ALL':
        return true;

      case 'BUSINESS_UNIT':
      case 'DEPARTMENT':
      case 'TEAM':
        // 检查数据的组织单元是否在用户可访问范围内
        if (!data.org_unit_id && !data.department_id) return true;
        const dataOrgId = data.org_unit_id || data.department_id;
        return userOrgUnitIds.includes(dataOrgId);

      case 'PROJECT':
        // 检查是否参与该项目
        if (!data.project_id) return true;
        // 这需要额外的项目成员信息，返回 null 表示需要服务端检查
        return null;

      case 'OWN':
        // 只能访问自己创建或负责的数据
        return data.created_by === currentUserId ||
               data.owner_id === currentUserId ||
               data.pm_id === currentUserId;

      default:
        return false;
    }
  }, [isSuperuser, getDataScope]);

  /**
   * 获取用户可见的菜单树
   */
  const visibleMenus = useMemo(() => {
    if (isSuperuser) return menus || [];
    return menus || [];
  }, [menus, isSuperuser]);

  return {
    // 权限检查方法
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    canAccessMenu,
    getDataScope,
    canAccessData,

    // 数据
    permissions,
    menus: visibleMenus,
    dataScopes,
    isSuperuser,

    // 状态
    isLoading,
    error,
  };
}

/**
 * 权限守卫组件
 * 用于条件渲染
 */
export function PermissionGuard({
  children,
  permission,
  permissions: permissionList,
  requireAll = false,
  fallback = null
}) {
  const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermission();

  const hasAccess = useMemo(() => {
    // 单个权限检查
    if (permission) {
      return hasPermission(permission);
    }

    // 多个权限检查
    if (permissionList && Array.isArray(permissionList)) {
      return requireAll
        ? hasAllPermissions(permissionList)
        : hasAnyPermission(permissionList);
    }

    return true;
  }, [permission, permissionList, requireAll, hasPermission, hasAnyPermission, hasAllPermissions]);

  if (!hasAccess) {
    return fallback;
  }

  return children;
}

/**
 * 常用权限编码常量
 * 统一管理，避免硬编码字符串
 */
export const PERMISSIONS = {
  // 项目管理
  PROJECT: {
    READ: 'project:read',
    CREATE: 'project:create',
    UPDATE: 'project:update',
    DELETE: 'project:delete',
  },

  // 客户管理
  CUSTOMER: {
    READ: 'customer:read',
    CREATE: 'customer:create',
    UPDATE: 'customer:update',
    DELETE: 'customer:delete',
  },

  // 销售管理
  SALES: {
    LEAD_READ: 'sales:lead:read',
    LEAD_CREATE: 'sales:lead:create',
    OPPORTUNITY_READ: 'sales:opportunity:read',
    OPPORTUNITY_CREATE: 'sales:opportunity:create',
    QUOTE_READ: 'sales:quote:read',
    QUOTE_CREATE: 'sales:quote:create',
    QUOTE_APPROVE: 'sales:quote:approve',
    CONTRACT_READ: 'sales:contract:read',
    CONTRACT_CREATE: 'sales:contract:create',
  },

  // 采购管理
  PROCUREMENT: {
    READ: 'procurement:read',
    ORDER_CREATE: 'purchase:order:create',
    ORDER_APPROVE: 'purchase:order:approve',
    SUPPLIER_READ: 'procurement:supplier:read',
    SUPPLIER_CREATE: 'procurement:supplier:create',
  },

  // 生产管理
  PRODUCTION: {
    READ: 'production:read',
    PLAN_CREATE: 'production:plan:create',
    WORKORDER_CREATE: 'production:workorder:create',
  },

  // 财务管理
  FINANCE: {
    READ: 'finance:read',
    INVOICE_CREATE: 'finance:invoice:create',
    PAYMENT_APPROVE: 'finance:payment:approve',
  },

  // 人力资源
  HR: {
    READ: 'hr:read',
    EMPLOYEE_CREATE: 'hr:employee:create',
    EMPLOYEE_UPDATE: 'hr:employee:update',
    SALARY_READ: 'hr:salary:read',
  },

  // 系统管理
  SYSTEM: {
    USER_READ: 'system:user:read',
    USER_CREATE: 'system:user:create',
    ROLE_READ: 'system:role:read',
    ROLE_CREATE: 'system:role:create',
    PERMISSION_READ: 'system:permission:read',
    ORG_READ: 'system:org:read',
    ORG_CREATE: 'system:org:create',
  },
};

/**
 * 数据权限范围常量
 */
export const DATA_SCOPES = {
  ALL: 'ALL',                      // 全部数据
  BUSINESS_UNIT: 'BUSINESS_UNIT',  // 本事业部数据
  DEPARTMENT: 'DEPARTMENT',        // 本部门数据
  TEAM: 'TEAM',                    // 本团队数据
  PROJECT: 'PROJECT',              // 参与项目数据
  OWN: 'OWN',                      // 仅个人数据
};

export default usePermission;
