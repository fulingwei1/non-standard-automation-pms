import { Navigate, useLocation } from "react-router-dom";
import { roleDashboardMap } from "../../config/roleDashboardMap";

/**
 * 应用级别的受保护路由组件（带角色重定向）
 */
export function AppProtectedRoute({ children }) {
  const location = useLocation();

  // 检查用户是否应该被重定向到角色特定的仪表板
  const userStr = localStorage.getItem("user");

  // 只在根路径时重定向
  if (location.pathname === "/" && userStr) {
    let user = null;
    let role = null;

    try {
      user = JSON.parse(userStr);
      role = user.role;
    } catch (e) {
      // 忽略解析错误，但清除无效的用户数据
      console.warn("Invalid user data in localStorage:", e);
      localStorage.removeItem("user");
      return children;
    }

    if (role) {
      const dashboardPath = roleDashboardMap[role];
      if (dashboardPath) {
        // 使用 replace 确保不会在历史记录中留下 '/' 路径
        return <Navigate to={dashboardPath} replace />;
      }
    }
  }

  return children;
}
