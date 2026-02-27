import { Navigate, useLocation } from "react-router-dom";
import { getWorkstationPath } from "../../config/roleDashboardMap";

/**
 * 角色未配置错误组件
 */
function RoleNotConfiguredError({ role }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-50">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">账号未配置工作台</h2>
          <p className="text-gray-600 mb-4">
            您的角色 <code className="bg-gray-100 px-2 py-1 rounded text-sm">{role}</code> 尚未配置对应的工作台页面。
          </p>
          <p className="text-sm text-gray-500">
            请联系系统管理员为您分配正确的角色权限。
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * 应用级别的受保护路由组件（带角色重定向）
 */
export function AppProtectedRoute({ children }) {
  const location = useLocation();

  // 检查用户是否应该被重定向到角色特定的工作台
  const userStr = localStorage.getItem("user");

  // 只在根路径时重定向
  if (location.pathname === "/" && userStr) {
    try {
      const user = JSON.parse(userStr);
      const role = user?.role;
    } catch (e) {
      // 忽略解析错误，但清除无效的用户数据
      console.warn("Invalid user data in localStorage:", e);
      localStorage.removeItem("user");
      return <Navigate to="/login" replace />;
    }

    if (role) {
      // 使用 getWorkstationPath 函数，它会自动处理大小写转换
      // 兼容前端旧格式（sales_director）和数据库新格式（SALES_DIR）
      const dashboardPath = getWorkstationPath(role);
      if (dashboardPath) {
        // 使用 replace 确保不会在历史记录中留下 '/' 路径
        return <Navigate to={dashboardPath} replace />;
      } else {
        // 角色未配置，显示错误页面
        return <RoleNotConfiguredError role={role} />;
      }
    } else {
      // 用户没有角色信息
      return <RoleNotConfiguredError role="(未设置)" />;
    }
  }

  return children;
}
