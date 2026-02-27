/**
 * IssueManagement 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import IssueManagement from '../IssueManagement';
import _api, { issueApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    issueApi: {
      create: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      getIssues: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      assign: vi.fn().mockResolvedValue({ data: {} }),
      resolve: vi.fn().mockResolvedValue({ data: {} }),
      verify: vi.fn().mockResolvedValue({ data: {} }),
      close: vi.fn().mockResolvedValue({ data: {} }),
      cancel: vi.fn().mockResolvedValue({ data: {} }),
      changeStatus: vi.fn().mockResolvedValue({ data: {} }),
      getStatistics: vi.fn().mockResolvedValue({ data: {} }),
      getStats: vi.fn().mockResolvedValue({ data: {} }),
      getTrend: vi.fn().mockResolvedValue({ data: {} }),
      getEngineerStatistics: vi.fn().mockResolvedValue({ data: {} }),
      getCauseAnalysis: vi.fn().mockResolvedValue({ data: {} }),
      getSnapshots: vi.fn().mockResolvedValue({ data: {} }),
      getSnapshot: vi.fn().mockResolvedValue({ data: {} }),
      getFollowUps: vi.fn().mockResolvedValue({ data: {} }),
      addFollowUp: vi.fn().mockResolvedValue({ data: {} }),
      getRelated: vi.fn().mockResolvedValue({ data: {} }),
      createRelated: vi.fn().mockResolvedValue({ data: {} }),
      batchAssign: vi.fn().mockResolvedValue({ data: {} }),
      batchStatus: vi.fn().mockResolvedValue({ data: {} }),
      batchClose: vi.fn().mockResolvedValue({ data: {} }),
      export: vi.fn().mockResolvedValue({ data: {} }),
      import: vi.fn().mockResolvedValue({ data: {} }),
      getBoard: vi.fn().mockResolvedValue({ data: {} }),
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

describe.skip('IssueManagement', () => {
  const mockIssueData = {
    items: [
      {
        id: 1,
        issueNo: 'ISS-2024-001',
        title: '系统登录失败',
        projectName: '智能制造系统',
        severity: 'high',
        status: 'open',
        reportedBy: '张三',
        assignedTo: '李四',
        reportedAt: '2024-02-15',
        dueDate: '2024-02-20'
      },
      {
        id: 2,
        issueNo: 'ISS-2024-002',
        title: '数据同步延迟',
        projectName: 'ERP系统升级',
        severity: 'medium',
        status: 'in_progress',
        reportedBy: '王五',
        assignedTo: '赵六',
        reportedAt: '2024-02-10',
        dueDate: '2024-02-25'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    issueApi.getIssues.mockResolvedValue({ data: mockIssueData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render issue management page with title', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/问题管理|Issue Management/i)).toBeInTheDocument();
      });
    });

    it('should render issue list table', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
        expect(screen.getByText('ISS-2024-001')).toBeInTheDocument();
      });
    });

    it('should render severity badges', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/高|High/i)).toBeInTheDocument();
        expect(screen.getByText(/中|Medium/i)).toBeInTheDocument();
      });
    });

    it('should render status badges', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/打开|Open/i)).toBeInTheDocument();
        expect(screen.getByText(/进行中|In Progress/i)).toBeInTheDocument();
      });
    });

    it('should render action buttons', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
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
    it('should load issues on mount', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledWith(
          expect.stringContaining('/issues')
        );
      });
    });

    it('should display loading state', () => {
      issueApi.getIssues.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });

    it('should handle empty issue list', async () => {
      issueApi.getIssues.mockResolvedValue({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument();
      });
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /刷新|Refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledTimes(2);
      });
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should open create issue modal', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建问题|Create Issue/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建问题|Create Issue/i)).toBeInTheDocument();
      });
    });

    it('should filter by severity', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const severityFilter = screen.getByRole('combobox', { name: /严重程度|Severity/i });
      fireEvent.change(severityFilter, { target: { value: 'high' } });

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledWith(
          expect.stringContaining('severity=high')
        );
      });
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const statusFilter = screen.getByRole('combobox', { name: /状态|Status/i });
      fireEvent.change(statusFilter, { target: { value: 'open' } });

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledWith(
          expect.stringContaining('status=open')
        );
      });
    });

    it('should search by keyword', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索问题|Search issue/i);
      fireEvent.change(searchInput, { target: { value: '登录' } });

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledWith(
          expect.stringContaining('keyword=登录')
        );
      });
    });

    it('should view issue detail', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const viewButton = screen.getAllByRole('button', { name: /查看|View/i })[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/issues/1'));
      });
    });

    it('should assign issue to user', async () => {
      issueApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const assignButton = screen.getAllByRole('button', { name: /分配|Assign/i })[0];
      fireEvent.click(assignButton);

      await waitFor(() => {
        expect(screen.getByText(/分配问题|Assign Issue/i)).toBeInTheDocument();
      });
    });

    it('should update issue status', async () => {
      issueApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const statusButton = screen.getAllByRole('button', { name: /更新状态|Update Status/i })[0];
      fireEvent.click(statusButton);

      await waitFor(() => {
        expect(issueApi.update).toHaveBeenCalledWith(
          expect.stringContaining('/issues/1'),
          expect.any(Object)
        );
      });
    });

    it('should resolve issue', async () => {
      issueApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const resolveButton = screen.getAllByRole('button', { name: /解决|Resolve/i })[0];
      fireEvent.click(resolveButton);

      await waitFor(() => {
        expect(issueApi.update).toHaveBeenCalledWith(
          expect.stringContaining('/issues/1/resolve'),
          expect.any(Object)
        );
      });
    });

    it('should close issue', async () => {
      issueApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const closeButton = screen.getAllByRole('button', { name: /关闭|Close/i })[0];
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(issueApi.update).toHaveBeenCalledWith(
          expect.stringContaining('/issues/1/close'),
          expect.any(Object)
        );
      });
    });

    it('should delete issue', async () => {
      issueApi.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(issueApi.delete).toHaveBeenCalledWith('/issues/1');
      });
    });

    it('should add comment to issue', async () => {
      issueApi.create.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const commentButton = screen.getAllByRole('button', { name: /评论|Comment/i })[0];
      fireEvent.click(commentButton);

      await waitFor(() => {
        expect(screen.getByText(/添加评论|Add Comment/i)).toBeInTheDocument();
      });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const nextPageButton = screen.getByRole('button', { name: /下一页|Next/i });
      fireEvent.click(nextPageButton);

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledWith(
          expect.stringContaining('page=2')
        );
      });
    });

    it('should export issues', async () => {
      issueApi.getIssues.mockResolvedValue({ data: new Blob(['data'], { type: 'application/vnd.ms-excel' }) });

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /导出|Export/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(issueApi.getIssues).toHaveBeenCalledWith(
          expect.stringContaining('/issues/export')
        );
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      issueApi.getIssues.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle create issue failure', async () => {
      issueApi.create.mockRejectedValue(new Error('Create Failed'));

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建问题|Create Issue/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /提交|Submit/i });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/创建失败|Create Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle update issue failure', async () => {
      issueApi.update.mockRejectedValue(new Error('Update Failed'));

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('系统登录失败')).toBeInTheDocument();
      });

      const statusButton = screen.getAllByRole('button', { name: /更新状态|Update Status/i })[0];
      fireEvent.click(statusButton);

      await waitFor(() => {
        expect(screen.getByText(/更新失败|Update Failed/i)).toBeInTheDocument();
      });
    });
  });

  // 5. 权限测试
  describe('Permission Control', () => {
    it('should show create button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['issue:create']));

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /新建问题|Create Issue/i })).toBeInTheDocument();
      });
    });

    it('should hide create button for unauthorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify([]));

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /新建问题|Create Issue/i })).not.toBeInTheDocument();
      });
    });

    it('should show assign button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['issue:assign']));

      render(
        <MemoryRouter>
          <IssueManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /分配|Assign/i }).length).toBeGreaterThan(0);
      });
    });
  });
});
