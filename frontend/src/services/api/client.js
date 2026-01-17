import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 5000, // 5秒超时，更快响应
});

// 公开的 API 端点（不需要认证）
const PUBLIC_ENDPOINTS = [
  "/auth/login",
  "/auth/register",
  "/health",
  "/docs",
  "/openapi.json",
];

// 判断是否为公开 API
const isPublicEndpoint = (url) => {
  if (!url) return false;
  return PUBLIC_ENDPOINTS.some((endpoint) => url.includes(endpoint));
};

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    const url = config.url || "";
    const isPublic = isPublicEndpoint(url);

    // 调试日志（总是启用，帮助诊断问题）
    console.log(`[API请求] ${config.method?.toUpperCase()} ${url}`);
    
    // 如果是公开 API，不检查 token
    if (isPublic) {
      console.log("[API] ℹ️ 公开API，无需认证");
      return config;
    }

    console.log(
      `[API] Token状态:`,
      token
        ? token.startsWith("demo_token_")
          ? "演示账号token"
          : `真实token (${token.substring(0, 20)}...)`
        : "未找到token",
    );

    // 如果是演示账号的 token，不发送 Authorization header，避免后端返回 401
    if (token && !token.startsWith("demo_token_")) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`[API] ✅ 已添加Authorization头`);
    } else if (!token) {
      // 只在需要认证的 API 请求时显示警告
      console.warn(
        "[API] ⚠️ 未找到token，请求可能失败 (Not authenticated)",
        "\n提示：如果这是登录前的请求，请先完成登录"
      );
    } else {
      console.log("[API] ℹ️ 演示账号token，不发送Authorization头");
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    try {
      const method = error?.config?.method?.toUpperCase?.() || "?"
      const url = error?.config?.url || ""
      const status = error?.response?.status
      const contentType = error?.response?.headers?.["content-type"]
      const data = error?.response?.data

      if (status) {
        console.error(`[API错误] ${method} ${url} -> ${status}`, contentType || "")
        if (typeof data === "string" && data.trim()) {
          console.error("[API错误] 响应内容(截断):", data.slice(0, 400))
        } else if (data) {
          console.error("[API错误] 响应数据:", data)
        }
      }
    } catch {
      // best-effort logging; never block the original error
    }

    if (error.response && error.response.status === 401) {
      const token = localStorage.getItem("token");
      const requestUrl = error.config?.url || "";

      // 如果是演示账号的 token，不删除 token，也不重定向
      // 演示账号的 API 调用失败是预期的，因为后端不支持演示账号
      if (token && token.startsWith("demo_token_")) {
        // 对于演示账号，静默处理 401 错误，让页面组件使用 mock 数据
        console.log("演示账号 API 调用失败，将使用 mock 数据");
      } else {
        // 只有在认证相关的 API 返回 401 时才清除 token 并重定向
        // 其他 API 的 401 错误可能是权限问题，不应该导致登出
        const isAuthEndpoint = requestUrl.includes("/auth/");
        if (isAuthEndpoint) {
          console.log("认证 API 返回 401，清除 token");
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          // Redirect to login
          if (window.location.pathname !== "/") {
            window.location.href = "/";
          }
        } else {
          // 非认证 API 的 401 错误，只记录日志，不清除 token
          // 页面组件会使用 mock 数据或显示错误信息
          console.log("数据 API 返回 401，保持登录状态，使用 mock 数据");
        }
      }
    }
    return Promise.reject(error);
  },
);

export default api;
export { api };
