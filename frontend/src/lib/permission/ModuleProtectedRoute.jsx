/**
 * ModuleProtectedRoute
 *
 * 统一的模块级路由保护组件，替代 ProcurementProtectedRoute、
 * FinanceProtectedRoute 等分散的角色白名单路由守卫。
 *
 * 特性：
 * - 使用 PermissionContext（非 localStorage）
 * - fail-closed：权限加载中显示 loading，加载失败拒绝访问
 * - 支持模块级和权限码级检查
 *
 * 用法：
 *   <ModuleProtectedRoute module="procurement">
 *     <ProcurementPage />
 *   </ModuleProtectedRoute>
 *
 *   <ModuleProtectedRoute permission="purchase:order:read">
 *     <PurchaseOrderDetail />
 *   </ModuleProtectedRoute>
 */

import { motion } from 'framer-motion';
import { Button } from '../../components/ui/button';
import { useModuleAccess } from './useModuleAccess';
import { MODULE_LABELS } from './constants';

/**
 * 无权限占位组件
 */
function AccessDenied({ message }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center h-[60vh] text-center"
    >
      <div className="text-6xl mb-4">🔒</div>
      <h1 className="text-2xl font-semibold text-white mb-2">无权限访问</h1>
      <p className="text-slate-400 mb-4">{message}</p>
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

/**
 * 加载中占位组件
 */
function PermissionLoading() {
  return (
    <div className="flex items-center justify-center h-[60vh]">
      <div className="text-slate-400">权限验证中...</div>
    </div>
  );
}

/**
 * 模块级路由保护
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {string} [props.module] - 模块标识，如 'procurement'
 * @param {string} [props.permission] - 单个权限码，如 'purchase:order:read'
 * @param {string[]} [props.permissions] - 多个权限码（任一匹配即放行）
 * @param {string} [props.moduleName] - 自定义模块名称（用于提示文案）
 * @param {React.ReactNode} [props.fallback] - 自定义无权限组件
 */
export function ModuleProtectedRoute({
  children,
  module: moduleKey,
  permission,
  permissions: permissionList,
  moduleName,
  fallback,
}) {
  const { hasModuleAccess, checkPermission, isSuperuser, isLoading } = useModuleAccess();

  // 权限加载中 → 显示 loading（fail-closed）
  if (isLoading) {
    return <PermissionLoading />;
  }

  // 超级管理员直接放行
  if (isSuperuser) {
    return children;
  }

  // 检查权限
  let hasAccess = false;

  if (moduleKey) {
    hasAccess = hasModuleAccess(moduleKey);
  } else if (permission) {
    hasAccess = checkPermission(permission);
  } else if (permissionList && Array.isArray(permissionList)) {
    hasAccess = permissionList.some(code => checkPermission(code));
  } else {
    // 未指定任何权限要求 → fail-closed，拒绝访问
    console.warn('[ModuleProtectedRoute] 未指定 module 或 permission，拒绝访问');
    hasAccess = false;
  }

  if (!hasAccess) {
    if (fallback) return fallback;

    const label = moduleName
      || (moduleKey && MODULE_LABELS[moduleKey])
      || '此功能';

    return <AccessDenied message={`您没有权限访问${label}模块`} />;
  }

  return children;
}

export default ModuleProtectedRoute;
