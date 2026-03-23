/**
 * Generic Protected Route Component
 * Provides role-based access control for routes
 */

import {
  hasProcurementAccess,
  hasFinanceAccess,
  hasProductionAccess,
  hasProjectReviewAccess,
  hasStrategyAccess,
} from "../../lib/roleConfig";
import {
  hasPermission,
  hasAnyPurchasePermission,
} from "../../lib/permissionUtils";

/**
 * Permission check function type
 * @typedef {(role: string) => boolean} PermissionChecker
 */

/**
 * Generic route protection component
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components to render if authorized
 * @param {PermissionChecker} props.checkPermission - Function to check if user has permission
 * @param {string} props.permissionName - Name of the permission (for error message)
 * @param {string} props.redirectTo - Path to redirect if not authenticated (default: '/')
 */
export function ProtectedRoute({
  children,
  checkPermission,
  permissionName = "此功能",
  redirectTo = "/",
}) {
  const userStr = localStorage.getItem("user");

  if (!userStr) {
    console.warn(
      "ProtectedRoute: No user in localStorage, redirecting to",
      redirectTo,
    );
    return <Navigate to={redirectTo} replace />;
  }

  let user;
  let role;
  let isSuperuser;

  try {
    user = JSON.parse(userStr);
    role = user.role;
    isSuperuser = user.is_superuser === true || user.isSuperuser === true;
    console.log(
      "ProtectedRoute: User role =",
      role,
      ", isSuperuser =",
      isSuperuser,
      ", permissionName =",
      permissionName,
    );
  } catch (e) {
    console.warn("Invalid user data in localStorage:", e);
    localStorage.removeItem("user");
    return <Navigate to={redirectTo} replace />;
  }

  // 超级管理员绕过所有权限检查
  if (isSuperuser) {
    console.log("ProtectedRoute: Superuser bypass, rendering children");
    return children;
  }

  // 管理员角色也应该绕过权限检查
  if (
    role === "admin" ||
    role === "super_admin" ||
    role === "管理员" ||
    role === "系统管理员"
  ) {
    console.log("ProtectedRoute: Admin role bypass, rendering children");
    return children;
  }

  const hasPermission = checkPermission ? checkPermission(role) : true;
  console.log("ProtectedRoute: checkPermission result =", hasPermission);
  console.log("ProtectedRoute: role =", role, ", role type =", typeof role);
  console.log("ProtectedRoute: permissionName =", permissionName);

  if (!role || !hasPermission) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center justify-center h-[60vh] text-center"
      >
        <div className="text-6xl mb-4">🔒</div>
        <h1 className="text-2xl font-semibold text-white mb-2">无权限访问</h1>
        <p className="text-slate-400 mb-4">您没有权限访问{permissionName}</p>
        <Button
          onClick={() => window.history.back()}
          variant="default"
          className="mt-4"
        >
          返回上一页
        </Button>
      </motion.div>
    );
  }

  return children;
}

/**
 * Procurement-specific protected route
 * Wrapper for ProtectedRoute with procurement permission check
 *
 * 支持两种模式：
 * 1. 粗粒度检查（默认）：使用角色代码检查（向后兼容）
 * 2. 细粒度检查：使用权限编码检查（推荐）
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components
 * @param {string} props.requiredPermission - 细粒度权限编码（可选），如 'purchase:order:read'
 * @param {boolean} props.useFineGrained - 是否使用细粒度权限检查（默认：true，如果提供了requiredPermission）
 */
export function ProcurementProtectedRoute({
  children,
  requiredPermission = null,
  useFineGrained = null,
}) {
  const userStr = localStorage.getItem("user");
  let isSuperuser = false;

  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      isSuperuser = user.is_superuser === true || user.isSuperuser === true;
    } catch {
      // ignore
    }
  }

  // 决定使用哪种检查方式
  const shouldUseFineGrained =
    useFineGrained !== null ? useFineGrained : requiredPermission !== null;

  // 细粒度权限检查
  if (shouldUseFineGrained) {
    // 如果指定了具体权限，检查该权限；否则检查是否有任何purchase权限
    const hasAccess = requiredPermission
      ? hasPermission(requiredPermission)
      : hasAnyPurchasePermission();

    if (!hasAccess && !isSuperuser) {
      return (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center justify-center h-[60vh] text-center"
        >
          <div className="text-6xl mb-4">🔒</div>
          <h1 className="text-2xl font-semibold text-white mb-2">无权限访问</h1>
          <p className="text-slate-400 mb-4">
            您没有权限访问
            {requiredPermission
              ? `此功能（需要权限：${requiredPermission}）`
              : "采购和物料管理模块"}
          </p>
          <Button
            onClick={() => window.history.back()}
            variant="default"
            className="mt-4"
          >
            返回上一页
          </Button>
        </motion.div>
      );
    }

    return children;
  }

  // 粗粒度权限检查（向后兼容）
  return (
    <ProtectedRoute
      checkPermission={(role) => hasProcurementAccess(role, isSuperuser)}
      permissionName="采购和物料管理模块"
    >
      {children}
    </ProtectedRoute>
  );
}

/**
 * Finance-specific protected route
 * Wrapper for ProtectedRoute with finance permission check
 */
export function FinanceProtectedRoute({ children }) {
  const userStr = localStorage.getItem("user");
  let isSuperuser = false;
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      isSuperuser = user.is_superuser === true || user.isSuperuser === true;
    } catch {
      // ignore
    }
  }

  return (
    <ProtectedRoute
      checkPermission={(role) => hasFinanceAccess(role, isSuperuser)}
      permissionName="财务管理模块"
    >
      {children}
    </ProtectedRoute>
  );
}

/**
 * Production-specific protected route
 * Wrapper for ProtectedRoute with production permission check
 */
export function ProductionProtectedRoute({ children }) {
  const userStr = localStorage.getItem("user");
  let isSuperuser = false;
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      isSuperuser = user.is_superuser === true || user.isSuperuser === true;
    } catch {
      // ignore
    }
  }

  return (
    <ProtectedRoute
      checkPermission={(role) => hasProductionAccess(role, isSuperuser)}
      permissionName="生产管理模块"
    >
      {children}
    </ProtectedRoute>
  );
}

/**
 * Project Review-specific protected route
 * Wrapper for ProtectedRoute with project review permission check
 *
 * 使用动态权限检查：优先检查用户的 permissions 数组中是否包含项目复盘相关权限
 */
export function ProjectReviewProtectedRoute({ children }) {
  const userStr = localStorage.getItem("user");
  let isSuperuser = false;
  let permissions = [];

  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      isSuperuser = user.is_superuser === true || user.isSuperuser === true;
      permissions = user.permissions || [];
    } catch {
      // ignore
    }
  }

  // 使用权限代码检查（动态从数据库获取）
  const checkPermission = (userRole) => hasProjectReviewAccess(userRole, isSuperuser, permissions);

  return (
    <ProtectedRoute
      checkPermission={checkPermission}
      permissionName="项目复盘模块"
    >
      {children}
    </ProtectedRoute>
  );
}

/**
 * Strategy-specific protected route
 * Wrapper for ProtectedRoute with strategy module permission check
 *
 * 战略管理模块访问控制：
 * - 高管层：完整访问（战略全景、目标分解、执行追踪等）
 * - 部门经理：部门访问（查看部门目标和KPI）
 * - 普通员工：暂不开放（后续可开放个人KPI查看）
 */
export function StrategyProtectedRoute({ children }) {
  const userStr = localStorage.getItem("user");
  let isSuperuser = false;
  let permissions = [];

  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      isSuperuser = user.is_superuser === true || user.isSuperuser === true;
      permissions = user.permissions || [];
    } catch {
      // ignore
    }
  }

  // 使用权限代码检查（动态从数据库获取）
  const checkPermission = (userRole) => hasStrategyAccess(userRole, isSuperuser, permissions);

  return (
    <ProtectedRoute
      checkPermission={checkPermission}
      permissionName="战略管理模块"
    >
      {children}
    </ProtectedRoute>
  );
}

/**
 * Warehouse-specific protected route
 * Wrapper for ProtectedRoute with warehouse permission check
 *
 * 仓储模块访问控制：
 * - 仓储管理员/仓储经理：完整访问
 * - 超级管理员/系统管理员：完整访问
 */
export function WarehouseProtectedRoute({ children }) {
  const userStr = localStorage.getItem("user");
  let isSuperuser = false;

  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      isSuperuser = user.is_superuser === true || user.isSuperuser === true;
    } catch {
      // ignore
    }
  }

  // 仓储角色权限检查
  const warehouseRoles = ['WAREHOUSE', 'WAREHOUSE_MGR', 'WAREHOUSE', 'WAREHOUSE_MGR'];
  const hasWarehouseAccess = (userRole) => {
    const upperRole = userRole?.toUpperCase();
    return warehouseRoles.includes(upperRole) || isSuperuser;
  };

  return (
    <ProtectedRoute
      checkPermission={(userRole) => hasWarehouseAccess({ role: userRole })}
      permissionName="仓储管理模块"
    >
      {children}
    </ProtectedRoute>
  );
}

/**
 * Quality-specific protected route
 * Wrapper for ProtectedRoute with quality permission check
 *
 * 质量模块访问控制：
 * - 质量工程师/质量主管：完整访问
 * - 超级管理员/系统管理员：完整访问
 */
export function QualityProtectedRoute({ children }) {
  const userStr = localStorage.getItem("user");
  let isSuperuser = false;

  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      isSuperuser = user.is_superuser === true || user.isSuperuser === true;
    } catch {
      // ignore
    }
  }

  // 质量角色权限检查
  const qualityRoles = ['QA', 'QA_MGR'];
  const hasQualityAccess = (userRole) => {
    const upperRole = userRole?.toUpperCase();
    return qualityRoles.includes(upperRole) || isSuperuser;
  };

  return (
    <ProtectedRoute
      checkPermission={(userRole) => hasQualityAccess({ role: userRole })}
      permissionName="质量管理模块"
    >
      {children}
    </ProtectedRoute>
  );
}
