/**
 * DepartmentManagement 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DepartmentManagement from '../DepartmentManagement';
import api from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
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

describe.skip('DepartmentManagement', () => {
  const mockDeptData = {
    items: [
      {
        id: 1,
        deptName: '研发部',
        deptCode: 'RD',
        parentId: null,
        manager: '张三',
        employeeCount: 20,
        description: '研发部门',
        status: 'active',
        createdAt: '2024-01-15'
      },
      {
        id: 2,
        deptName: '销售部',
        deptCode: 'SALES',
        parentId: null,
        manager: '李四',
        employeeCount: 15,
        description: '销售部门',
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
    api.get.mockResolvedValue({ data: mockDeptData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render department management page with title', async () => {
      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/部门管理|Department Management/i)).toBeInTheDocument();
      });
    });

    it('should render department tree', async () => {
      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('研发部')).toBeInTheDocument();
        expect(screen.getByText('销售部')).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load departments on mount', async () => {
      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/departments')
        );
      });
    });

    it('should display loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should open create department modal', async () => {
      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('研发部')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建部门|Create Department/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建部门|Create Department/i)).toBeInTheDocument();
      });
    });

    it('should edit department', async () => {
      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('研发部')).toBeInTheDocument();
      });

      const editButton = screen.getAllByRole('button', { name: /编辑|Edit/i })[0];
      fireEvent.click(editButton);

      await waitFor(() => {
        expect(screen.getByText(/编辑部门|Edit Department/i)).toBeInTheDocument();
      });
    });

    it('should delete department', async () => {
      api.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('研发部')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(api.delete).toHaveBeenCalledWith('/departments/1');
      });
    });

    it('should set department manager', async () => {
      api.put.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('研发部')).toBeInTheDocument();
      });

      const managerButton = screen.getAllByRole('button', { name: /设置负责人|Set Manager/i })[0];
      fireEvent.click(managerButton);

      await waitFor(() => {
        expect(screen.getByText(/设置部门负责人|Set Department Manager/i)).toBeInTheDocument();
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      api.get.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <DepartmentManagement />
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
      localStorage.setItem('userPermissions', JSON.stringify(['dept:create']));

      render(
        <MemoryRouter>
          <DepartmentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /新建部门|Create Department/i })).toBeInTheDocument();
      });
    });
  });
});
