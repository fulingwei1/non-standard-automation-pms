/**
 * AuthContext 测试
 * 测试认证上下文的核心功能
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth, withAuth } from '../AuthContext';

describe('AuthContext', () => {
  beforeEach(() => {
    // 清除 localStorage
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('AuthProvider', () => {
    it('应该正确渲染子组件', () => {
      render(
        <AuthProvider>
          <div>Test Child</div>
        </AuthProvider>
      );
      expect(screen.getByText('Test Child')).toBeInTheDocument();
    });

    it('初始状态应该未登录', () => {
      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      expect(authData.isAuthenticated).toBe(false);
      expect(authData.user).toBeNull();
      expect(authData.token).toBeNull();
      expect(authData.isLoading).toBe(false);
    });

    it('应该从localStorage加载已存在的认证信息', async () => {
      const mockUser = { id: 1, username: 'test', real_name: '测试用户' };
      const mockToken = 'mock-token-123';
      
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', mockToken);

      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authData.isAuthenticated).toBe(true);
        expect(authData.user).toEqual(mockUser);
        expect(authData.token).toBe(mockToken);
      });
    });

    it('应该处理localStorage中的无效JSON', async () => {
      localStorage.setItem('user', 'invalid-json');
      localStorage.setItem('token', 'token-123');

      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authData.isAuthenticated).toBe(false);
        expect(authData.user).toBeNull();
      });
    });
  });

  describe('login 方法', () => {
    it('应该正确设置用户信息和token', async () => {
      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      const mockUser = { id: 1, username: 'test', real_name: '测试用户' };
      const mockToken = 'new-token-456';

      act(() => {
        authData.login(mockUser, mockToken);
      });

      await waitFor(() => {
        expect(authData.isAuthenticated).toBe(true);
        expect(authData.user).toEqual(mockUser);
        expect(authData.token).toBe(mockToken);
        expect(localStorage.getItem('token')).toBe(mockToken);
        expect(JSON.parse(localStorage.getItem('user'))).toEqual(mockUser);
      });
    });
  });

  describe('logout 方法', () => {
    it('应该清除认证信息', async () => {
      const mockUser = { id: 1, username: 'test' };
      const mockToken = 'token-123';
      
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', mockToken);

      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // 等待初始加载
      await waitFor(() => {
        expect(authData.isAuthenticated).toBe(true);
      });

      // 执行登出
      act(() => {
        authData.logout();
      });

      await waitFor(() => {
        expect(authData.isAuthenticated).toBe(false);
        expect(authData.user).toBeNull();
        expect(authData.token).toBeNull();
        expect(localStorage.getItem('token')).toBeNull();
        expect(localStorage.getItem('user')).toBeNull();
      });
    });
  });

  describe('updateUser 方法', () => {
    it('应该更新用户信息', async () => {
      const mockUser = { id: 1, username: 'test', real_name: '测试用户' };
      const mockToken = 'token-123';
      
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', mockToken);

      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(authData.user.real_name).toBe('测试用户');
      });

      act(() => {
        authData.updateUser({ real_name: '更新用户' });
      });

      await waitFor(() => {
        expect(authData.user.real_name).toBe('更新用户');
        expect(authData.user.username).toBe('test'); // 其他字段保持不变
        expect(JSON.parse(localStorage.getItem('user')).real_name).toBe('更新用户');
      });
    });
  });

  describe('refreshAuth 方法', () => {
    it('应该从localStorage重新加载认证信息', async () => {
      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // 初始未登录
      expect(authData.isAuthenticated).toBe(false);

      // 手动设置localStorage
      const mockUser = { id: 1, username: 'test' };
      const mockToken = 'token-123';
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', mockToken);

      // 刷新认证状态
      act(() => {
        authData.refreshAuth();
      });

      await waitFor(() => {
        expect(authData.isAuthenticated).toBe(true);
        expect(authData.user).toEqual(mockUser);
      });
    });
  });

  describe('storage 事件监听', () => {
    it('应该响应storage变化（跨标签页同步）', async () => {
      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      expect(authData.isAuthenticated).toBe(false);

      // 模拟其他标签页的storage变化
      const mockUser = { id: 1, username: 'test' };
      const mockToken = 'token-123';
      
      act(() => {
        localStorage.setItem('user', JSON.stringify(mockUser));
        localStorage.setItem('token', mockToken);
        
        // 触发storage事件
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'token',
          newValue: mockToken,
          oldValue: null,
        }));
      });

      await waitFor(() => {
        expect(authData.isAuthenticated).toBe(true);
      });
    });
  });

  describe('useAuth Hook', () => {
    it('在Provider外部使用应该抛出错误', () => {
      const TestComponent = () => {
        useAuth();
        return <div>Test</div>;
      };

      // 捕获console.error
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth 必须在 AuthProvider 内部使用');

      consoleError.mockRestore();
    });

    it('在Provider内部使用应该返回上下文值', () => {
      let authData;
      const TestComponent = () => {
        authData = useAuth();
        return <div>Test</div>;
      };

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      expect(authData).toBeDefined();
      expect(authData.login).toBeInstanceOf(Function);
      expect(authData.logout).toBeInstanceOf(Function);
      expect(authData.updateUser).toBeInstanceOf(Function);
      expect(authData.refreshAuth).toBeInstanceOf(Function);
    });
  });

  describe('withAuth HOC', () => {
    it('应该将认证数据注入到组件props', () => {
      const TestComponent = ({ auth }) => {
        return (
          <div>
            <span data-testid="authenticated">{String(auth.isAuthenticated)}</span>
            <span data-testid="username">{auth.user?.username || 'none'}</span>
          </div>
        );
      };

      const WrappedComponent = withAuth(TestComponent);

      render(
        <AuthProvider>
          <WrappedComponent />
        </AuthProvider>
      );

      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('username')).toHaveTextContent('none');
    });

    it('应该传递原有的props', () => {
      const TestComponent = ({ customProp }) => {
        return (
          <div>
            <span data-testid="custom">{customProp}</span>
          </div>
        );
      };

      const WrappedComponent = withAuth(TestComponent);

      render(
        <AuthProvider>
          <WrappedComponent customProp="test-value" />
        </AuthProvider>
      );

      expect(screen.getByTestId('custom')).toHaveTextContent('test-value');
    });
  });
});
