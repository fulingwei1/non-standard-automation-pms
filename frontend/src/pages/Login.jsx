import { useState } from 'react';
import { cn } from '../lib/utils';
import { authApi } from '../services/api';
import { diagnoseLogin } from '../utils/diagnose';
import { logger } from '../utils/logger';
import { resolveRoleCode } from '../utils/roleMapping';

const DEFAULT_BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || "8002";
const DEFAULT_BACKEND_TARGET =
  import.meta.env.VITE_BACKEND_URL || `127.0.0.1:${DEFAULT_BACKEND_PORT}`;


export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      // 纯真实 API 登录
      const response = await authApi.login(formData);

      // 处理响应数据（兼容直接返回 / 统一包装 { data: { access_token } }）
      const data = response.data?.data ?? response.data;
      const token =
        data?.access_token ??
        response.data?.access_token ??
        response.access_token;
      const refreshToken =
        data?.refresh_token ??
        response.data?.refresh_token ??
        response.refresh_token;

      if (!token) {
        const isStub = response.data?._stub ?? response.data?._message;
        logger.error("登录响应格式错误:", response);
        if (isStub) {
          throw new Error("登录接口返回了占位数据，请确认后端已启动且认证模块已加载，可尝试重启后端服务");
        }
        if (response.status === 404) {
          throw new Error("登录服务暂不可用(404)，请检查后端是否正常启动或重启后端服务");
        }
        throw new Error("服务器返回格式错误，请检查后端服务");
      }

      // 清理之前的用户信息
      localStorage.removeItem("user");

      // 保存 token
      localStorage.setItem("token", token);
      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      } else {
        localStorage.removeItem("refresh_token");
      }

      // 获取用户信息
      try {
        const userResponse = await authApi.me();
        const userData = userResponse.data;

        if (userData) {
          if (userData.permissions && Array.isArray(userData.permissions)) {
            logger.debug("[Login] 用户权限列表:", userData.permissions?.length, "个权限");
          } else {
            userData.permissions = [];
          }

          // 确定用户角色
          let userRole = "user";

          if (userData.roles && userData.roles?.length > 0) {
            userRole = resolveRoleCode(userData.roles[0]);
          } else if (userData.is_superuser) {
            userRole = "super_admin";
          } else {
            logger.warn("[Login] 用户没有分配角色:", userData.username);
            localStorage.removeItem("token");
            localStorage.removeItem("refresh_token");
            setError("您的账号尚未分配角色，请联系管理员进行角色配置");
            setLoading(false);
            return;
          }

          const frontendUser = {
            id: userData.id,
            username: userData.username,
            real_name: userData.real_name || userData.username,
            email: userData.email,
            phone: userData.phone,
            role: userRole,
            roles: userData.roles || [],
            permissions: userData.permissions || [],
            is_superuser: userData.is_superuser || false,
            department: userData.department_name || userData.department || null,
            avatar: userData.avatar || null,
          };

          localStorage.setItem("user", JSON.stringify(frontendUser));
          logger.debug("[Login] 登录成功:", frontendUser.username, "角色:", userRole);
        }
      } catch (userErr) {
        logger.error("获取用户信息失败:", userErr);
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");

        let userErrMessage = "获取用户信息失败，请重试";
        if (userErr.response?.status === 403) {
          userErrMessage = "系统错误：无法加载用户角色信息，请联系管理员检查账号配置";
        } else if (userErr.response?.status === 401) {
          userErrMessage = "登录凭证已过期，请重新登录";
        } else if (userErr.response?.status === 404) {
          userErrMessage = "用户账号不存在或已被删除，请联系管理员";
        } else if (!userErr.response) {
          userErrMessage = "网络连接失败，请检查网络后重试";
        }

        setError(userErrMessage);
        setLoading(false);
        return;
      }

      onLoginSuccess();
    } catch (err) {
      logger.error("登录错误:", err);

      let errorMessage = "登录失败，请检查用户名和密码";

      if (err.code === "ECONNABORTED" || err.message?.includes("timeout")) {
        errorMessage = "登录请求超时，请检查网络连接或稍后重试";
      } else if (err.response) {
        const detail = err.response.data?.detail;
        const status = err.response.status;
        const rawData = err.response.data;
        const contentType =
          err.response.headers?.["content-type"] ||
          err.response.headers?.["Content-Type"];

        if (
          status === 500 && (
            (typeof rawData === "string" && (rawData.includes("ECONNREFUSED") || rawData.includes("502"))) ||
            (contentType && !contentType.includes("application/json"))
          )
        ) {
          errorMessage = `后端服务不可达，请确认后端(${DEFAULT_BACKEND_TARGET})已启动`;
        } else if (status === 401 || status === 403) {
          errorMessage = typeof detail === "string"
            ? detail
            : "用户名或密码错误";
        } else if (status === 422) {
          errorMessage = "请输入正确格式的用户名和密码";
        } else if (status === 404) {
          errorMessage = "登录服务暂不可用，请检查后端服务是否正常运行";
        } else if (status >= 500) {
          errorMessage = `服务器错误(${status})，请联系管理员`;
        } else {
          errorMessage = typeof detail === "string" ? detail : `请求失败(${status})`;
        }
      } else if (!err.response && err.request) {
        errorMessage = `无法连接到服务器(${DEFAULT_BACKEND_TARGET})，请检查网络连接或后端服务是否启动`;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      <LoginBackground />

      <div className="flex w-full min-h-screen relative z-10">
        <FeatureShowcase />

        {/* Right - Form Section */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-white">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="w-full max-w-md"
          >
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">欢迎回来</h2>
              <p className="text-gray-500">登录您的账户以继续</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">用户名</label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                    <User className="h-5 w-5" />
                  </div>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="请输入用户名"
                    required
                    className={cn(
                      "w-full h-[52px] pl-12 pr-4 rounded-xl",
                      "bg-gray-50 border-2 border-transparent",
                      "text-gray-900 placeholder:text-gray-400",
                      "transition-all duration-200",
                      "hover:bg-gray-100",
                      "focus:bg-white focus:border-primary focus:outline-none",
                      "focus:ring-4 focus:ring-primary/10"
                    )}
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">密码</label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                    <Lock className="h-5 w-5" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                    required
                    className={cn(
                      "w-full h-[52px] pl-12 pr-12 rounded-xl",
                      "bg-gray-50 border-2 border-transparent",
                      "text-gray-900 placeholder:text-gray-400",
                      "transition-all duration-200",
                      "hover:bg-gray-100",
                      "focus:bg-white focus:border-primary focus:outline-none",
                      "focus:ring-4 focus:ring-primary/10"
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>

              {/* Options */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="sr-only"
                  />
                  <div className={cn(
                    "w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all",
                    rememberMe ? "bg-primary border-primary" : "border-gray-300"
                  )}>
                    {rememberMe && (
                      <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <span className="text-sm text-gray-600">记住登录状态</span>
                </label>
                <a href="#" className="text-sm font-medium text-primary hover:text-primary-dark underline">
                  忘记密码？
                </a>
              </div>

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-red-500 text-center space-y-2"
                >
                  <p>{error}</p>
                  <button
                    type="button"
                    onClick={() => {
                      diagnoseLogin();
                      alert("请查看浏览器控制台（F12）查看详细诊断信息");
                    }}
                    className="text-xs text-blue-500 hover:text-blue-700 underline"
                  >
                    点击运行诊断工具
                  </button>
                </motion.div>
              )}

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={loading}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "relative w-full h-[52px] rounded-xl",
                  "bg-gradient-to-r from-violet-600 to-indigo-600",
                  "text-white font-semibold",
                  "flex items-center justify-center gap-2",
                  "shadow-lg shadow-violet-500/30",
                  "hover:shadow-violet-500/50 hover:scale-[1.02]",
                  "active:scale-[0.98]",
                  "transition-all duration-200",
                  "disabled:opacity-70 disabled:cursor-not-allowed"
                )}
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  <>
                    <span>登录</span>
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </motion.button>
            </form>

            <QuickLoginGrid onSelect={(u, p) => { setUsername(u); setPassword(p); }} />

            <p className="mt-6 text-xs text-gray-400 text-center">
              &copy; 2026 项目进度管理系统 &middot; 安全登录
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
