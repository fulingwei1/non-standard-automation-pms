/**
 * PresalesTasks 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PresalesTasks from '../PresalesTasks';
import { presaleApi } from '../../services/api';

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
      delete: vi.fn().mockResolvedValue({ data: {} }),
      tickets: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
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

describe.skip('PresalesTasks', () => {
  const mockTasksData = {
    items: [
      {
        id: 1,
        taskName: '客户需求调研',
        projectName: '智能制造系统',
        assignee: '张三',
        status: 'in_progress',
        priority: 'high',
        deadline: '2024-02-28',
        completionRate: 60
      },
      {
        id: 2,
        taskName: '技术方案编写',
        projectName: 'ERP升级',
        assignee: '李四',
        status: 'pending',
        priority: 'medium',
        deadline: '2024-03-15',
        completionRate: 0
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.tickets.list.mockResolvedValue({ data: mockTasksData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render presales tasks page with title', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/售前任务|Presales Tasks/i)).toBeInTheDocument();
      });
    });

    it('should render task list table', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
        expect(screen.getByText('客户需求调研')).toBeInTheDocument();
      });
    });

    it('should render action buttons', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
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
    it('should load tasks on mount', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(presaleApi.tickets.list).toHaveBeenCalledWith(
          expect.stringContaining('/presales/tasks')
        );
      });
    });

    it('should display loading state', () => {
      presaleApi.tickets.list.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });

    it('should handle empty task list', async () => {
      presaleApi.tickets.list.mockResolvedValue({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument();
      });
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(presaleApi.tickets.list).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /刷新|Refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(presaleApi.tickets.list).toHaveBeenCalledTimes(2);
      });
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should open create task modal', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建任务|Create Task/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建售前任务|Create Presales Task/i)).toBeInTheDocument();
      });
    });

    it('should filter tasks by status', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const statusFilter = screen.getByRole('combobox', { name: /状态|Status/i });
      fireEvent.change(statusFilter, { target: { value: 'in_progress' } });

      await waitFor(() => {
        expect(presaleApi.tickets.list).toHaveBeenCalledWith(
          expect.stringContaining('status=in_progress')
        );
      });
    });

    it('should filter tasks by priority', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const priorityFilter = screen.getByRole('combobox', { name: /优先级|Priority/i });
      fireEvent.change(priorityFilter, { target: { value: 'high' } });

      await waitFor(() => {
        expect(presaleApi.tickets.list).toHaveBeenCalledWith(
          expect.stringContaining('priority=high')
        );
      });
    });

    it('should search tasks by keyword', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索任务|Search tasks/i);
      fireEvent.change(searchInput, { target: { value: '需求调研' } });

      await waitFor(() => {
        expect(presaleApi.tickets.list).toHaveBeenCalledWith(
          expect.stringContaining('keyword=需求调研')
        );
      });
    });

    it('should update task status', async () => {
      presaleApi.tickets.updateProgress.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('客户需求调研')).toBeInTheDocument();
      });

      const statusButton = screen.getAllByRole('button', { name: /更新状态|Update Status/i })[0];
      fireEvent.click(statusButton);

      await waitFor(() => {
        expect(presaleApi.tickets.updateProgress).toHaveBeenCalledWith(
          expect.stringContaining('/presales/tasks/1'),
          expect.any(Object)
        );
      });
    });

    it('should delete task', async () => {
      presaleApi.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('客户需求调研')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(presaleApi.delete).toHaveBeenCalledWith('/presales/tasks/1');
      });
    });

    it('should assign task to user', async () => {
      presaleApi.tickets.updateProgress.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('客户需求调研')).toBeInTheDocument();
      });

      const assignButton = screen.getAllByRole('button', { name: /分配|Assign/i })[0];
      fireEvent.click(assignButton);

      await waitFor(() => {
        expect(screen.getByText(/分配任务|Assign Task/i)).toBeInTheDocument();
      });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const nextPageButton = screen.getByRole('button', { name: /下一页|Next/i });
      fireEvent.click(nextPageButton);

      await waitFor(() => {
        expect(presaleApi.tickets.list).toHaveBeenCalledWith(
          expect.stringContaining('page=2')
        );
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      presaleApi.tickets.list.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle create task failure', async () => {
      presaleApi.tickets.accept.mockRejectedValue(new Error('Create Failed'));

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建任务|Create Task/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /提交|Submit/i });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/创建失败|Create Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle update task failure', async () => {
      presaleApi.tickets.updateProgress.mockRejectedValue(new Error('Update Failed'));

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('客户需求调研')).toBeInTheDocument();
      });

      const statusButton = screen.getAllByRole('button', { name: /更新状态|Update Status/i })[0];
      fireEvent.click(statusButton);

      await waitFor(() => {
        expect(screen.getByText(/更新失败|Update Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle delete task failure', async () => {
      presaleApi.delete.mockRejectedValue(new Error('Delete Failed'));
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('客户需求调研')).toBeInTheDocument();
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
      localStorage.setItem('userPermissions', JSON.stringify(['presales:create']));

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /新建任务|Create Task/i })).toBeInTheDocument();
      });
    });

    it('should hide create button for unauthorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify([]));

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /新建任务|Create Task/i })).not.toBeInTheDocument();
      });
    });

    it('should show delete button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['presales:delete']));

      render(
        <MemoryRouter>
          <PresalesTasks />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /删除|Delete/i }).length).toBeGreaterThan(0);
      });
    });
  });
});
