import { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import ErrorBoundary from "./components/common/ErrorBoundary";
import { MainLayout } from "./components/layout/MainLayout";
import { AppRoutes } from "./routes/routeConfig";

// Pages
import Login from "./pages/Login";

// 登录页面包装组件，用于处理路由
function LoginRoute({ onLoginSuccess, isAuthenticated }) {
  const location = useLocation();

  // 如果已认证，重定向到根路径（会自动跳转到对应的dashboard）
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // 未认证时显示登录页面
  return <Login onLoginSuccess={onLoginSuccess} />;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem("token"),
  );

  // 监听 localStorage 中 token 的变化，同步认证状态
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("token");
      setIsAuthenticated(!!token);
    };

    // 初始检查
    checkAuth();

    // 监听 storage 事件（跨标签页同步）
    window.addEventListener("storage", checkAuth);

    // 定期检查（防止其他代码直接修改 localStorage）
    const interval = setInterval(checkAuth, 1000);

    return () => {
      window.removeEventListener("storage", checkAuth);
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    // 清理所有登录相关的数据
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setIsAuthenticated(false);
    // 跳转到登录页
    window.location.href = "/login";
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    // 登录成功后，跳转逻辑由 ProtectedRoute 处理
    // 不需要在这里手动跳转，避免页面重新加载导致的闪退
    // ProtectedRoute 会在根路径 '/' 时自动跳转到对应的 dashboard
  };

  // 始终使用 Router，这样 /login 路径才能正常工作
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          {/* 登录路由 */}
          <Route
            path="/login"
            element={
              <LoginRoute
                onLoginSuccess={handleLoginSuccess}
                isAuthenticated={isAuthenticated}
              />
            }
          />
          {/* 未认证时，所有其他路径都重定向到登录页 */}
          {!isAuthenticated ? (
            <Route path="*" element={<Navigate to="/login" replace />} />
          ) : (
            /* 已认证时，显示主应用 */
            <Route
              path="*"
              element={
                <MainLayout onLogout={handleLogout}>
                  <AppRoutes />
                </MainLayout>
              }
            />
          )}
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
