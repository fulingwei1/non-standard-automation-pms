/**
 * PermissionContext
 *
 * 权限上下文，管理用户的权限、菜单、数据权限等信息
 * 在应用启动时从后端获取权限数据，提供给整个应用使用
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../services/api';

// 创建上下文
const PermissionContext = createContext(null);

/**
 * 权限数据结构
 * @typedef {Object} PermissionData
 * @property {string[]} permissions - 权限编码列表
 * @property {Object[]} menus - 菜单树
 * @property {Object} dataScopes - 数据权限映射 { resourceType: scopeType }
 * @property {boolean} isSuperuser - 是否超级管理员
 * @property {Object} user - 用户信息
 */

/**
 * 权限 Provider 组件
 */
export function PermissionProvider({ children }) {
  // 权限数据状态
  const [permissions, setPermissions] = useState([]);
  const [menus, setMenus] = useState([]);
  const [dataScopes, setDataScopes] = useState({});
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [user, setUser] = useState(null);

  // 加载状态
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * 从后端加载权限数据
   */
  const loadPermissions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    // 检查是否有token
    const token = localStorage.getItem('token');
    if (!token) {
      console.log('[PermissionContext] 未找到token，跳过权限加载');
      setIsLoading(false);
      return;
    }

    try {
      // 获取当前用户信息和权限
      const response = await authApi.me();
      const userData = response.data;

      // 设置用户信息
      setUser(userData);
      setIsSuperuser(userData.is_superuser || userData.isSuperuser || false);

      // 设置权限列表
      setPermissions(userData.permissions || []);

      // 尝试获取完整的权限数据（包括菜单和数据权限）
      try {
        const permResponse = await authApi.getPermissions?.();
        if (permResponse?.data) {
          if (permResponse.data.menus) {
            setMenus(permResponse.data.menus);
          }
          if (permResponse.data.dataScopes) {
            setDataScopes(permResponse.data.dataScopes);
          }
        }
      } catch (_permError) {
        // 如果新的权��� API 不存在，使用旧的 nav_groups
        console.warn('新权限 API 不可用，使用兼容模式');
        // 从 localStorage 获取用户数据（兼容旧系统）
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          const parsedUser = JSON.parse(storedUser);
          // 使用旧的权限数据
          if (parsedUser.permissions) {
            setPermissions(parsedUser.permissions);
          }
        }
      }

    } catch (err) {
      console.error('加载权限数据失败:', err);

      // 检查是否是认证错误（401）
      if (err.response?.status === 401) {
        console.log('[PermissionContext] Token无效或已过期，清除本地数据');
        // Token无效，清除本地存储
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setError('登录已过期，请重新登录');
      } else if (err.response?.status === 500) {
        console.error('[PermissionContext] 服务器错误，尝试从本地恢复');
        setError('服务器暂时不可用，使用缓存数据');

        // 尝试从 localStorage 恢复
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          try {
            const parsedUser = JSON.parse(storedUser);
            setUser(parsedUser);
            setIsSuperuser(parsedUser.is_superuser || parsedUser.isSuperuser || false);
            setPermissions(parsedUser.permissions || []);
          } catch (parseError) {
            console.error('解析本地用户数据失败:', parseError);
          }
        }
      } else {
        setError(err.message || '加载权限数据失败');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 刷新权限数据
   */
  const refreshPermissions = useCallback(async () => {
    await loadPermissions();
  }, [loadPermissions]);

  /**
   * 清除权限数据（登出时调用）
   */
  const clearPermissions = useCallback(() => {
    setPermissions([]);
    setMenus([]);
    setDataScopes({});
    setIsSuperuser(false);
    setUser(null);
    setError(null);
  }, []);

  /**
   * 更新单个权限（用于实时权限变更）
   */
  const updatePermission = useCallback((permissionCode, hasPermission) => {
    setPermissions((prev) => {
      if (hasPermission && !prev.includes(permissionCode)) {
        return [...prev, permissionCode];
      }
      if (!hasPermission && prev.includes(permissionCode)) {
        return prev.filter((p) => p !== permissionCode);
      }
      return prev;
    });
  }, []);

  // 初始化时加载权限
  useEffect(() => {
    // 检查是否已登录
    const token = localStorage.getItem('token');
    if (token) {
      loadPermissions();
    } else {
      setIsLoading(false);
    }
    // 只在组件挂载时执行一次
     
  }, []);

  // 监听登录/登出事件
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'token') {
        if (e.newValue) {
          // 登录
          loadPermissions();
        } else {
          // 登出
          clearPermissions();
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
    // 依赖项可能导致无限循环，这里故意不包含loadPermissions和clearPermissions
     
  }, []);

  // 上下文值
  const contextValue = {
    // 权限数据
    permissions,
    menus,
    dataScopes,
    isSuperuser,
    user,

    // 状态
    isLoading,
    error,

    // 方法
    refreshPermissions,
    clearPermissions,
    updatePermission
  };

  return (
    <PermissionContext.Provider value={contextValue || "unknown"}>
      {children}
    </PermissionContext.Provider>);

}

/**
 * 使用权限上下文的 Hook
 */
export function usePermissionContext() {
  const context = useContext(PermissionContext);

  if (!context) {
    throw new Error('usePermissionContext 必须在 PermissionProvider 内部使用');
  }

  return context;
}

/**
 * 高阶组件：为组件注入权限数据
 */
export function withPermission(WrappedComponent) {
  return function WithPermissionComponent(props) {
    const permissionData = usePermissionContext();
    return <WrappedComponent {...props} permission={permissionData} />;
  };
}

/**
 * 权限加载中的占位组件
 */
export function PermissionLoading({ children, fallback = null }) {
  const { isLoading } = usePermissionContext();

  if (isLoading) {
    return fallback ||
    <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">加载权限中...</div>
    </div>;

  }

  return children;
}

export default PermissionContext;