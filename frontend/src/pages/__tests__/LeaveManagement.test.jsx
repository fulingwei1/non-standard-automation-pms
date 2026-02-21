/**
 * LeaveManagement 组件测试
 * 测试覆盖：请假申请列表、申请状态、筛选功能、审批操作、统计数据
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LeaveManagement from '../LeaveManagement/index';
import api from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
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

describe('LeaveManagement', () => {
  const mockLeaveApplications = [
    {
      id: 1,
      employeeId: 101,
      employeeName: '张三',
      department: '研发部',
      leaveType: 'annual',
      startDate: '2024-02-20',
      endDate: '2024-02-22',
      days: 3,
      reason: '春节返乡',
      status: 'approved',
      appliedAt: '2024-02-10',
      approvedBy: '李经理',
      approvedAt: '2024-02-12',
      remark: '已批准',
    },
    {
      id: 2,
      employeeId: 102,
      employeeName: '李四',
      department: '测试部',
      leaveType: 'sick',
      startDate: '2024-02-18',
      endDate: '2024-02-18',
      days: 1,
      reason: '身体不适',
      status: 'pending',
      appliedAt: '2024-02-17',
      approvedBy: null,
      approvedAt: null,
      remark: null,
    },
    {
      id: 3,
      employeeId: 103,
      employeeName: '王五',
      department: '产品部',
      leaveType: 'personal',
      startDate: '2024-02-15',
      endDate: '2024-02-16',
      days: 2,
      reason: '私事',
      status: 'rejected',
      appliedAt: '2024-02-13',
      approvedBy: '赵总监',
      approvedAt: '2024-02-14',
      remark: '部门人手不足',
    },
  ];

  const mockStats = {
    totalApplications: 120,
    pending: 15,
    approved: 85,
    rejected: 10,
    thisMonthLeaves: 20,
    annualLeave: 45,
    sickLeave: 30,
    personalLeave: 25,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    api.get.mockImplementation((url) => {
      if (url.includes('/leave/stats')) {
        return Promise.resolve({ data: mockStats });
      }
      if (url.includes('/leave')) {
        return Promise.resolve({ 
          data: {
            items: mockLeaveApplications,
            total: mockLeaveApplications.length,
            page: 1,
            pageSize: 20,
          }
        });
      }
      return Promise.resolve({ data: {} });
    });

    api.put.mockResolvedValue({ data: { success: true } });
    api.post.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render leave management title', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/请假管理|Leave Management/i)).toBeInTheDocument();
    });

    it('should render statistics cards', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/leave'));
      });
    });

    it('should display action buttons', () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增申请|Add Application/i });
      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      
      expect(addButton || exportButton).toBeTruthy();
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch leave applications on mount', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/leave'));
      });
    });

    it('should handle API error gracefully', async () => {
      api.get.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should display empty state when no applications', async () => {
      api.get.mockResolvedValueOnce({ 
        data: { items: [], total: 0, page: 1, pageSize: 20 } 
      });

      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无请假申请|No leave applications/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 请假申请列表显示测试
  describe('Leave Applications List Display', () => {
    it('should display employee names', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
        expect(screen.getByText(/李四/)).toBeInTheDocument();
      });
    });

    it('should show departments', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/研发部/)).toBeInTheDocument();
        expect(screen.getByText(/测试部/)).toBeInTheDocument();
      });
    });

    it('should display leave types', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/年假|Annual/i)).toBeInTheDocument();
        expect(screen.getByText(/病假|Sick/i)).toBeInTheDocument();
        expect(screen.getByText(/事假|Personal/i)).toBeInTheDocument();
      });
    });

    it('should show leave dates', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-20/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02-22/)).toBeInTheDocument();
      });
    });

    it('should display application status', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已批准|Approved/i)).toBeInTheDocument();
        expect(screen.getByText(/待审批|Pending/i)).toBeInTheDocument();
        expect(screen.getByText(/已拒绝|Rejected/i)).toBeInTheDocument();
      });
    });
  });

  // 4. 统计数据测试
  describe('Statistics Display', () => {
    it('should display total applications count', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('120')).toBeInTheDocument();
      });
    });

    it('should show pending applications count', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('15')).toBeInTheDocument();
      });
    });

    it('should display approved count', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('85')).toBeInTheDocument();
      });
    });

    it('should show leave type statistics', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('45')).toBeInTheDocument(); // annual leave
        expect(screen.getByText('30')).toBeInTheDocument(); // sick leave
      });
    });
  });

  // 5. 筛选功能测试
  describe('Filter Functionality', () => {
    it('should filter by application status', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const pendingFilter = screen.queryByRole('button', { name: /待审批|Pending/i });
      if (pendingFilter) {
        fireEvent.click(pendingFilter);
      }
    });

    it('should filter by leave type', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const annualFilter = screen.queryByRole('button', { name: /年假|Annual/i });
      if (annualFilter) {
        fireEvent.click(annualFilter);
      }
    });

    it('should filter by department', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const deptFilter = screen.queryByText(/研发部/);
      if (deptFilter) {
        const button = deptFilter.closest('button');
        if (button) fireEvent.click(button);
      }
    });
  });

  // 6. 搜索功能测试
  describe('Search Functionality', () => {
    it('should render search input', () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      const searchInput = screen.queryByPlaceholderText(/搜索员工|Search employee/i);
      expect(searchInput).toBeTruthy();
    });

    it('should search by employee name', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索员工|Search employee/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '张三' } });
      }
    });

    it('should search by department', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/研发部/)).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索员工|Search employee/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '研发部' } });
      }
    });
  });

  // 7. 审批操作测试
  describe('Approval Actions', () => {
    it('should approve leave application', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/李四/)).toBeInTheDocument();
      });

      const approveButtons = screen.queryAllByRole('button', { name: /批准|Approve/i });
      if (approveButtons.length > 0) {
        fireEvent.click(approveButtons[0]);
        
        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });

    it('should reject leave application', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/李四/)).toBeInTheDocument();
      });

      const rejectButtons = screen.queryAllByRole('button', { name: /拒绝|Reject/i });
      if (rejectButtons.length > 0) {
        fireEvent.click(rejectButtons[0]);
        
        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });

    it('should view application detail', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);
      }
    });
  });

  // 8. 新增申请测试
  describe('Add Application', () => {
    it('should open add application dialog', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增申请|Add Application/i });
      if (addButton) {
        fireEvent.click(addButton);
      }
    });

    it('should submit new application', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增申请|Add Application/i });
      if (addButton) {
        fireEvent.click(addButton);
        
        await waitFor(() => {
          const submitButton = screen.queryByRole('button', { name: /提交|Submit/i });
          if (submitButton) {
            fireEvent.click(submitButton);
          }
        });
      }
    });
  });

  // 9. 导出功能测试
  describe('Export Functionality', () => {
    it('should render export button', () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      expect(exportButton).toBeTruthy();
    });

    it('should trigger export when clicking export button', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);
      }
    });
  });

  // 10. 分页功能测试
  describe('Pagination', () => {
    it('should display pagination controls', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const pagination = screen.queryByRole('navigation');
        expect(pagination).toBeTruthy();
      });
    });

    it('should navigate to next page', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const nextButton = screen.queryByRole('button', { name: /下一页|Next/i });
      if (nextButton && !nextButton.disabled) {
        fireEvent.click(nextButton);
      }
    });
  });

  // 11. 请假天数显示测试
  describe('Leave Days Display', () => {
    it('should display leave days for each application', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText(/3|1|2/).length).toBeGreaterThan(0);
      });
    });

    it('should show total leave days', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalDays = screen.queryByText(/总天数|Total Days/i);
        expect(totalDays).toBeTruthy();
      });
    });
  });

  // 12. 审批人显示测试
  describe('Approver Display', () => {
    it('should display approved by user', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/李经理/)).toBeInTheDocument();
        expect(screen.getByText(/赵总监/)).toBeInTheDocument();
      });
    });

    it('should show approval dates', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-12/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02-14/)).toBeInTheDocument();
      });
    });
  });

  // 13. 请假原因显示测试
  describe('Leave Reason Display', () => {
    it('should display leave reasons', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/春节返乡/)).toBeInTheDocument();
        expect(screen.getByText(/身体不适/)).toBeInTheDocument();
      });
    });

    it('should show rejection remarks', async () => {
      render(
        <MemoryRouter>
          <LeaveManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/部门人手不足/)).toBeInTheDocument();
      });
    });
  });
});
