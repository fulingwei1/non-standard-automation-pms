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
    if (isSuperuser) {return true;}

    // 检查权限列表
    if (!permissions || !Array.isArray(permissions)) {return false;}

    return permissions.includes(permissionCode);
  }, [permissions, isSuperuser]);

  /**
   * 检查是否有任一权限
   * @param {string[]} permissionCodes - 权限编码数组
   * @returns {boolean}
   */
  const hasAnyPermission = useCallback((permissionCodes) => {
    if (isSuperuser) {return true;}
    if (!permissions || !Array.isArray(permissions)) {return false;}
    if (!permissionCodes || !Array.isArray(permissionCodes)) {return false;}

    return permissionCodes.some(code => permissions.includes(code));
  }, [permissions, isSuperuser]);

  /**
   * 检查是否有所有权限
   * @param {string[]} permissionCodes - 权限编码数组
   * @returns {boolean}
   */
  const hasAllPermissions = useCallback((permissionCodes) => {
    if (isSuperuser) {return true;}
    if (!permissions || !Array.isArray(permissions)) {return false;}
    if (!permissionCodes || !Array.isArray(permissionCodes)) {return true;}

    return permissionCodes.every(code => permissions.includes(code));
  }, [permissions, isSuperuser]);

  /**
   * 检查是否可以访问指定菜单
   * @param {string} menuCode - 菜单编码
   * @returns {boolean}
   */
  const canAccessMenu = useCallback((menuCode) => {
    if (isSuperuser) {return true;}
    if (!menus || !Array.isArray(menus)) {return false;}

    // 递归检查菜单树
    const findMenu = (menuList, code) => {
      for (const menu of menuList) {
        if (menu.code === code) {return true;}
        if (menu.children && findMenu(menu.children, code)) {return true;}
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
    if (isSuperuser) {return 'ALL';}
    if (!dataScopes || typeof dataScopes !== 'object') {return null;}

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
    if (isSuperuser) {return true;}

    const scope = getDataScope(resourceType);
    if (!scope) {return false;}

    switch (scope) {
      case 'ALL':
        return true;

      case 'BUSINESS_UNIT':
      case 'DEPARTMENT':
      case 'TEAM':
        // 检查数据的组织单元是否在用户可访问范围内
        if (!data.org_unit_id && !data.department_id) {return true;}
        {
          const dataOrgId = data.org_unit_id || data.department_id;
          return userOrgUnitIds.includes(dataOrgId);
        }

      case 'PROJECT':
        // 检查是否参与该项目
        if (!data.project_id) {return true;}
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
    if (isSuperuser) {return menus || [];}
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
 * 权限编码常量
 *
 * 命名规范：
 * - 格式: module:resource:action 或 module:action
 * - 示例: project:project:read, budget:read, sales:lead:create
 * - 特殊: 部分历史端点使用大写格式 (USER_VIEW, ROLE_VIEW)
 *
 * 注意：这些常量必须与后端 api_permissions 表中的 perm_code 保持一致
 */
export const PERMISSIONS = {
  // 用户管理 (后端使用大写格式)
  USER: {
    VIEW: 'USER_VIEW',
    CREATE: 'USER_CREATE',
    UPDATE: 'USER_UPDATE',
    DELETE: 'USER_DELETE',
  },

  // 角色管理 (后端使用大写格式)
  ROLE: {
    VIEW: 'ROLE_VIEW',
    CREATE: 'ROLE_CREATE',
    UPDATE: 'ROLE_UPDATE',
    DELETE: 'ROLE_DELETE',
  },

  // 审计日志 (后端使用大写格式)
  AUDIT: {
    VIEW: 'AUDIT_VIEW',
  },

  // 项目管理
  PROJECT: {
    READ: 'project:project:read',
    CREATE: 'project:project:create',
    UPDATE: 'project:project:update',
    DELETE: 'project:project:delete',
    INITIATION_READ: 'project:initiation:read',
    CLOSE: 'project:close',
  },

  // 预算管理
  BUDGET: {
    READ: 'budget:read',
    CREATE: 'budget:create',
    APPROVE: 'budget:approve',
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
    TARGET_READ: 'sales:target:read',
    LEAD_READ: 'sales:lead:read',
    LEAD_CREATE: 'sales:lead:create',
    OPPORTUNITY_READ: 'sales:opportunity:read',
    OPPORTUNITY_CREATE: 'sales:opportunity:create',
    QUOTE_READ: 'sales:quote:read',
    QUOTE_CREATE: 'sales:quote:create',
    QUOTE_APPROVE: 'sales:quote:approve',
    CONTRACT_READ: 'sales:contract:read',
    CONTRACT_CREATE: 'sales:contract:create',
    FUNNEL_READ: 'sales:funnel:read',
    TEAM_READ: 'sales:team:read',
    BID_READ: 'sales:bid:read',
  },

  // 采购管理
  PURCHASE: {
    READ: 'purchase:read',
    CREATE: 'purchase:create',
    REQUEST_READ: 'purchase:request:read',
    RECEIPT_READ: 'purchase:receipt:read',
    ANALYSIS_READ: 'purchase:analysis:read',
  },

  // 供应商管理
  SUPPLIER: {
    READ: 'supplier:read',
    CREATE: 'supplier:create',
  },

  // 物料管理
  MATERIAL: {
    READ: 'material:read',
    CREATE: 'material:create',
    DEMAND_READ: 'material:demand:read',
    ANALYSIS_READ: 'material:analysis:read',
    REQUISITION_READ: 'material:requisition:read',
  },

  // BOM管理
  BOM: {
    READ: 'bom:read',
    CREATE: 'bom:create',
  },

  // 生产管理
  PRODUCTION: {
    BOARD_READ: 'production:board:read',
    PLAN_READ: 'production:plan:read',
    PLAN_CREATE: 'production:plan:create',
    EXCEPTION_READ: 'production:exception:read',
  },

  // 工单管理
  WORKORDER: {
    READ: 'workorder:read',
    CREATE: 'workorder:create',
  },

  // 派工管理
  DISPATCH: {
    READ: 'dispatch:read',
    CREATE: 'dispatch:create',
  },

  // ECN变更管理
  ECN: {
    READ: 'ecn:read',
    CREATE: 'ecn:create',
    TYPE_READ: 'ecn:type:read',
    STATISTICS_READ: 'ecn:statistics:read',
  },

  // 研发管理
  RD: {
    PROJECT_READ: 'rd:project:read',
    PROJECT_CREATE: 'rd:project:create',
    COST_READ: 'rd:cost:read',
  },

  // 财务管理
  FINANCE: {
    RECEIVABLE_READ: 'finance:receivable:read',
    INVOICE_READ: 'finance:invoice:read',
    INVOICE_CREATE: 'finance:invoice:create',
    REPORT_READ: 'finance:report:read',
  },

  // 付款管理
  PAYMENT: {
    APPROVE: 'payment:approve',
  },

  // 成本管理
  COST: {
    ACCOUNTING_READ: 'cost:accounting:read',
  },

  // 结算管理
  SETTLEMENT: {
    READ: 'settlement:read',
  },

  // 服务管理
  SERVICE: {
    TICKET_READ: 'service:ticket:read',
    ANALYTICS_READ: 'service:analytics:read',
  },

  // 验收管理
  ACCEPTANCE: {
    READ: 'acceptance:read',
    CREATE: 'acceptance:create',
  },

  // 安装调试
  INSTALLATION: {
    READ: 'installation:read',
    MANAGE: 'installation:manage',
    DISPATCH: 'installation:dispatch',
    ASSIGN: 'installation:assign',
  },

  // 绩效管理
  PERFORMANCE: {
    MANAGE: 'performance:manage',
    ENGINEER_READ: 'performance:engineer:read',
  },

  // 评价管理
  EVALUATION: {
    TASK_READ: 'evaluation:task:read',
    CONFIG_MANAGE: 'evaluation:config:manage',
  },

  // 资质管理
  QUALIFICATION: {
    READ: 'qualification:read',
  },

  // 员工管理
  STAFF: {
    TAG_MANAGE: 'staff:tag:manage',
    PROFILE_READ: 'staff:profile:read',
    NEED_READ: 'staff:need:read',
    MATCH_READ: 'staff:match:read',
  },

  // 预警管理
  ALERT: {
    READ: 'alert:read',
  },

  // 问题管理
  ISSUE: {
    READ: 'issue:read',
    CREATE: 'issue:create',
  },

  // 审批管理
  APPROVAL: {
    READ: 'approval:read',
  },

  // 知识库
  KNOWLEDGE: {
    READ: 'knowledge:read',
  },

  // 报表
  REPORT: {
    READ: 'report:read',
  },

  // 系统管理
  SYSTEM: {
    TEMPLATE_MANAGE: 'system:template:manage',
    USER_MANAGE: 'system:user:manage',
    ROLE_MANAGE: 'system:role:manage',
    PERMISSION_MANAGE: 'system:permission:manage',
    ORG_MANAGE: 'system:org:manage',
    POSITION_MANAGE: 'system:position:manage',
    SCHEDULER_READ: 'system:scheduler:read',
    AUDIT_READ: 'system:audit:read',
    DATA_MANAGE: 'system:data:manage',
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
