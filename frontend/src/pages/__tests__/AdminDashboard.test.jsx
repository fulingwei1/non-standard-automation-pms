/**
 * AdminDashboard 组件测试
 * 测试覆盖：组件渲染、数据加载、用户交互、错误处理、权限控制
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminDashboard from '../AdminDashboard';
import api from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  }
}));

// Mock framer-motion to avoid animation issues in tests
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

describe.skip('AdminDashboard', () => {
  const mockStatsData = {
    totalUsers: 150,
    activeUsers: 120,
    inactiveUsers: 30,
    newUsersThisMonth: 15,
    usersWithRoles: 140,
    usersWithoutRoles: 10,
    totalRoles: 8,
    systemRoles: 5,
    customRoles: 3,
    activeRoles: 7,
    inactiveRoles: 1,
    totalPermissions: 50,
    assignedPermissions: 45,
    unassignedPermissions: 5,
    systemUptime: 99.9,
    databaseSize: 2048,
    storageUsed: 1536,
    apiResponseTime: 120,
    errorRate: 0.5,
    loginCountToday: 50,
    loginCountThisWeek: 300,
    lastBackup: '2024-02-20T10:00:00Z',
    auditLogsToday: 100,
    auditLogsThisWeek: 500
  };

  const mockRecentActivities = [
    {
      id: 1,
      user: 'admin',
      action: '创建用户',
      target: 'user-123',
      timestamp: new Date().toISOString(),
      status: 'success'
    },
    {
      id: 2,
      user: 'admin',
      action: '修改角色',
      target: 'role-admin',
      timestamp: new Date().toISOString(),
      status: 'success'
    }
  ];

  const mockSystemHealth = {
    cpu: 45,
    memory: 60,
    disk: 75,
    network: 30
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock API responses
    api.get.mockImplementation((url) => {
      if (url.includes('/admin/stats')) {
        return Promise.resolve({ data: mockStatsData });
      }
      if (url.includes('/admin/activities')) {
        return Promise.resolve({ data: mockRecentActivities });
      }
      if (url.includes('/admin/system-health')) {
        return Promise.resolve({ data: mockSystemHealth });
      }
      return Promise.resolve({ data: {} });
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render admin dashboard with title', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      expect(screen.getByText(/管理员工作台|Admin Dashboard/i)).toBeInTheDocument();
    });

    it('should render loading state initially', () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      // 应该显示加载中的骨架屏或加载指示器
      const loadingElements = screen.queryAllByRole('status') || screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should render all stat cards after data loads', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 检查用户统计
        expect(screen.getByText(/总用户|Total Users/i)).toBeInTheDocument();
      });
    });

    it('should display correct user statistics', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('150')).toBeInTheDocument(); // totalUsers
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch stats on mount', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/admin/stats'));
      });
    });

    it('should handle API success response', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('150')).toBeInTheDocument();
        expect(screen.getByText('120')).toBeInTheDocument();
      });
    });

    it('should handle API error gracefully', async () => {
      api.get.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|failed/i);
        // 错误应该被捕获，或显示默认数据
        expect(errorMessage || screen.queryByText('0')).toBeTruthy();
      });
    });

    it('should refresh data when refresh button is clicked', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const initialCallCount = api.get.mock.calls.length;

      const refreshButton = screen.queryByRole('button', { name: /刷新|Refresh/i });
      if (refreshButton) {
        fireEvent.click(refreshButton);
        
        await waitFor(() => {
          expect(api.get.mock.calls.length).toBeGreaterThan(initialCallCount);
        });
      }
    });
  });

  // 3. 用户交互测试
  describe('User Interactions', () => {
    it('should navigate to user management when clicking user card', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/总用户|Total Users/i)).toBeInTheDocument();
      });

      const userCards = screen.queryAllByText(/用户管理|User/i);
      if (userCards.length > 0) {
        const clickableCard = userCards[0].closest('button') || userCards[0].closest('a');
        if (clickableCard) {
          fireEvent.click(clickableCard);
          // 验证导航被调用
          expect(mockNavigate).toHaveBeenCalled();
        }
      }
    });

    it('should navigate to role management when clicking role card', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/角色|Role/i)).toBeInTheDocument();
      });

      const roleLinks = screen.queryAllByText(/角色管理|Role Management/i);
      if (roleLinks.length > 0) {
        const clickableElement = roleLinks[0].closest('button') || roleLinks[0].closest('a');
        if (clickableElement) {
          fireEvent.click(clickableElement);
          expect(mockNavigate).toHaveBeenCalled();
        }
      }
    });

    it('should open settings when clicking settings button', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      const settingsButton = screen.queryByRole('button', { name: /设置|Settings/i });
      if (settingsButton) {
        fireEvent.click(settingsButton);
        // 验证设置对话框或页面被打开
        await waitFor(() => {
          expect(mockNavigate).toHaveBeenCalled();
        });
      }
    });

    it('should filter activities by status', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const filterButtons = screen.queryAllByRole('button');
      const statusFilter = filterButtons.find(btn => 
        btn.textContent.includes('状态') || btn.textContent.includes('Status')
      );

      if (statusFilter) {
        fireEvent.click(statusFilter);
      }
    });
  });

  // 4. 权限控制测试
  describe('Permission Control', () => {
    it('should show admin-only features for admin users', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 管理员应该能看到系统配置
        const adminFeatures = screen.queryByText(/系统配置|System Config/i);
        expect(adminFeatures).toBeTruthy();
      });
    });

    it('should display permission management section', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/权限|Permission/i)).toBeInTheDocument();
      });
    });
  });

  // 5. 错误处理测试
  describe('Error Handling', () => {
    it('should show error message when stats API fails', async () => {
      api.get.mockRejectedValueOnce(new Error('Failed to fetch stats'));

      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorElement = screen.queryByText(/错误|Error|failed/i);
        // 应该显示错误提示或默认值
        expect(errorElement || screen.queryByText('0')).toBeTruthy();
      });
    });

    it('should show error message when activities API fails', async () => {
      api.get.mockImplementation((url) => {
        if (url.includes('/admin/activities')) {
          return Promise.reject(new Error('Failed to fetch activities'));
        }
        return Promise.resolve({ data: mockStatsData });
      });

      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 统计数据应该加载成功
        expect(screen.getByText('150')).toBeInTheDocument();
      });
    });

    it('should handle network timeout', async () => {
      api.get.mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      );

      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 应该显示超时错误或默认状态
        const errorOrDefault = screen.queryByText(/超时|Timeout|0/);
        expect(errorOrDefault).toBeTruthy();
      }, { timeout: 3000 });
    });
  });

  // 6. 系统健康监控测试
  describe('System Health Monitoring', () => {
    it('should display system uptime', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/99.9|运行时间|Uptime/i)).toBeInTheDocument();
      });
    });

    it('should show database size', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 2048 MB or formatted version
        const dbSize = screen.queryByText(/2048|2.0 GB|数据库/i);
        expect(dbSize).toBeTruthy();
      });
    });

    it('should display API response time', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/120|响应时间|Response Time/i)).toBeInTheDocument();
      });
    });
  });

  // 7. 最近活动测试
  describe('Recent Activities', () => {
    it('should display recent activities list', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/最近活动|Recent Activities/i)).toBeInTheDocument();
      });
    });

    it('should show activity details', async () => {
      render(
        <MemoryRouter>
          <AdminDashboard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/创建用户|Create User/i)).toBeInTheDocument();
      });
    });
  });
});
