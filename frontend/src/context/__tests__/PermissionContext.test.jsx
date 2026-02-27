/**
 * PermissionContext 测试
 * 测试权限上下文的核心功能
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { PermissionProvider, usePermissionContext, withPermission, PermissionLoading } from '../PermissionContext';
import { authApi } from '../../services/api';

// Mock authApi
vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: '/api' },
    },
  };
});

describe('PermissionContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('PermissionProvider', () => {
    it('应该正确渲染子组件', () => {
      localStorage.removeItem('token');
      render(
        <PermissionProvider>
          <div>Test Child</div>
        </PermissionProvider>
      );
      expect(screen.getByText('Test Child')).toBeInTheDocument();
    });

    it('未登录时应该跳过权限加载', async () => {
      localStorage.removeItem('token');

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(authApi.me).not.toHaveBeenCalled();
      expect(permData.permissions).toEqual([]);
      expect(permData.user).toBeNull();
    });

    it('已登录时应该加载权限数据', async () => {
      localStorage.setItem('token', 'valid-token');

      const mockUserData = {
        id: 1,
        username: 'test',
        is_superuser: false,
        permissions: ['project:view', 'project:edit'],
      };

      authApi.me.mockResolvedValue({ data: mockUserData });
      authApi.getPermissions.mockResolvedValue({
        data: {
          menus: [{ label: '项目管理', items: [] }],
          dataScopes: { project: 'own' },
        },
      });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(authApi.me).toHaveBeenCalled();
      expect(permData.permissions).toEqual(['project:view', 'project:edit']);
      expect(permData.user).toEqual(mockUserData);
      expect(permData.isSuperuser).toBe(false);
      expect(permData.menus).toEqual([{ label: '项目管理', items: [] }]);
      expect(permData.dataScopes).toEqual({ project: 'own' });
    });

    it('应该处理API错误（401未授权）', async () => {
      localStorage.setItem('token', 'invalid-token');
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'test' }));

      const error = new Error('Unauthorized');
      error.response = { status: 401 };
      authApi.me.mockRejectedValue(error);

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(permData.error).toBe('登录已过期，请重新登录');
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    it('应该处理服务器错误（500）并从localStorage恢复', async () => {
      const mockUser = {
        id: 1,
        username: 'test',
        is_superuser: false,
        permissions: ['project:view'],
      };

      localStorage.setItem('token', 'valid-token');
      localStorage.setItem('user', JSON.stringify(mockUser));

      const error = new Error('Server Error');
      error.response = { status: 500 };
      authApi.me.mockRejectedValue(error);

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(permData.error).toBe('服务器暂时不可用，使用缓存数据');
      expect(permData.user).toEqual(mockUser);
      expect(permData.permissions).toEqual(['project:view']);
    });

    it('应该处理超级管理员', async () => {
      localStorage.setItem('token', 'admin-token');

      const mockAdminData = {
        id: 1,
        username: 'admin',
        is_superuser: true,
        permissions: [],
      };

      authApi.me.mockResolvedValue({ data: mockAdminData });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(permData.isSuperuser).toBe(true);
    });

    it('应该处理isSuperuser的两种命名方式', async () => {
      localStorage.setItem('token', 'admin-token');

      const mockAdminData = {
        id: 1,
        username: 'admin',
        isSuperuser: true, // 使用驼峰命名
        permissions: [],
      };

      authApi.me.mockResolvedValue({ data: mockAdminData });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isSuperuser).toBe(true);
      });
    });

    it('应该处理getPermissions API不存在的情况', async () => {
      localStorage.setItem('token', 'valid-token');

      const mockUser = {
        id: 1,
        username: 'test',
        permissions: ['project:view'],
      };

      localStorage.setItem('user', JSON.stringify(mockUser));

      authApi.me.mockResolvedValue({ data: mockUser });
      authApi.getPermissions = undefined; // API不存在

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(permData.permissions).toEqual(['project:view']);
    });
  });

  describe('refreshPermissions 方法', () => {
    it('应该重新加载权限数据', async () => {
      localStorage.setItem('token', 'valid-token');

      const mockUserData = {
        id: 1,
        username: 'test',
        permissions: ['project:view'],
      };

      authApi.me.mockResolvedValue({ data: mockUserData });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(permData.permissions).toEqual(['project:view']);

      // 更新mock数据
      authApi.me.mockResolvedValue({
        data: {
          ...mockUserData,
          permissions: ['project:view', 'project:edit', 'project:delete'],
        },
      });

      // 刷新权限
      await act(async () => {
        await permData.refreshPermissions();
      });

      await waitFor(() => {
        expect(permData.permissions).toEqual(['project:view', 'project:edit', 'project:delete']);
      });
    });
  });

  describe('clearPermissions 方法', () => {
    it('应该清除所有权限数据', async () => {
      localStorage.setItem('token', 'valid-token');

      const mockUserData = {
        id: 1,
        username: 'test',
        permissions: ['project:view'],
      };

      authApi.me.mockResolvedValue({ data: mockUserData });
      authApi.getPermissions.mockResolvedValue({
        data: {
          menus: [{ label: '项目' }],
          dataScopes: { project: 'own' },
        },
      });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.permissions.length).toBeGreaterThan(0);
      });

      act(() => {
        permData.clearPermissions();
      });

      await waitFor(() => {
        expect(permData.permissions).toEqual([]);
        expect(permData.menus).toEqual([]);
        expect(permData.dataScopes).toEqual({});
        expect(permData.user).toBeNull();
        expect(permData.error).toBeNull();
      });
    });
  });

  describe('updatePermission 方法', () => {
    it('应该添加新权限', async () => {
      localStorage.setItem('token', 'valid-token');

      authApi.me.mockResolvedValue({
        data: { id: 1, username: 'test', permissions: ['project:view'] },
      });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.permissions).toEqual(['project:view']);
      });

      act(() => {
        permData.updatePermission('project:edit', true);
      });

      await waitFor(() => {
        expect(permData.permissions).toContain('project:edit');
      });
    });

    it('应该移除已有权限', async () => {
      localStorage.setItem('token', 'valid-token');

      authApi.me.mockResolvedValue({
        data: {
          id: 1,
          username: 'test',
          permissions: ['project:view', 'project:edit'],
        },
      });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.permissions).toContain('project:edit');
      });

      act(() => {
        permData.updatePermission('project:edit', false);
      });

      await waitFor(() => {
        expect(permData.permissions).not.toContain('project:edit');
        expect(permData.permissions).toContain('project:view');
      });
    });

    it('重复添加权限应该不影响列表', async () => {
      localStorage.setItem('token', 'valid-token');

      authApi.me.mockResolvedValue({
        data: { id: 1, username: 'test', permissions: ['project:view'] },
      });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.permissions).toEqual(['project:view']);
      });

      act(() => {
        permData.updatePermission('project:view', true);
      });

      // 权限列表不应该有重复
      expect(permData.permissions).toEqual(['project:view']);
    });
  });

  describe('storage 事件监听', () => {
    it('token变化时应该重新加载权限', async () => {
      localStorage.removeItem('token');

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.isLoading).toBe(false);
      });

      expect(authApi.me).not.toHaveBeenCalled();

      // 模拟登录（token变化）
      authApi.me.mockResolvedValue({
        data: { id: 1, username: 'test', permissions: ['project:view'] },
      });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      act(() => {
        localStorage.setItem('token', 'new-token');
        window.dispatchEvent(
          new StorageEvent('storage', {
            key: 'token',
            newValue: 'new-token',
            oldValue: null,
          })
        );
      });

      await waitFor(() => {
        expect(authApi.me).toHaveBeenCalled();
      });
    });

    it('token被清除时应该清空权限', async () => {
      localStorage.setItem('token', 'valid-token');

      authApi.me.mockResolvedValue({
        data: { id: 1, username: 'test', permissions: ['project:view'] },
      });
      authApi.getPermissions.mockResolvedValue({ data: {} });

      let permData;
      const TestComponent = () => {
        permData = usePermissionContext();
        return <div>Test</div>;
      };

      render(
        <PermissionProvider>
          <TestComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(permData.permissions.length).toBeGreaterThan(0);
      });

      // 模拟登出（token被清除）
      act(() => {
        localStorage.removeItem('token');
        window.dispatchEvent(
          new StorageEvent('storage', {
            key: 'token',
            newValue: null,
            oldValue: 'valid-token',
          })
        );
      });

      await waitFor(() => {
        expect(permData.permissions).toEqual([]);
      });
    });
  });

  describe('usePermissionContext Hook', () => {
    it('在Provider外部使用应该抛出错误', () => {
      const TestComponent = () => {
        usePermissionContext();
        return <div>Test</div>;
      };

      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('usePermissionContext 必须在 PermissionProvider 内部使用');

      consoleError.mockRestore();
    });
  });

  describe('withPermission HOC', () => {
    it('应该将权限数据注入到组件props', async () => {
      localStorage.removeItem('token');

      const TestComponent = ({ permission }) => {
        return (
          <div>
            <span data-testid="loading">{String(permission.isLoading)}</span>
            <span data-testid="perms">{permission.permissions.length}</span>
          </div>
        );
      };

      const WrappedComponent = withPermission(TestComponent);

      render(
        <PermissionProvider>
          <WrappedComponent />
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading')).toHaveTextContent('false');
        expect(screen.getByTestId('perms')).toHaveTextContent('0');
      });
    });
  });

  describe('PermissionLoading 组件', () => {
    it('加载中时应该显示fallback', async () => {
      localStorage.setItem('token', 'valid-token');

      // 让API调用挂起
      authApi.me.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 10000))
      );

      render(
        <PermissionProvider>
          <PermissionLoading fallback={<div>Loading...</div>}>
            <div>Content</div>
          </PermissionLoading>
        </PermissionProvider>
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      expect(screen.queryByText('Content')).not.toBeInTheDocument();
    });

    it('加载完成后应该显示children', async () => {
      localStorage.removeItem('token');

      render(
        <PermissionProvider>
          <PermissionLoading fallback={<div>Loading...</div>}>
            <div>Content</div>
          </PermissionLoading>
        </PermissionProvider>
      );

      await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
        expect(screen.getByText('Content')).toBeInTheDocument();
      });
    });

    it('未提供fallback时应该使用默认loading', async () => {
      localStorage.setItem('token', 'valid-token');

      authApi.me.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 10000))
      );

      render(
        <PermissionProvider>
          <PermissionLoading>
            <div>Content</div>
          </PermissionLoading>
        </PermissionProvider>
      );

      expect(screen.getByText('加载权限中...')).toBeInTheDocument();
    });
  });
});
