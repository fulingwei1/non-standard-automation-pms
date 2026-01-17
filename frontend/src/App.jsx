import { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation } from
"react-router-dom";
import { ConfigProvider, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import ErrorBoundary from "./components/common/ErrorBoundary";
import { MainLayout } from "./components/layout/MainLayout";
import { AppRoutes } from "./routes/routeConfig";

// Pages
import Login from "./pages/Login";

// Ant Design 深色主题配置 - 匹配项目设计系统
const antdDarkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    // 主色调 - 紫色 (匹配 --color-primary: #8b5cf6)
    colorPrimary: "#8b5cf6",
    colorLink: "#8b5cf6",
    colorLinkHover: "#a78bfa",

    // 背景色 (匹配 --surface-* 变量)
    colorBgContainer: "#18181b", // surface-200
    colorBgElevated: "#27272a", // surface-300
    colorBgLayout: "#09090b", // surface-50
    colorBgSpotlight: "#3f3f46", // surface-400

    // 边框色 (匹配 --border-color)
    colorBorder: "rgba(255, 255, 255, 0.08)",
    colorBorderSecondary: "rgba(255, 255, 255, 0.05)",

    // 文字色 (匹配 --text-* 变量)
    colorText: "#f8fafc", // text-primary
    colorTextSecondary: "#94a3b8", // text-secondary
    colorTextTertiary: "#64748b", // text-tertiary
    colorTextQuaternary: "#475569", // text-muted

    // 圆角
    borderRadius: 8,
    borderRadiusLG: 12,
    borderRadiusSM: 6,

    // 字体
    fontFamily: "'Inter var', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
  },
  components: {
    Card: {
      colorBgContainer: "#18181b",
      colorBorderSecondary: "rgba(255, 255, 255, 0.08)"
    },
    Table: {
      colorBgContainer: "#18181b",
      headerBg: "#27272a",
      rowHoverBg: "#27272a",
      borderColor: "rgba(255, 255, 255, 0.08)"
    },
    Input: {
      colorBgContainer: "#27272a",
      colorBorder: "rgba(255, 255, 255, 0.08)"
    },
    Select: {
      colorBgContainer: "#27272a",
      colorBgElevated: "#27272a",
      optionSelectedBg: "#3f3f46"
    },
    Modal: {
      contentBg: "#18181b",
      headerBg: "#18181b"
    },
    Tabs: {
      colorBgContainer: "transparent",
      itemSelectedColor: "#8b5cf6",
      inkBarColor: "#8b5cf6"
    },
    Button: {
      colorBgContainer: "#27272a",
      defaultBorderColor: "rgba(255, 255, 255, 0.08)"
    },
    Tag: {
      colorBgContainer: "#27272a"
    },
    Statistic: {
      colorTextDescription: "#94a3b8"
    },
    Progress: {
      defaultColor: "#8b5cf6"
    }
  }
};

// 登录页面包装组件，用于处理路由
function LoginRoute({ onLoginSuccess, isAuthenticated }) {
  const _location = useLocation();

  // 如果已认证，重定向到根路径（会自动跳转到对应的dashboard）
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // 未认证时显示登录页面
  return <Login onLoginSuccess={onLoginSuccess} />;
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem("token")
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
      <ConfigProvider theme={antdDarkTheme} locale={zhCN}>
        <Router>
          <Routes>
            {/* 登录路由 */}
            <Route
              path="/login"
              element={
              <LoginRoute
                onLoginSuccess={handleLoginSuccess}
                isAuthenticated={isAuthenticated} />

              } />

            {/* 未认证时，所有其他路径都重定向到登录页 */}
            {!isAuthenticated ?
            <Route path="*" element={<Navigate to="/login" replace />} /> : (

            /* 已认证时，显示主应用 */
            <Route
              path="*"
              element={
              <MainLayout onLogout={handleLogout}>
                    <AppRoutes />
              </MainLayout>
              } />)

            }
          </Routes>
        </Router>
      </ConfigProvider>
    </ErrorBoundary>);

}

export default App;