/**
 * 登录逻辑 Hook
 * 处理表单状态、认证流程、用户信息获取
 */

import { useState } from 'react';
import { authApi } from '../../../services/api';
import { diagnoseLogin } from '../../../utils/diagnose';
import { logger } from '../../../utils/logger';
import { DEFAULT_BACKEND_TARGET, resolveRoleCode } from '../constants';

export function useLogin(onLoginSuccess) {
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
      const data = response.data?.data ?? response.data;
      const token = data?.access_token ?? response.data?.access_token ?? response.access_token;
      const refreshToken = data?.refresh_token ?? response.data?.refresh_token ?? response.refresh_token;

      if (!token) {
        const isStub = response.data?._stub ?? response.data?._message;
        logger.error("登录响应格式错误:", response);
        if (isStub) throw new Error("登录接口返回了占位数据，请确认后端已启动且认证模块已加载，可尝试重启后端服务");
        if (response.status === 404) throw new Error("登录服务暂不可用(404)，请检查后端是否正常启动或重启后端服务");
        throw new Error("服务器返回格式错误，请检查后端服务");
      }

      // 清理之前的用户信息并保存 token
      localStorage.removeItem("user");
      localStorage.setItem("token", token);
      if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
      else localStorage.removeItem("refresh_token");

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
            const firstRole = userData.roles[0];
            const roleName = typeof firstRole === "object" ? (firstRole.role_code || firstRole.role_name || firstRole) : firstRole;
            userRole = resolveRoleCode(roleName);
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
            department: userData.department,
            position: userData.position,
            is_superuser: userData.is_superuser || false,
            isSuperuser: userData.is_superuser || false,
            is_active: userData.is_active,
            roles: userData.roles || [],
            role: userRole,
            permissions: userData.permissions || []
          };

          localStorage.setItem("user", JSON.stringify(frontendUser));
          logger.debug("[Login] 用户权限已保存:", frontendUser.permissions?.length, "个权限");
          onLoginSuccess();
          return;
        }
      } catch (userErr) {
        logger.error("获取用户信息失败:", userErr);
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");

        let userErrMessage = "获取用户信息失败，请重新登录";
        if (userErr.response?.status === 500) userErrMessage = "系统错误：无法加载用户角色信息，请联系管理员检查账号配置";
        else if (userErr.response?.status === 401) userErrMessage = "登录凭证已过期，请重新登录";
        else if (userErr.response?.status === 404) userErrMessage = "用户账号不存在或已被删除，请联系管理员";
        else if (!userErr.response) userErrMessage = "网络连接失败，请检查网络后重试";

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
        const contentType = err.response.headers?.["content-type"] || err.response.headers?.["Content-Type"];

        if (status === 500 && (typeof rawData === "string" && (rawData.includes("ECONNREFUSED") || rawData.includes("proxy") || rawData.includes("connect") || rawData.includes(DEFAULT_BACKEND_TARGET)) || typeof contentType === "string" && (contentType.includes("text/html") || contentType.includes("text/plain")))) {
          errorMessage = `无法连接到后端服务（${DEFAULT_BACKEND_TARGET}），请确认后端已启动（运行 ./start.sh）`;
          setError(errorMessage);
          return;
        }

        if (detail && typeof detail === "object" && detail.error_code) {
          switch (detail.error_code) {
            case "USER_NOT_FOUND": errorMessage = "该员工尚未开通系统账号，请联系管理员"; break;
            case "USER_INACTIVE": errorMessage = "账号待激活，请联系管理员开通系统访问权限"; break;
            case "USER_DISABLED": errorMessage = "账号已被禁用，如有疑问请联系管理员"; break;
            case "WRONG_PASSWORD": errorMessage = "密码错误，忘记密码请联系管理员重置"; break;
            default: errorMessage = detail.message || errorMessage; break;
          }
        } else if (typeof detail === "string") {
          errorMessage = detail;
        } else if (err.response.data?.message) {
          errorMessage = err.response.data.message || errorMessage;
        } else if (status === 404) {
          errorMessage = "登录接口不可用(404)，请确认后端已启动且认证模块已加载，可尝试重启后端服务";
        } else if (status === 500) {
          errorMessage = "后端服务发生内部错误(500)。请查看后端日志 logs/backend.log 获取具体报错";
        }
      } else if (err.request) {
        errorMessage = "无法连接到服务器，请检查后端服务是否启动";
      } else {
        errorMessage = err.message || errorMessage;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    username, setUsername,
    password, setPassword,
    showPassword, setShowPassword,
    rememberMe, setRememberMe,
    error, loading,
    handleSubmit,
    diagnoseLogin,
  };
}
