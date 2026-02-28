/**
 * AuthContext
 *
 * 认证上下文，管理用户的登录状态、用户信息等
 * 与 localStorage 同步，提供全局的认证状态访问
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';

// 创建上下文
const AuthContext = createContext(null);

/**
 * 认证数据结构
 * @typedef {Object} AuthData
 * @property {Object} user - 当前用户信息
 * @property {string} token - JWT 令牌
 * @property {boolean} isAuthenticated - 是否已登录
 * @property {boolean} isLoading - 加载状态
 */

/**
 * 认证 Provider 组件
 */
export function AuthProvider({ children }) {
  // 认证状态
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * 从 localStorage 加载用户数据
   */
  const loadAuthFromStorage = useCallback(() => {
    try {
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');

      if (storedToken && storedUser) {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } else {
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch (err) {
      console.error('加载认证信息失败:', err);
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 登录方法
   */
  const login = useCallback((userData, authToken) => {
    localStorage.setItem('token', authToken);
    localStorage.setItem('user', JSON.stringify(userData));
    setToken(authToken);
    setUser(userData);
    setIsAuthenticated(true);
  }, []);

  /**
   * 登出方法
   */
  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  /**
   * 更新用户信息
   */
  const updateUser = useCallback((userData) => {
    const updatedUser = { ...user, ...userData };
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setUser(updatedUser);
  }, [user]);

  /**
   * 刷新认证状态（从 localStorage 重新加载）
   */
  const refreshAuth = useCallback(() => {
    loadAuthFromStorage();
  }, [loadAuthFromStorage]);

  // 初始化时加载认证信息
  useEffect(() => {
    loadAuthFromStorage();
     
  }, []);

  // 监听 storage 变化（跨标签页同步）
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'token' || e.key === 'user') {
        loadAuthFromStorage();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
     
  }, []);

  // 上下文值
  const contextValue = {
    // 状态
    user,
    token,
    isAuthenticated,
    isLoading,

    // 方法
    login,
    logout,
    updateUser,
    refreshAuth
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * 使用认证上下文的 Hook
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth 必须在 AuthProvider 内部使用');
  }

  return context;
}

/**
 * 高阶组件：为组件注入认证数据
 */
export function withAuth(WrappedComponent) {
  return function WithAuthComponent(props) {
    const authData = useAuth();
    return <WrappedComponent {...props} auth={authData} />;
  };
}

export default AuthContext;
