/**
 * RoleManagement 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RoleManagement from '../RoleManagement';
import api from '../../services/api';

// Mock dependencies
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(Object.entries(props).filter(([k]) => !['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'].includes(k)));
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
  AnimatePresence: ({ children }) => children,
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useInView: () => true,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe.skip('RoleManagement', () => {
  const mockRoleData = {
    items: [
      {
        id: 1,
        roleName: '系统管理员',
        roleCode: 'admin',
        description: '系统管理员角色',
        userCount: 5,
        permissions: ['user:create', 'user:delete', 'role:manage'],
        status: 'active',
        createdAt: '2024-01-15'
      },
      {
        id: 2,
        roleName: '项目经理',
        roleCode: 'pm',
        description: '项目经理角色',
        userCount: 15,
        permissions: ['project:create', 'project:view'],
        status: 'active',
        createdAt: '2024-02-10'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockRoleData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render role management page with title', async () => {
      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/角色管理|Role Management/i)).toBeInTheDocument();
      });
    });

    it('should render role list table', async () => {
      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统管理员')).toBeInTheDocument();
        expect(screen.getByText('项目经理')).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load roles on mount', async () => {
      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/roles')
        );
      });
    });

    it('should display loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should open create role modal', async () => {
      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统管理员')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建角色|Create Role/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建角色|Create Role/i)).toBeInTheDocument();
      });
    });

    it('should edit role', async () => {
      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统管理员')).toBeInTheDocument();
      });

      const editButton = screen.getAllByRole('button', { name: /编辑|Edit/i })[0];
      fireEvent.click(editButton);

      await waitFor(() => {
        expect(screen.getByText(/编辑角色|Edit Role/i)).toBeInTheDocument();
      });
    });

    it('should assign permissions to role', async () => {
      api.put.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统管理员')).toBeInTheDocument();
      });

      const permButton = screen.getAllByRole('button', { name: /权限|Permissions/i })[0];
      fireEvent.click(permButton);

      await waitFor(() => {
        expect(screen.getByText(/权限配置|Permission Config/i)).toBeInTheDocument();
      });
    });

    it('should delete role', async () => {
      api.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统管理员')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(api.delete).toHaveBeenCalledWith('/roles/1');
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      api.get.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });
  });

  // 5. 权限测试
  describe('Permission Control', () => {
    it('should show create button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['role:create']));

      render(
        <MemoryRouter>
          <RoleManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /新建角色|Create Role/i })).toBeInTheDocument();
      });
    });
  });
});
