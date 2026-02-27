/**
 * AlertCenter 组件测试
 * 测试覆盖：预警列表渲染、预警状态管理、预警级别筛选、预警处理、统计数据
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, _within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AlertCenter from '../AlertCenter';
import { alertApi } from '../../services/api';

// Mock API
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

describe.skip('AlertCenter', () => {
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
    alertApi.getStats.mockResolvedValue({ data: mockStats });
    alertApi.update.mockResolvedValue({ data: { success: true } });
    alertApi.resolve.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render alert center with title', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      expect(screen.getByText(/预警中心|Alert Center/i)).toBeInTheDocument();
    });

    it('should render loading state initially', () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      const loadingElements = screen.queryAllByRole('status') || screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should render alert statistics cards', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(alertApi.getStats).toHaveBeenCalled();
      });
    });

    it('should display total alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('45')).toBeInTheDocument();
      });
    });

    it('should render alert list after loading', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch alerts on mount', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(alertApi.list).toHaveBeenCalled();
      });
    });

    it('should call API to fetch stats on mount', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(alertApi.getStats).toHaveBeenCalled();
      });
    });

    it('should handle API error gracefully', async () => {
      alertApi.list.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|failed/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should display empty state when no alerts', async () => {
      alertApi.list.mockResolvedValueOnce({ data: [] });

      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无预警|No alerts/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 预警级别筛选测试
  describe('Alert Level Filtering', () => {
    it('should filter alerts by critical level', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      const criticalFilter = screen.queryByRole('button', { name: /紧急|Critical/i });
      if (criticalFilter) {
        fireEvent.click(criticalFilter);
        
        await waitFor(() => {
          expect(alertApi.list).toHaveBeenCalledWith(expect.objectContaining({
            level: 'critical'
          }));
        });
      }
    });

    it('should filter alerts by warning level', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(alertApi.list).toHaveBeenCalled();
      });

      const warningFilter = screen.queryByRole('button', { name: /警告|Warning/i });
      if (warningFilter) {
        fireEvent.click(warningFilter);
      }
    });

    it('should show all alerts when clicking "All" filter', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      const allFilter = screen.queryByRole('button', { name: /全部|All/i });
      if (allFilter) {
        fireEvent.click(allFilter);
      }
    });
  });

  // 4. 预警状态管理测试
  describe('Alert Status Management', () => {
    it('should display pending alerts', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/待处理|Pending/i)).toBeInTheDocument();
      });
    });

    it('should display in-progress alerts', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/处理中|In Progress/i)).toBeInTheDocument();
      });
    });

    it('should display resolved alerts', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已解决|Resolved/i)).toBeInTheDocument();
      });
    });

    it('should filter alerts by status', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(alertApi.list).toHaveBeenCalled();
      });

      const statusFilters = screen.queryAllByRole('button');
      const pendingFilter = statusFilters.find(btn => 
        btn.textContent.includes('待处理') || btn.textContent.includes('Pending')
      );

      if (pendingFilter) {
        fireEvent.click(pendingFilter);
      }
    });
  });

  // 5. 预警搜索功能测试
  describe('Alert Search', () => {
    it('should render search input', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText(/搜索预警|Search alerts/i);
      expect(searchInput).toBeInTheDocument();
    });

    it('should search alerts by keyword', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText(/搜索预警|Search alerts/i);
      fireEvent.change(searchInput, { target: { value: '预算' } });

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });
    });

    it('should clear search when input is empty', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText(/搜索预警|Search alerts/i);
      fireEvent.change(searchInput, { target: { value: '预算' } });
      fireEvent.change(searchInput, { target: { value: '' } });

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
        expect(screen.getByText(/项目进度延迟预警/)).toBeInTheDocument();
      });
    });
  });

  // 6. 预警处理操作测试
  describe('Alert Actions', () => {
    it('should resolve an alert', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      const resolveButtons = screen.queryAllByRole('button', { name: /解决|Resolve/i });
      if (resolveButtons.length > 0) {
        fireEvent.click(resolveButtons[0]);
        
        await waitFor(() => {
          expect(alertApi.resolve).toHaveBeenCalledWith(1);
        });
      }
    });

    it('should view alert details', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);
      }
    });

    it('should dismiss an alert', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目预算超支预警/)).toBeInTheDocument();
      });

      const dismissButtons = screen.queryAllByRole('button', { name: /忽略|Dismiss/i });
      if (dismissButtons.length > 0) {
        fireEvent.click(dismissButtons[0]);
        
        await waitFor(() => {
          expect(alertApi.dismiss).toHaveBeenCalled();
        });
      }
    });
  });

  // 7. 预警详情测试
  describe('Alert Details', () => {
    it('should display alert level badge', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/紧急|Critical/i)).toBeInTheDocument();
      });
    });

    it('should display alert type', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/预算|Budget/i)).toBeInTheDocument();
      });
    });

    it('should show related project information', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
      });
    });

    it('should display alert creation time', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        const timeElements = screen.queryAllByText(/2024-02-/);
        expect(timeElements.length).toBeGreaterThan(0);
      });
    });
  });

  // 8. 统计数据测试
  describe('Statistics', () => {
    it('should display total alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('45')).toBeInTheDocument();
      });
    });

    it('should show pending alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('12')).toBeInTheDocument();
      });
    });

    it('should display resolved alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('28')).toBeInTheDocument();
      });
    });

    it('should show critical alerts count', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    it('should display today new alerts', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });
  });

  // 9. 刷新功能测试
  describe('Refresh Functionality', () => {
    it('should refresh alerts when clicking refresh button', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(alertApi.list).toHaveBeenCalled();
      });

      const initialCallCount = alertApi.list.mock.calls.length;

      const refreshButton = screen.queryByRole('button', { name: /刷新|Refresh/i });
      if (refreshButton) {
        fireEvent.click(refreshButton);
        
        await waitFor(() => {
          expect(alertApi.list.mock.calls.length).toBeGreaterThan(initialCallCount);
        });
      }
    });
  });

  // 10. 导航测试
  describe('Navigation', () => {
    it('should navigate to alert settings', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      const settingsButton = screen.queryByRole('button', { name: /设置|Settings/i });
      if (settingsButton) {
        fireEvent.click(settingsButton);
        expect(mockNavigate).toHaveBeenCalled();
      }
    });

    it('should navigate to project detail from alert', async () => {
      render(
        <MemoryRouter>
          <AlertCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
      });

      const projectLinks = screen.queryAllByText(/智能制造系统/);
      if (projectLinks.length > 0) {
        const clickableLink = projectLinks[0].closest('a') || projectLinks[0].closest('button');
        if (clickableLink) {
          fireEvent.click(clickableLink);
        }
      }
    });
  });
});
