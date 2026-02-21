/**
 * Acceptance 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Acceptance from '../Acceptance';
import api from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    tr: ({ children, ...props }) => <tr {...props}>{children}</tr>,
  },
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
    api.get.mockResolvedValue({ data: mockAcceptanceData });
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
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance')
        );
      });
    });

    it('should display loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });

    it('should handle empty acceptance list', async () => {
      api.get.mockResolvedValue({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument();
      });
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
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
    it('should open create acceptance modal', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建验收|Create Acceptance/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建验收记录|Create Acceptance Record/i)).toBeInTheDocument();
      });
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
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
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const typeFilter = screen.getByRole('combobox', { name: /类型|Type/i });
      fireEvent.change(typeFilter, { target: { value: 'final' } });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('type=final')
        );
      });
    });

    it('should search by keyword', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索验收|Search acceptance/i);
      fireEvent.change(searchInput, { target: { value: '智能制造' } });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('keyword=智能制造')
        );
      });
    });

    it('should view acceptance detail', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const viewButton = screen.getAllByRole('button', { name: /查看|View/i })[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/acceptance/1'));
      });
    });

    it('should start acceptance execution', async () => {
      api.post.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const startButton = screen.getAllByRole('button', { name: /开始验收|Start/i })[0];
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/1/start'),
          expect.any(Object)
        );
      });
    });

    it('should submit acceptance result', async () => {
      api.put.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const submitButton = screen.getAllByRole('button', { name: /提交结果|Submit Result/i })[0];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/提交验收结果|Submit Acceptance Result/i)).toBeInTheDocument();
      });
    });

    it('should approve acceptance', async () => {
      api.put.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('ERP系统升级')).toBeInTheDocument();
      });

      const approveButton = screen.getAllByRole('button', { name: /批准|Approve/i })[0];
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(api.put).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/2/approve'),
          expect.any(Object)
        );
      });
    });

    it('should reject acceptance', async () => {
      api.put.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const rejectButton = screen.getAllByRole('button', { name: /拒绝|Reject/i })[0];
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(api.put).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/1/reject'),
          expect.any(Object)
        );
      });
    });

    it('should delete acceptance', async () => {
      api.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(api.delete).toHaveBeenCalledWith('/acceptance/1');
      });
    });

    it('should export acceptance report', async () => {
      api.get.mockResolvedValue({ data: new Blob(['data'], { type: 'application/pdf' }) });

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const exportButton = screen.getAllByRole('button', { name: /导出|Export/i })[0];
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/acceptance/1/report')
        );
      });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
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
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle create acceptance failure', async () => {
      api.post.mockRejectedValue(new Error('Create Failed'));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建验收|Create Acceptance/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /提交|Submit/i });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/创建失败|Create Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle submit result failure', async () => {
      api.put.mockRejectedValue(new Error('Submit Failed'));

      render(
        <MemoryRouter>
          <Acceptance />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const submitButton = screen.getAllByRole('button', { name: /提交结果|Submit Result/i })[0];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/提交失败|Submit Failed/i)).toBeInTheDocument();
      });
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
      });
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
      });
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
      });
    });
  });
});
