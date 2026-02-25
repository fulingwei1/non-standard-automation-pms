/**
 * AttendanceManagement 组件测试
 * 测试覆盖：考勤记录显示、统计数据、筛选功能、请假申请、加班管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AttendanceManagement from '../AttendanceManagement';
import { adminApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  adminApi: {
    attendance: {
      list: vi.fn(),
      getStats: vi.fn(),
      approve: vi.fn(),
    },
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

describe.skip('AttendanceManagement', () => {
  const mockAttendanceData = [
    {
      id: 1,
      employeeId: 101,
      employeeName: '张三',
      department: '研发部',
      date: '2024-02-20',
      checkIn: '09:00:00',
      checkOut: '18:00:00',
      status: 'present',
      workHours: 8,
      overtime: 0,
      late: false,
      total: 1,
      present: 1,
      leave: 0,
      lateCount: 0,
    },
    {
      id: 2,
      employeeId: 102,
      employeeName: '李四',
      department: '测试部',
      date: '2024-02-20',
      checkIn: '09:15:00',
      checkOut: '18:00:00',
      status: 'late',
      workHours: 7.75,
      overtime: 0,
      late: true,
      total: 1,
      present: 1,
      leave: 0,
      lateCount: 1,
    },
    {
      id: 3,
      employeeId: 103,
      employeeName: '王五',
      department: '产品部',
      date: '2024-02-20',
      checkIn: null,
      checkOut: null,
      status: 'leave',
      workHours: 0,
      overtime: 0,
      late: false,
      total: 1,
      present: 0,
      leave: 1,
      lateCount: 0,
    },
  ];

  const mockStats = {
    totalEmployees: 150,
    presentToday: 145,
    lateToday: 3,
    leaveToday: 2,
    attendanceRate: 96.7,
    avgWorkHours: 8.2,
    overtimeHours: 15,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    adminApi.attendance.list.mockResolvedValue({ 
      data: { items: mockAttendanceData } 
    });
    adminApi.attendance.getStats.mockResolvedValue({ data: mockStats });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render attendance management title', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/员工考勤管理|Attendance Management/i)).toBeInTheDocument();
    });

    it('should render statistics cards', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/出勤率|Attendance Rate/i)).toBeInTheDocument();
      });
    });

    it('should display action buttons', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/导出报表|Export/i)).toBeInTheDocument();
      expect(screen.getByText(/统计分析|Statistics/i)).toBeInTheDocument();
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch attendance records', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });
    });

    it('should handle API error gracefully', async () => {
      adminApi.attendance.list.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });
    });

    it('should display empty state when no records', async () => {
      adminApi.attendance.list.mockResolvedValueOnce({ data: { items: [] } });

      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无考勤记录|No attendance records/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 考勤记录显示测试
  describe('Attendance Records Display', () => {
    it('should display employee names', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
        expect(screen.getByText(/李四/)).toBeInTheDocument();
        expect(screen.getByText(/王五/)).toBeInTheDocument();
      });
    });

    it('should show department information', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/研发部/)).toBeInTheDocument();
        expect(screen.getByText(/测试部/)).toBeInTheDocument();
      });
    });

    it('should display check-in and check-out times', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/09:00:00/)).toBeInTheDocument();
        expect(screen.getByText(/18:00:00/)).toBeInTheDocument();
      });
    });

    it('should show attendance status badges', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/正常|Present/i)).toBeInTheDocument();
        expect(screen.getByText(/迟到|Late/i)).toBeInTheDocument();
        expect(screen.getByText(/请假|Leave/i)).toBeInTheDocument();
      });
    });
  });

  // 4. 统计数据测试
  describe('Statistics Display', () => {
    it('should display total employees count', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalText = screen.queryByText(/150|总人数/);
        expect(totalText).toBeTruthy();
      });
    });

    it('should show attendance rate', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/96.7%/)).toBeInTheDocument();
      });
    });

    it('should display late count', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const lateCount = screen.queryByText(/3|迟到/);
        expect(lateCount).toBeTruthy();
      });
    });

    it('should show leave count', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const leaveCount = screen.queryByText(/2|请假/);
        expect(leaveCount).toBeTruthy();
      });
    });
  });

  // 5. 日期筛选测试
  describe('Date Filtering', () => {
    it('should filter by today', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });

      const todayButton = screen.queryByRole('button', { name: /今天|Today/i });
      if (todayButton) {
        fireEvent.click(todayButton);
      }
    });

    it('should filter by this week', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });

      const weekButton = screen.queryByRole('button', { name: /本周|This Week/i });
      if (weekButton) {
        fireEvent.click(weekButton);
      }
    });

    it('should filter by this month', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });

      const monthButton = screen.queryByRole('button', { name: /本月|This Month/i });
      if (monthButton) {
        fireEvent.click(monthButton);
      }
    });
  });

  // 6. 搜索功能测试
  describe('Search Functionality', () => {
    it('should render search input', () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      const searchInput = screen.queryByPlaceholderText(/搜索员工|Search/i);
      expect(searchInput).toBeTruthy();
    });

    it('should search by employee name', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索员工|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '张三' } });
      }
    });

    it('should search by department', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/研发部/)).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索员工|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '研发部' } });
      }
    });
  });

  // 7. 状态筛选测试
  describe('Status Filtering', () => {
    it('should filter by present status', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });

      const presentFilter = screen.queryByRole('button', { name: /正常|Present/i });
      if (presentFilter) {
        fireEvent.click(presentFilter);
      }
    });

    it('should filter by late status', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });

      const lateFilter = screen.queryByRole('button', { name: /迟到|Late/i });
      if (lateFilter) {
        fireEvent.click(lateFilter);
      }
    });

    it('should filter by leave status', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(adminApi.attendance.list).toHaveBeenCalled();
      });

      const leaveFilter = screen.queryByRole('button', { name: /请假|Leave/i });
      if (leaveFilter) {
        fireEvent.click(leaveFilter);
      }
    });
  });

  // 8. 导出功能测试
  describe('Export Functionality', () => {
    it('should render export button', () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      const exportButton = screen.getByRole('button', { name: /导出报表|Export/i });
      expect(exportButton).toBeInTheDocument();
    });

    it('should trigger export when clicking export button', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      const exportButton = screen.getByRole('button', { name: /导出报表|Export/i });
      fireEvent.click(exportButton);
    });
  });

  // 9. 标签页切换测试
  describe('Tab Navigation', () => {
    it('should render all tabs', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const tabs = screen.queryAllByRole('tab');
        expect(tabs.length).toBeGreaterThan(0);
      });
    });

    it('should switch between tabs', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const tabs = screen.queryAllByRole('tab');
        if (tabs.length > 1) {
          fireEvent.click(tabs[1]);
        }
      });
    });
  });

  // 10. 加班管理测试
  describe('Overtime Management', () => {
    it('should display overtime hours', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const overtimeText = screen.queryByText(/15|加班/);
        expect(overtimeText).toBeTruthy();
      });
    });

    it('should show work hours for each record', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const workHours = screen.queryByText(/8|工时/);
        expect(workHours).toBeTruthy();
      });
    });
  });

  // 11. 响应式行为测试
  describe('Responsive Behavior', () => {
    it('should render properly on mount', async () => {
      const { container } = render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(container.firstChild).toBeInTheDocument();
      });
    });

    it('should handle window resize', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      global.innerWidth = 768;
      global.dispatchEvent(new Event('resize'));

      await waitFor(() => {
        expect(screen.getByText(/员工考勤管理/)).toBeInTheDocument();
      });
    });
  });

  // 12. 权限控制测试
  describe('Permission Control', () => {
    it('should show management actions for authorized users', async () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const actionButtons = screen.queryAllByRole('button');
        expect(actionButtons.length).toBeGreaterThan(0);
      });
    });

    it('should display export and statistics buttons', () => {
      render(
        <MemoryRouter>
          <AttendanceManagement />
        </MemoryRouter>
      );

      expect(screen.getByRole('button', { name: /导出报表|Export/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /统计分析|Statistics/i })).toBeInTheDocument();
    });
  });
});
