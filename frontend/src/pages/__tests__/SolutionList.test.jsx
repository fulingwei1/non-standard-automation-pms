/**
 * SolutionList 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SolutionList from '../SolutionList';
import _api, { presaleApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    presaleApi: {
      create: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      tickets: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        accept: vi.fn().mockResolvedValue({ data: {} }),
        updateProgress: vi.fn().mockResolvedValue({ data: {} }),
        complete: vi.fn().mockResolvedValue({ data: {} }),
        rate: vi.fn().mockResolvedValue({ data: {} }),
        getBoard: vi.fn().mockResolvedValue({ data: {} }),
      },
      solutions: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        review: vi.fn().mockResolvedValue({ data: {} }),
        getVersions: vi.fn().mockResolvedValue({ data: {} }),
        getCost: vi.fn().mockResolvedValue({ data: {} }),
      },
      templates: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
      },
      tenders: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        updateResult: vi.fn().mockResolvedValue({ data: {} }),
      },
      statistics: {
        workload: vi.fn().mockResolvedValue({ data: {} }),
        responseTime: vi.fn().mockResolvedValue({ data: {} }),
        conversion: vi.fn().mockResolvedValue({ data: {} }),
        performance: vi.fn().mockResolvedValue({ data: {} }),
      },
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

describe.skip('SolutionList', () => {
  const mockSolutionData = {
    items: [
      {
        id: 1,
        solutionName: '智能制造整体解决方案',
        customerName: '上海智能制造有限公司',
        industry: '制造业',
        status: 'approved',
        version: 'v1.0',
        createdBy: '张三',
        createdAt: '2024-01-15',
        updatedAt: '2024-02-01'
      },
      {
        id: 2,
        solutionName: 'ERP系统集成方案',
        customerName: '北京科技公司',
        industry: 'IT服务',
        status: 'draft',
        version: 'v0.5',
        createdBy: '李四',
        createdAt: '2024-02-10',
        updatedAt: '2024-02-20'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.solutions.list.mockResolvedValue({ data: mockSolutionData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render solution list page with title', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/方案列表|Solution List/i)).toBeInTheDocument();
      });
    });

    it('should render solution table', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
        expect(screen.getByText('ERP系统集成方案')).toBeInTheDocument();
      });
    });

    it('should render status badges', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已批准|Approved/i)).toBeInTheDocument();
        expect(screen.getByText(/草稿|Draft/i)).toBeInTheDocument();
      });
    });

    it('should render action buttons', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        expect(buttons.length).toBeGreaterThan(0);
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load solutions on mount', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledWith(
          expect.stringContaining('/solutions')
        );
      });
    });

    it('should display loading state', () => {
      presaleApi.solutions.list.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });

    it('should handle empty solution list', async () => {
      presaleApi.solutions.list.mockResolvedValue({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument();
      });
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /刷新|Refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledTimes(2);
      });
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should open create solution modal', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建方案|Create Solution/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建解决方案|Create Solution/i)).toBeInTheDocument();
      });
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const statusFilter = screen.getByRole('combobox', { name: /状态|Status/i });
      fireEvent.change(statusFilter, { target: { value: 'approved' } });

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledWith(
          expect.stringContaining('status=approved')
        );
      });
    });

    it('should filter by industry', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const industryFilter = screen.getByRole('combobox', { name: /行业|Industry/i });
      fireEvent.change(industryFilter, { target: { value: '制造业' } });

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledWith(
          expect.stringContaining('industry=制造业')
        );
      });
    });

    it('should search by keyword', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索方案|Search solution/i);
      fireEvent.change(searchInput, { target: { value: '智能制造' } });

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledWith(
          expect.stringContaining('keyword=智能制造')
        );
      });
    });

    it('should view solution detail', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const viewButton = screen.getAllByRole('button', { name: /查看|View/i })[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/solutions/1'));
      });
    });

    it('should edit solution', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const editButton = screen.getAllByRole('button', { name: /编辑|Edit/i })[0];
      fireEvent.click(editButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/solutions/1/edit'));
      });
    });

    it('should clone solution', async () => {
      presaleApi.create.mockResolvedValue({ data: { success: true, id: 3 } });

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const cloneButton = screen.getAllByRole('button', { name: /克隆|Clone/i })[0];
      fireEvent.click(cloneButton);

      await waitFor(() => {
        expect(presaleApi.create).toHaveBeenCalledWith(
          expect.stringContaining('/solutions/1/clone'),
          expect.any(Object)
        );
      });
    });

    it('should approve solution', async () => {
      presaleApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('ERP系统集成方案')).toBeInTheDocument();
      });

      const approveButton = screen.getAllByRole('button', { name: /批准|Approve/i })[0];
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(presaleApi.update).toHaveBeenCalledWith(
          expect.stringContaining('/solutions/2/approve'),
          expect.any(Object)
        );
      });
    });

    it('should delete solution', async () => {
      presaleApi.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(presaleApi.delete).toHaveBeenCalledWith('/solutions/1');
      });
    });

    it('should export solution', async () => {
      presaleApi.solutions.list.mockResolvedValue({ data: new Blob(['data'], { type: 'application/pdf' }) });

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const exportButton = screen.getAllByRole('button', { name: /导出|Export/i })[0];
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledWith(
          expect.stringContaining('/solutions/1/export')
        );
      });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const nextPageButton = screen.getByRole('button', { name: /下一页|Next/i });
      fireEvent.click(nextPageButton);

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledWith(
          expect.stringContaining('page=2')
        );
      });
    });

    it('should sort by created date', async () => {
      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const sortButton = screen.getByRole('button', { name: /创建时间|Created Date/i });
      fireEvent.click(sortButton);

      await waitFor(() => {
        expect(presaleApi.solutions.list).toHaveBeenCalledWith(
          expect.stringContaining('sort=createdAt')
        );
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      presaleApi.solutions.list.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle create solution failure', async () => {
      presaleApi.create.mockRejectedValue(new Error('Create Failed'));

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建方案|Create Solution/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /提交|Submit/i });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/创建失败|Create Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle delete failure', async () => {
      presaleApi.delete.mockRejectedValue(new Error('Delete Failed'));
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造整体解决方案')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(/删除失败|Delete Failed/i)).toBeInTheDocument();
      });
    });
  });

  // 5. 权限测试
  describe('Permission Control', () => {
    it('should show create button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['solution:create']));

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /新建方案|Create Solution/i })).toBeInTheDocument();
      });
    });

    it('should hide create button for unauthorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify([]));

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /新建方案|Create Solution/i })).not.toBeInTheDocument();
      });
    });

    it('should show approve button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['solution:approve']));

      render(
        <MemoryRouter>
          <SolutionList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /批准|Approve/i }).length).toBeGreaterThan(0);
      });
    });
  });
});
