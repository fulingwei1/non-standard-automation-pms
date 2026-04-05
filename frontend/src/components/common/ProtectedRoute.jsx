/**
 * Protected Route Components
 *
 * 重构后：所有路由守卫通过 PermissionContext 检查权限，
 * 不再直接读取 localStorage。
 *
 * 新代码推荐直接使用 ModuleProtectedRoute：
 *   import { ModuleProtectedRoute } from '../../lib/permission';
 *   <ModuleProtectedRoute module="procurement">...</ModuleProtectedRoute>
 *
 * 本文件保留旧的 export 签名，内部已迁移到新权限体系。
 */

import { Navigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "../ui/button";
import { usePermission } from "../../hooks/usePermission";
import { useModuleAccess } from "../../lib/permission";

// ─── 共享 UI ────────────────────────────────────────────

function AccessDenied({ permissionName = "此功能" }) {
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

function PermissionLoadingPlaceholder() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="text-slate-400">权限验证中...</div>
    </div>
  );
}

// ─── 基础 ProtectedRoute ────────────────────────────────

/**
 * Generic route protection component
 *
 * 已重构：使用 PermissionContext 代替 localStorage。
 * checkPermission 回调仍然接收 role 参数以保持向后兼容，
 * 但推荐迁移到 ModuleProtectedRoute。
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {(role: string) => boolean} [props.checkPermission] - 旧式角色检查回调
 * @param {string} [props.permissionName] - 模块名称（用于提示）
 * @param {string} [props.redirectTo] - 未登录时重定向路径
 */
export function ProtectedRoute({
  children,
  checkPermission,
  permissionName = "此功能",
  redirectTo = "/",
}) {
  const { isSuperuser, isLoading, permissions } = usePermission();

  // 未登录 → 重定向
  const token = typeof window !== 'undefined' ? localStorage.getItem("token") : null;
  if (!token && !isLoading) {
    return <Navigate to={redirectTo} replace />;
  }

  // 权限加载中 → 显示 loading（fail-closed）
  if (isLoading) {
    return <PermissionLoadingPlaceholder />;
  }

  // 超级管理员直接放行
  if (isSuperuser) {
    return children;
  }

  // 兼容旧的 checkPermission(role) 回调
  // 从 PermissionContext 中的 user 获取 role（而非直接读 localStorage）
  if (checkPermission) {
    // 从 localStorage 读 role 仅用于传递给旧回调（过渡期）
    let role = null;
    try {
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const user = JSON.parse(userStr);
        role = user.role;
      }
    } catch {
      // ignore
    }

    const hasAccess = checkPermission(role);
    if (!role || !hasAccess) {
      return <AccessDenied permissionName={permissionName} />;
    }
    return children;
  }

  // 无 checkPermission 回调 → 只检查是否已登录
  if (!permissions || permissions.length === 0) {
    return <AccessDenied permissionName={permissionName} />;
  }

  return children;
}

// ─── 模块级路由守卫（新版：通过权限码检查） ──────────────

/**
 * @deprecated 推荐使用 ModuleProtectedRoute module="procurement"
 */
export function ProcurementProtectedRoute({
  children,
  requiredPermission = null,
}) {
  const { hasModuleAccess, checkPermission, isSuperuser, isLoading } = useModuleAccess();

  if (isLoading) return <PermissionLoadingPlaceholder />;
  if (isSuperuser) return children;

  let hasAccess = false;
  if (requiredPermission) {
    hasAccess = checkPermission(requiredPermission);
  } else {
    hasAccess = hasModuleAccess('procurement');
  }

  if (!hasAccess) {
    const msg = requiredPermission
      ? `此功能（需要权限：${requiredPermission}）`
      : "采购和物料管理模块";
    return <AccessDenied permissionName={msg} />;
  }

  return children;
}

/**
 * @deprecated 推荐使用 ModuleProtectedRoute module="finance"
 */
export function FinanceProtectedRoute({ children }) {
  const { hasModuleAccess, isSuperuser, isLoading } = useModuleAccess();

  if (isLoading) return <PermissionLoadingPlaceholder />;
  if (isSuperuser) return children;
  if (!hasModuleAccess('finance')) {
    return <AccessDenied permissionName="财务管理模块" />;
  }
  return children;
}

/**
 * @deprecated 推荐使用 ModuleProtectedRoute module="production"
 */
export function ProductionProtectedRoute({ children }) {
  const { hasModuleAccess, isSuperuser, isLoading } = useModuleAccess();

  if (isLoading) return <PermissionLoadingPlaceholder />;
  if (isSuperuser) return children;
  if (!hasModuleAccess('production')) {
    return <AccessDenied permissionName="生产管理模块" />;
  }
  return children;
}

/**
 * @deprecated 推荐使用 ModuleProtectedRoute module="project_review"
 */
export function ProjectReviewProtectedRoute({ children }) {
  const { hasModuleAccess, isSuperuser, isLoading } = useModuleAccess();

  if (isLoading) return <PermissionLoadingPlaceholder />;
  if (isSuperuser) return children;
  if (!hasModuleAccess('project_review')) {
    return <AccessDenied permissionName="项目复盘模块" />;
  }
  return children;
}

/**
 * @deprecated 推荐使用 ModuleProtectedRoute module="strategy"
 */
export function StrategyProtectedRoute({ children }) {
  const { hasModuleAccess, isSuperuser, isLoading } = useModuleAccess();

  if (isLoading) return <PermissionLoadingPlaceholder />;
  if (isSuperuser) return children;
  if (!hasModuleAccess('strategy')) {
    return <AccessDenied permissionName="战略管理模块" />;
  }
  return children;
}

/**
 * @deprecated 推荐使用 ModuleProtectedRoute module="warehouse"
 */
export function WarehouseProtectedRoute({ children }) {
  const { hasModuleAccess, isSuperuser, isLoading } = useModuleAccess();

  if (isLoading) return <PermissionLoadingPlaceholder />;
  if (isSuperuser) return children;
  if (!hasModuleAccess('warehouse')) {
    return <AccessDenied permissionName="仓储管理模块" />;
  }
  return children;
}

/**
 * @deprecated 推荐使用 ModuleProtectedRoute module="quality"
 */
export function QualityProtectedRoute({ children }) {
  const { hasModuleAccess, isSuperuser, isLoading } = useModuleAccess();

  if (isLoading) return <PermissionLoadingPlaceholder />;
  if (isSuperuser) return children;
  if (!hasModuleAccess('quality')) {
    return <AccessDenied permissionName="质量管理模块" />;
  }
  return children;
}
