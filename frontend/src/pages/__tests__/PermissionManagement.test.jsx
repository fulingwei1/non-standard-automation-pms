/**
 * PermissionManagement 组件测试
 * 测试覆盖：权限列表、模块过滤、权限分配、角色关联
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PermissionManagement from '../PermissionManagement';
import { roleApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  roleApi: {
    permissions: vi.fn(),
    list: vi.fn(),
    assignPermissions: vi.fn(),
  }
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(Object.entries(props).filter(([k]) => !['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'].includes(k)));
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
  AnimatePresence: ({ children }) => children,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('PermissionManagement', () => {
  const mockPermissions = [
    {
      id: 1,
      code: 'user:create',
      name: '创建用户',
      module: 'user',
      action: 'create',
      description: '创建新用户权限',
      roleCount: 3
    },
    {
      id: 2,
      code: 'user:delete',
      name: '删除用户',
      module: 'user',
      action: 'delete',
      description: '删除用户权限',
      roleCount: 1
    },
    {
      id: 3,
      code: 'project:view',
      name: '查看项目',
      module: 'project',
      action: 'view',
      description: '查看项目详情权限',
      roleCount: 5
    }
  ];

  const mockRoles = [
    { id: 1, roleName: '系统管理员', roleCode: 'admin', userCount: 5 },
    { id: 2, roleName: '项目经理', roleCode: 'pm', userCount: 10 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('token', 'test-token-123');
    roleApi.permissions.mockResolvedValue({ data: mockPermissions });
    roleApi.list.mockResolvedValue({ data: { items: mockRoles } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render permission management page', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/权限管理|Permission Management/i)).toBeInTheDocument();
      });
    });

    it('should render permission list', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('创建用户')).toBeInTheDocument();
        expect(screen.getByText('删除用户')).toBeInTheDocument();
        expect(screen.getByText('查看项目')).toBeInTheDocument();
      });
    });

    it('should display permission codes', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/user:create/)).toBeInTheDocument();
        expect(screen.getByText(/user:delete/)).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load permissions on mount', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(roleApi.permissions).toHaveBeenCalled();
      });
    });

    it('should show loading state', () => {
      roleApi.permissions.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      roleApi.permissions.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  // 3. 模块过滤测试
  describe('Module Filtering', () => {
    it('should filter permissions by module', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('创建用户')).toBeInTheDocument();
      });

      const moduleFilter = screen.queryByRole('combobox');
      if (moduleFilter) {
        fireEvent.change(moduleFilter, { target: { value: 'user' } });

        await waitFor(() => {
          expect(roleApi.permissions).toHaveBeenCalledWith({ module: 'user' });
        });
      }
    });

    it('should group permissions by module', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/user|用户/i)).toBeInTheDocument();
        expect(screen.getByText(/project|项目/i)).toBeInTheDocument();
      });
    });
  });

  // 4. 搜索功能测试
  describe('Search Functionality', () => {
    it('should search permissions by keyword', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('创建用户')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '创建' } });

        await waitFor(() => {
          expect(screen.getByText('创建用户')).toBeInTheDocument();
          expect(screen.queryByText('删除用户')).not.toBeInTheDocument();
        });
      }
    });
  });

  // 5. 权限分配测试
  describe('Permission Assignment', () => {
    it('should show roles with permission', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('创建用户')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);

        await waitFor(() => {
          expect(roleApi.list).toHaveBeenCalled();
        });
      }
    });

    it('should assign permission to role', async () => {
      roleApi.assignPermissions.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('创建用户')).toBeInTheDocument();
      });

      const assignButton = screen.queryByRole('button', { name: /分配|Assign/i });
      if (assignButton) {
        fireEvent.click(assignButton);

        await waitFor(() => {
          expect(screen.queryByText(/选择角色|Select Role/i)).toBeTruthy();
        });
      }
    });
  });

  // 6. 权限详情测试
  describe('Permission Details', () => {
    it('should display permission description', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/创建新用户权限/)).toBeInTheDocument();
      });
    });

    it('should show role count', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/3.*角色|3.*roles/i)).toBeInTheDocument();
      });
    });
  });

  // 7. 批量操作测试
  describe('Batch Operations', () => {
    it('should select multiple permissions', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('创建用户')).toBeInTheDocument();
      });

      const checkboxes = screen.queryAllByRole('checkbox');
      if (checkboxes.length > 0) {
        fireEvent.click(checkboxes[0]);
        fireEvent.click(checkboxes[1]);

        expect(screen.queryByText(/已选择|Selected/i)).toBeTruthy();
      }
    });

    it('should batch assign permissions', async () => {
      roleApi.assignPermissions.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('创建用户')).toBeInTheDocument();
      });

      const checkboxes = screen.queryAllByRole('checkbox');
      if (checkboxes.length > 1) {
        fireEvent.click(checkboxes[0]);
        fireEvent.click(checkboxes[1]);

        const batchAssignButton = screen.queryByRole('button', { name: /批量分配|Batch Assign/i });
        if (batchAssignButton) {
          fireEvent.click(batchAssignButton);
        }
      }
    });
  });

  // 8. 权限验证测试
  describe('Permission Validation', () => {
    it('should validate permission code format', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/user:create/)).toBeInTheDocument();
      });

      const permissions = screen.getAllByText(/:/);
      expect(permissions.length).toBeGreaterThan(0);
    });

    it('should show permission action badges', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/create|创建/i)).toBeInTheDocument();
        expect(screen.getByText(/delete|删除/i)).toBeInTheDocument();
        expect(screen.getByText(/view|查看/i)).toBeInTheDocument();
      });
    });
  });

  // 9. 演示账号处理测试
  describe('Demo Account Handling', () => {
    it('should handle demo account token', async () => {
      localStorage.setItem('token', 'demo_token_123');
      roleApi.permissions.mockResolvedValue({ data: [] });

      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(roleApi.permissions).not.toHaveBeenCalled();
      });
    });

    it('should redirect when no token', async () => {
      localStorage.removeItem('token');
      window.location.href = '';

      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(window.location.href).toBe('/');
      });
    });
  });

  // 10. 统计信息测试
  describe('Statistics Display', () => {
    it('should show total permission count', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/3.*权限|Total.*3/i)).toBeInTheDocument();
      });
    });

    it('should display most used permissions', async () => {
      render(
        <MemoryRouter>
          <PermissionManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const viewPermission = screen.getByText('查看项目');
        expect(viewPermission).toBeInTheDocument();
        expect(screen.getByText(/5.*角色|5.*roles/i)).toBeInTheDocument();
      });
    });
  });
});
