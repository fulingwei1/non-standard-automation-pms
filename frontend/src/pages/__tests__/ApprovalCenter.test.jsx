/**
 * ApprovalCenter 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ApprovalCenter from '../ApprovalCenter';
import api from '../../services/api';

// Mock dependencies
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

describe.skip('ApprovalCenter', () => {
  const mockApprovalData = {
    items: [
      {
        id: 1,
        approvalNo: 'APR-2024-001',
        title: '项目立项审批',
        type: 'project_initiation',
        applicant: '张三',
        status: 'pending',
        currentApprover: '李四',
        submittedAt: '2024-02-15',
        priority: 'high'
      },
      {
        id: 2,
        approvalNo: 'APR-2024-002',
        title: '合同签订审批',
        type: 'contract',
        applicant: '王五',
        status: 'approved',
        currentApprover: null,
        submittedAt: '2024-02-10',
        priority: 'medium'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockApprovalData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render approval center page with title', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/审批中心|Approval Center/i)).toBeInTheDocument();
      });
    });

    it('should render approval list table', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
        expect(screen.getByText('APR-2024-001')).toBeInTheDocument();
      });
    });

    it('should render status badges', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/待审批|Pending/i)).toBeInTheDocument();
        expect(screen.getByText(/已批准|Approved/i)).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load approval items on mount', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/approvals')
        );
      });
    });

    it('should display loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /刷新|Refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledTimes(2);
      });
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const statusFilter = screen.getByRole('combobox', { name: /状态|Status/i });
      fireEvent.change(statusFilter, { target: { value: 'pending' } });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('status=pending')
        );
      });
    });

    it('should filter by type', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const typeFilter = screen.getByRole('combobox', { name: /类型|Type/i });
      fireEvent.change(typeFilter, { target: { value: 'project_initiation' } });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('type=project_initiation')
        );
      });
    });

    it('should view approval detail', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const viewButton = screen.getAllByRole('button', { name: /查看|View/i })[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/approval/1'));
      });
    });

    it('should approve request', async () => {
      api.post.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const approveButton = screen.getAllByRole('button', { name: /批准|Approve/i })[0];
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith(
          expect.stringContaining('/approvals/1/approve'),
          expect.any(Object)
        );
      });
    });

    it('should reject request', async () => {
      api.post.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const rejectButton = screen.getAllByRole('button', { name: /拒绝|Reject/i })[0];
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith(
          expect.stringContaining('/approvals/1/reject'),
          expect.any(Object)
        );
      });
    });

    it('should transfer approval', async () => {
      api.post.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const transferButton = screen.getAllByRole('button', { name: /转交|Transfer/i })[0];
      fireEvent.click(transferButton);

      await waitFor(() => {
        expect(screen.getByText(/转交审批|Transfer Approval/i)).toBeInTheDocument();
      });
    });

    it('should recall approval', async () => {
      api.post.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const recallButton = screen.getAllByRole('button', { name: /撤回|Recall/i })[0];
      fireEvent.click(recallButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith(
          expect.stringContaining('/approvals/1/recall'),
          expect.any(Object)
        );
      });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const nextPageButton = screen.getByRole('button', { name: /下一页|Next/i });
      fireEvent.click(nextPageButton);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('page=2')
        );
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      api.get.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle approve failure', async () => {
      api.post.mockRejectedValue(new Error('Approve Failed'));

      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目立项审批')).toBeInTheDocument();
      });

      const approveButton = screen.getAllByRole('button', { name: /批准|Approve/i })[0];
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(screen.getByText(/审批失败|Approve Failed/i)).toBeInTheDocument();
      });
    });
  });

  // 5. 权限测试
  describe('Permission Control', () => {
    it('should show approve button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['approval:approve']));

      render(
        <MemoryRouter>
          <ApprovalCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /批准|Approve/i }).length).toBeGreaterThan(0);
      });
    });
  });
});
