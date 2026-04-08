/**
 * AlertCenter 组件测试
 * 测试覆盖：预警列表渲染、预警状态管理、预警级别筛选、预警处理、统计数据
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AlertCenter from '../AlertCenter';
import { alertApi, notificationApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  alertApi: {
    list: vi.fn().mockResolvedValue({ data: [] }),
    get: vi.fn(),
    acknowledge: vi.fn().mockResolvedValue({ data: { success: true } }),
    resolve: vi.fn().mockResolvedValue({ data: { success: true } }),
    close: vi.fn().mockResolvedValue({ data: { success: true } }),
    ignore: vi.fn().mockResolvedValue({ data: { success: true } }),
    rules: {
      list: vi.fn().mockResolvedValue({ data: [] }),
      get: vi.fn(),
      create: vi.fn().mockResolvedValue({ data: { success: true } }),
      update: vi.fn().mockResolvedValue({ data: { success: true } }),
      delete: vi.fn().mockResolvedValue({ data: { success: true } }),
      toggle: vi.fn().mockResolvedValue({ data: { success: true } }),
    },
    templates: vi.fn().mockResolvedValue({ data: [] }),
    statistics: vi.fn().mockResolvedValue({ data: {} }),
    dashboard: vi.fn().mockResolvedValue({ data: {} }),
    trends: vi.fn().mockResolvedValue({ data: [] }),
    responseMetrics: vi.fn().mockResolvedValue({ data: {} }),
    efficiencyMetrics: vi.fn().mockResolvedValue({ data: {} }),
    exportExcel: vi.fn(),
    exportPdf: vi.fn(),
  },
  notificationApi: {
    list: vi.fn().mockResolvedValue({ data: [] }),
    get: vi.fn(),
    getUnreadCount: vi.fn().mockResolvedValue({ data: { count: 0 } }),
    markRead: vi.fn().mockResolvedValue({ data: { success: true } }),
    batchRead: vi.fn().mockResolvedValue({ data: { success: true } }),
    readAll: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    getSettings: vi.fn().mockResolvedValue({ data: {} }),
    updateSettings: vi.fn().mockResolvedValue({ data: { success: true } }),
  },
}));

// Mock framer-motion
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

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('AlertCenter', () => {
  const mockAlerts = [
    {
      id: 1,
      title: '项目预算超支预警',
      level: 'critical',
      status: 'pending',
      type: 'budget',
      description: '项目PROJ-001预算超支20%',
      projectId: 1,
      projectName: '智能制造系统',
      createdAt: '2024-02-20T10:00:00Z',
      triggerTime: '2024-02-20T10:00:00Z',
      responseTime: null,
      resolvedAt: null,
    },
    {
      id: 2,
      title: '项目进度延迟预警',
      level: 'warning',
      status: 'in_progress',
      type: 'schedule',
      description: '项目PROJ-002进度延迟5天',
      projectId: 2,
      projectName: 'ERP系统升级',
      createdAt: '2024-02-19T14:00:00Z',
      triggerTime: '2024-02-19T14:00:00Z',
      responseTime: '2024-02-19T15:00:00Z',
      resolvedAt: null,
    },
    {
      id: 3,
      title: '资源冲突预警',
      level: 'urgent',
      status: 'resolved',
      type: 'resource',
      description: '工程师张三在3个项目中同时分配',
      projectId: 3,
      projectName: 'CRM系统开发',
      createdAt: '2024-02-18T09:00:00Z',
      triggerTime: '2024-02-18T09:00:00Z',
      responseTime: '2024-02-18T10:00:00Z',
      resolvedAt: '2024-02-18T16:00:00Z',
    },
  ];

  const mockStats = {
    total: 45,
    pending: 12,
    resolved: 28,
    critical: 3,
    today_new: 5,
    urgent: 8,
    warning: 22,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    alertApi.list.mockResolvedValue({ data: mockAlerts });
    alertApi.statistics.mockResolvedValue({ data: mockStats });
    alertApi.dashboard.mockResolvedValue({ data: mockStats });
    notificationApi.getUnreadCount.mockResolvedValue({ data: { count: 0 } });
  });

  describe('Statistics', () => {
    it('should display total alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(alertApi.statistics).toHaveBeenCalled();
      });

      expect(screen.getByText('总预警数')).toBeInTheDocument();
      expect(screen.getByText(/45/)).toBeInTheDocument();
    });

    it('should display pending alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/待处理/)).toBeInTheDocument();
      });

      expect(screen.getByText(/12/)).toBeInTheDocument();
    });

    it('should display critical alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/严重/)).toBeInTheDocument();
      });

      expect(screen.getByText(/3/)).toBeInTheDocument();
    });

    it('should display today\'s new alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/今日新增|Today/)).toBeInTheDocument();
      });

      expect(screen.getByText(/5/)).toBeInTheDocument();
    });

    it('should display resolved alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已解决/)).toBeInTheDocument();
      });

      expect(screen.getByText(/28/)).toBeInTheDocument();
    });
  });

  describe('Alert List', () => {
    it('should render alert list with details', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      expect(screen.getByText(/项目进度延迟预警/)).toBeInTheDocument();
      expect(screen.getByText(/资源冲突预警/)).toBeInTheDocument();

      // Check alert details
      expect(screen.getByText(/项目PROJ-001预算超支20%/)).toBeInTheDocument();
      expect(screen.getByText(/项目PROJ-002进度延迟5天/)).toBeInTheDocument();
    });

    it('should display alert levels with proper styling', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/严重/)).toBeInTheDocument();
      });

      const warningBadges = screen.getAllByText(/警告|Warning/);
      expect(warningBadges.length).toBeGreaterThan(0);
    });

    it('should display alert statuses', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        const pendingStatusElements = screen.getAllByText(/待处理/);
        expect(pendingStatusElements.length).toBeGreaterThan(0);
      });

      expect(screen.getByText(/处理中/)).toBeInTheDocument();
      expect(screen.getByText(/已解决/)).toBeInTheDocument();
    });
  });

  describe('Alert Actions', () => {
    it('should handle alert acknowledgment', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      // Find the specific acknowledge button for the first alert
      const ackButton = screen.getByRole('button', { name: /确认|Acknowledge|ack/i });
      fireEvent.click(ackButton);

      await waitFor(() => {
        expect(alertApi.acknowledge).toHaveBeenCalledWith(1);
      });
    });

    it('should handle alert resolution', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目进度延迟预警/)).toBeInTheDocument();
      });

      // Find the specific resolve button for the second alert
      const resolveButton = screen.getByRole('button', { name: /解决|Resolve|resolv/i });
      fireEvent.click(resolveButton);

      await waitFor(() => {
        expect(alertApi.resolve).toHaveBeenCalledWith(2, expect.anything());
      });
    });

    it('should handle alert ignoring', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/资源冲突预警/)).toBeInTheDocument();
      });

      // Find the specific ignore button for the third alert
      const ignoreButton = screen.getByRole('button', { name: /忽略|Ignore|ignor/i });
      fireEvent.click(ignoreButton);

      await waitFor(() => {
        expect(alertApi.ignore).toHaveBeenCalledWith(3, expect.anything());
      });
    });
  });

  describe('Alert Details', () => {
    it('should display alert creation time', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      // Should show formatted date/time
      expect(screen.getByText(/2024/)).toBeInTheDocument();
    });

    it('should display project information', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
      });

      expect(screen.getByText(/ERP系统升级/)).toBeInTheDocument();
    });

    it('should link to project details', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        const projectLinks = screen.getAllByText(/智能制造系统|智能/);
        expect(projectLinks.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Filtering', () => {
    it('should filter alerts by level', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      // Wait for filters to be rendered before interacting
      await waitFor(() => {
        const comboboxes = screen.queryAllByRole('combobox');
        expect(comboboxes.length).toBeGreaterThan(0);
      });
      
      // Find the level filter by its accessible name or role
      let levelFilter;
      try {
        levelFilter = screen.getByRole('combobox', { name: /预警级别|level/i });
      } catch {
        const comboboxes = screen.getAllByRole('combobox');
        levelFilter = comboboxes[0]; // fallback to first combobox
      }
      
      fireEvent.click(levelFilter);
      
      // Wait for options to appear
      await waitFor(() => {
        expect(screen.getByText('严重')).toBeInTheDocument();
      });
      
      const criticalOption = screen.getByText('严重');
      fireEvent.click(criticalOption);

      await waitFor(() => {
        expect(alertApi.list).toHaveBeenCalledWith(expect.objectContaining({
          level: 'critical'
        }));
      });
    });

    it('should filter alerts by status', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      // Wait for filters to be rendered before interacting
      await waitFor(() => {
        const comboboxes = screen.queryAllByRole('combobox');
        expect(comboboxes.length).toBeGreaterThan(1);
      });
      
      // Find the status filter by its accessible name or role
      let statusFilter;
      try {
        statusFilter = screen.getByRole('combobox', { name: /预警状态|status/i });
      } catch {
        const comboboxes = screen.getAllByRole('combobox');
        statusFilter = comboboxes[1]; // fallback to second combobox
      }
      
      fireEvent.click(statusFilter);
      
      // Wait for options to appear
      await waitFor(() => {
        expect(screen.getByText('待处理')).toBeInTheDocument();
      });
      
      const pendingOption = screen.getByText('待处理');
      fireEvent.click(pendingOption);

      await waitFor(() => {
        expect(alertApi.list).toHaveBeenCalledWith(expect.objectContaining({
          status: 'pending'
        }));
      });
    });

    it('should filter alerts by date range', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      // Simulate date range filter
      const dateFilter = screen.getByPlaceholderText?.('选择日期范围') || 
                         screen.getByText?.('今天')?.closest('button') ||
                         screen.getByText?.('本周')?.closest('button');
      
      if (dateFilter) {
        fireEvent.click(dateFilter);
        
        await waitFor(() => {
          expect(alertApi.list).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Pagination', () => {
    it('should handle pagination when multiple pages of alerts exist', async () => {
      const manyAlerts = Array.from({ length: 25 }, (_, i) => ({
        id: i + 1,
        title: `预警 ${i + 1}`,
        level: i % 3 === 0 ? 'critical' : i % 3 === 1 ? 'warning' : 'info',
        status: i % 3 === 0 ? 'pending' : i % 3 === 1 ? 'in_progress' : 'resolved',
        type: 'budget',
        description: `描述 ${i + 1}`,
        projectId: i + 1,
        projectName: `项目 ${i + 1}`,
        createdAt: '2024-02-20T10:00:00Z',
        triggerTime: '2024-02-20T10:00:00Z',
        responseTime: null,
        resolvedAt: null,
      }));

      alertApi.list.mockResolvedValue({ data: manyAlerts, meta: { total: 25, page: 1, pageSize: 10 } });

      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/预警 1/)).toBeInTheDocument();
      });

      // Should show pagination controls for multiple pages
      expect(screen.getByRole('button', { name: /2/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /下一页/ })).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when loading fails', async () => {
      const errorMessage = 'Failed to load alerts';
      alertApi.list.mockRejectedValue(new Error(errorMessage));
      alertApi.statistics.mockRejectedValue(new Error(errorMessage));

      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|失败/)).toBeInTheDocument();
      });
    });

    it('should retry loading when error occurs', async () => {
      // First call fails, second succeeds
      alertApi.list.mockRejectedValueOnce(new Error('Network error'))
                 .mockResolvedValue({ data: mockAlerts });
      alertApi.statistics.mockRejectedValueOnce(new Error('Network error'))
                          .mockResolvedValue({ data: mockStats });

      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警|预算超支/)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('should display loading spinner while fetching data', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      // Wait briefly to ensure loading state renders
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Check for loading state with flexible text matching
      const loadingText = screen.queryByText(/加载|Loading/);
      expect(loadingText).not.toBeNull();
    });

    it('should hide loading spinner after data loads', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      // Wait for API call to complete and data to load
      await waitFor(() => {
        expect(screen.queryByText(/项目预算超支预警/)).toBeInTheDocument();
      });
      
      // By this time, loading state should be gone
      // Verify that we're now showing actual alert data instead of loading
      expect(screen.queryByText(/加载|Loading/)).toBeNull();
    });
  });
});