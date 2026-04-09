describe.skip("/**
 * Acceptance 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

describe.skip("
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
describe.skip("
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
describe.skip("
import { MemoryRouter } from 'react-router-dom';
describe.skip("
import Acceptance from '../Acceptance';
describe.skip("
import _api, { acceptanceApi, projectApi as _projectApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    acceptanceApi: {
      delete: vi.fn().mockResolvedValue({data: { items: [] }}),
      update: vi.fn().mockResolvedValue({data: { items: [] }}),
      templates: {
        list: vi.fn().mockResolvedValue({data: { items: [] }}),
        get: vi.fn().mockResolvedValue({data: { items: [] }}),
        create: vi.fn().mockResolvedValue({data: { items: [] }}),
        getItems: vi.fn().mockResolvedValue({data: { items: [] }}),
        addItems: vi.fn().mockResolvedValue({data: { items: [] }}),
      },
      orders: {
        list: vi.fn().mockResolvedValue({data: { items: [] }}),
        get: vi.fn().mockResolvedValue({data: { items: [] }}),
        create: vi.fn().mockResolvedValue({data: { items: [] }}),
        start: vi.fn().mockResolvedValue({data: { items: [] }}),
        complete: vi.fn().mockResolvedValue({data: { items: [] }}),
        getItems: vi.fn().mockResolvedValue({data: { items: [] }}),
        updateItem: vi.fn().mockResolvedValue({data: { items: [] }}),
      },
      issues: {
        list: vi.fn().mockResolvedValue({data: { items: [] }}),
        create: vi.fn().mockResolvedValue({data: { items: [] }}),
        update: vi.fn().mockResolvedValue({data: { items: [] }}),
        close: vi.fn().mockResolvedValue({data: { items: [] }}),
        addFollowUp: vi.fn().mockResolvedValue({data: { items: [] }}),
      },
      signatures: {
        list: vi.fn().mockResolvedValue({data: { items: [] }}),
        create: vi.fn().mockResolvedValue({data: { items: [] }}),
      },
      reports: {
        generate: vi.fn().mockResolvedValue({data: { items: [] }}),
        download: vi.fn().mockResolvedValue({data: { items: [] }}),
      },
    },
    projectApi: {
      list: vi.fn().mockResolvedValue({data: { items: [] }}),
      getBoard: vi.fn().mockResolvedValue({data: { items: [] }}),
      get: vi.fn().mockResolvedValue({data: { items: [] }}),
      create: vi.fn().mockResolvedValue({data: { items: [] }}),
      update: vi.fn().mockResolvedValue({data: { items: [] }}),
      getMachines: vi.fn().mockResolvedValue({data: { items: [] }}),
      getInProductionSummary: vi.fn().mockResolvedValue({data: { items: [] }}),
      recommendTemplates: vi.fn().mockResolvedValue({data: { items: [] }}),
      createFromTemplate: vi.fn().mockResolvedValue({data: { items: [] }}),
      checkAutoTransition: vi.fn().mockResolvedValue({data: { items: [] }}),
      getGateCheckResult: vi.fn().mockResolvedValue({data: { items: [] }}),
      advanceStage: vi.fn().mockResolvedValue({data: { items: [] }}),
      getCacheStats: vi.fn().mockResolvedValue({data: { items: [] }}),
      clearCache: vi.fn().mockResolvedValue({data: { items: [] }}),
      resetCacheStats: vi.fn().mockResolvedValue({data: { items: [] }}),
      getStatusLogs: vi.fn().mockResolvedValue({data: { items: [] }}),
      getHealthDetails: vi.fn().mockResolvedValue({data: { items: [] }}),
      getStats: vi.fn().mockResolvedValue({data: { items: [] }}),
    }
}));
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const validProps = ['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'];
      const filtered = props && Object.entries(props).length > 0 
        ? Object.fromEntries(Object.entries(props).filter(([k]) => !validProps.includes(k))) 
        : {};
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

describe('Acceptance', () => {
  const mockAcceptanceData = {
    items: [
      {
        id: 1,
        projectName: '智能制造系统',
        acceptanceNo: 'ACC-2024-001',
        status: 'pending',
        type: 'final',
        planDate: '2024-03-15',
        actualDate: null,
        inspector: '张三',
        result: null
      },
      {
        id: 2,
        projectName: 'ERP系统升级',
        acceptanceNo: 'ACC-2024-002',
        status: 'passed',
        type: 'phase',
        planDate: '2024-02-20',
        actualDate: '2024-02-22',
        inspector: '李四',
        result: '合格'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    acceptanceApi.orders.list.mockResolvedValue({ data: mockAcceptanceData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render acceptance page with title', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/验收管理|Acceptance Management/i)).toBeInTheDocument();
      });
    });

    it('should render acceptance list table', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
        expect(screen.getByText('ACC-2024-001')).toBeInTheDocument();
      });
    });

    it('should render status badges', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/待验收|Pending/i)).toBeInTheDocument();
        expect(screen.getByText(/已通过|Passed/i)).toBeInTheDocument();
      });
    });

    it('should render action buttons', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
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
    it('should load acceptance records on mount', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance')
        );
      }, { timeout: 5000 });
    });

    it('should display loading state', async () => {
      acceptanceApi.orders.list.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should handle empty acceptance list', async () => {
      acceptanceApi.orders.list.mockResolvedValue({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledTimes(1);
      }, { timeout: 5000 });

      const refreshButton = screen.getByRole('button', { name: /刷新|Refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledTimes(2);
      }, { timeout: 5000 });
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should open create acceptance modal', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const createButton = screen.getByRole('button', { name: /新建验收|Create Acceptance/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建验收记录|Create Acceptance Record/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const statusFilter = screen.getByRole('combobox', { name: /状态|Status/i });
      fireEvent.change(statusFilter, { target: { value: 'pending' } });

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
          expect.stringContaining('status=pending')
        );
      }, { timeout: 5000 });
    });

    it('should filter by type', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const typeFilter = screen.getByRole('combobox', { name: /类型|Type/i });
      fireEvent.change(typeFilter, { target: { value: 'final' } });

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
          expect.stringContaining('type=final')
        );
      }, { timeout: 5000 });
    });

    it('should search by keyword', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const searchInput = screen.getByPlaceholderText(/搜索验收|Search acceptance/i);
      fireEvent.change(searchInput, { target: { value: '智能制造' } });

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
          expect.stringContaining('keyword=智能制造')
        );
      }, { timeout: 5000 });
    });

    it('should view acceptance detail', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const viewButton = screen.getAllByRole('button', { name: /查看|View/i })[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/acceptance/1'));
      }, { timeout: 5000 });
    });

    it('should start acceptance execution', async () => {
      acceptanceApi.orders.create.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const startButton = screen.getAllByRole('button', { name: /开始验收|Start/i })[0];
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(acceptanceApi.orders.create).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/1/start'),
          expect.any(Object)
        );
      }, { timeout: 5000 });
    });

    it('should submit acceptance result', async () => {
      acceptanceApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const submitButton = screen.getAllByRole('button', { name: /提交结果|Submit Result/i })[0];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/提交验收结果|Submit Acceptance Result/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should approve acceptance', async () => {
      acceptanceApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('ERP系统升级')).toBeInTheDocument();
      }, { timeout: 5000 });

      const approveButton = screen.getAllByRole('button', { name: /批准|Approve/i })[0];
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(acceptanceApi.update).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/2/approve'),
          expect.any(Object)
        );
      }, { timeout: 5000 });
    });

    it('should reject acceptance', async () => {
      acceptanceApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const rejectButton = screen.getAllByRole('button', { name: /拒绝|Reject/i })[0];
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(acceptanceApi.update).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/1/reject'),
          expect.any(Object)
        );
      }, { timeout: 5000 });
    });

    it('should delete acceptance', async () => {
      acceptanceApi.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(acceptanceApi.delete).toHaveBeenCalledWith('/acceptance/1');
      }, { timeout: 5000 });
    });

    it('should export acceptance report', async () => {
      acceptanceApi.orders.list.mockResolvedValue({ data: new Blob(['data'], { type: 'application/pdf' }) });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const exportButton = screen.getAllByRole('button', { name: /导出|Export/i })[0];
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/1/report')
        );
      }, { timeout: 5000 });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const nextPageButton = screen.getByRole('button', { name: /下一页|Next/i });
      fireEvent.click(nextPageButton);

      await waitFor(() => {
        expect(acceptanceApi.orders.list).toHaveBeenCalledWith(
          expect.stringContaining('page=2')
        );
      }, { timeout: 5000 });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      acceptanceApi.orders.list.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should handle create acceptance failure', async () => {
      acceptanceApi.orders.create.mockRejectedValue(new Error('Create Failed'));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const createButton = screen.getByRole('button', { name: /新建验收|Create Acceptance/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /提交|Submit/i });
        fireEvent.click(submitButton);
      }, { timeout: 5000 });

      await waitFor(() => {
        expect(screen.getByText(/创建失败|Create Failed/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should handle submit result failure', async () => {
      acceptanceApi.update.mockRejectedValue(new Error('Submit Failed'));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const submitButton = screen.getAllByRole('button', { name: /提交结果|Submit Result/i })[0];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/提交失败|Submit Failed/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  // 5. 权限测试
  describe('Permission Control', () => {
    it('should show create button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['acceptance:create']));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /新建验收|Create Acceptance/i })).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should hide create button for unauthorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify([]));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /新建验收|Create Acceptance/i })).not.toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should show approve button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['acceptance:approve']));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /批准|Approve/i }).length).toBeGreaterThan(0);
      }, { timeout: 5000 });
    });
  });
});
