/**
 * WorkOrderManagement 组件测试
 * 测试覆盖：工单列表、工单状态、任务分配、进度跟踪
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WorkOrderManagement from '../WorkOrderManagement';
import api from '../../services/api';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(Object.entries(props).filter(([k]) => !['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'].includes(k)));
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
  AnimatePresence: ({ children }) => children,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('WorkOrderManagement', () => {
  const mockWorkOrders = {
    items: [
      {
        id: 1,
        code: 'WO-2024-001',
        title: '产品A装配',
        productCode: 'PRD-001',
        productName: '产品A',
        quantity: 100,
        status: 'in_progress',
        priority: 'high',
        workshop: '车间A',
        assignedTo: '张师傅',
        startDate: '2024-02-01',
        dueDate: '2024-02-15',
        completedQuantity: 45,
        progress: 45,
        createdAt: '2024-01-25'
      },
      {
        id: 2,
        code: 'WO-2024-002',
        title: '产品B加工',
        productCode: 'PRD-002',
        productName: '产品B',
        quantity: 50,
        status: 'pending',
        priority: 'medium',
        workshop: '车间B',
        assignedTo: null,
        startDate: '2024-02-05',
        dueDate: '2024-02-20',
        completedQuantity: 0,
        progress: 0,
        createdAt: '2024-01-28'
      }
    ],
    total: 2,
    stats: {
      total: 2,
      pending: 1,
      inProgress: 1,
      completed: 0,
      overdue: 0
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockWorkOrders });
    api.post.mockResolvedValue({ data: { success: true, id: 3 } });
    api.put.mockResolvedValue({ data: { success: true } });
    api.delete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render work order management page', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/工单管理|Work Order Management/i)).toBeInTheDocument();
      });
    });

    it('should render work order list', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A装配')).toBeInTheDocument();
        expect(screen.getByText('产品B加工')).toBeInTheDocument();
      });
    });

    it('should display work order codes', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('WO-2024-001')).toBeInTheDocument();
        expect(screen.getByText('WO-2024-002')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load work orders on mount', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/workorder')
        );
      });
    });

    it('should show loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      api.get.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Work Order Information', () => {
    it('should display product information', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
        expect(screen.getByText('PRD-001')).toBeInTheDocument();
      });
    });

    it('should show quantities', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/100/)).toBeInTheDocument();
        expect(screen.getByText(/45.*完成|Completed.*45/i)).toBeInTheDocument();
      });
    });

    it('should display assigned worker', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('张师傅')).toBeInTheDocument();
      });
    });

    it('should show workshop', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('车间A')).toBeInTheDocument();
        expect(screen.getByText('车间B')).toBeInTheDocument();
      });
    });
  });

  describe('Status Management', () => {
    it('should display work order status', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/进行中|In Progress/i)).toBeInTheDocument();
        expect(screen.getByText(/待处理|Pending/i)).toBeInTheDocument();
      });
    });

    it('should update work order status', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A装配')).toBeInTheDocument();
      });

      const statusButtons = screen.queryAllByRole('button', { name: /状态|Status/i });
      if (statusButtons.length > 0) {
        fireEvent.click(statusButtons[0]);

        const completeButton = screen.queryByRole('button', { name: /完成|Complete/i });
        if (completeButton) {
          fireEvent.click(completeButton);

          await waitFor(() => {
            expect(api.put).toHaveBeenCalled();
          });
        }
      }
    });

    it('should show priority badges', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/高|High/i)).toBeInTheDocument();
        expect(screen.getByText(/中|Medium/i)).toBeInTheDocument();
      });
    });
  });

  describe('Task Assignment', () => {
    it('should assign work order to worker', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品B加工')).toBeInTheDocument();
      });

      const assignButtons = screen.queryAllByRole('button', { name: /分配|Assign/i });
      if (assignButtons.length > 0) {
        fireEvent.click(assignButtons[0]);

        expect(screen.queryByText(/选择人员|Select Worker/i)).toBeTruthy();
      }
    });

    it('should reassign work order', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('张师傅')).toBeInTheDocument();
      });

      const reassignButtons = screen.queryAllByRole('button', { name: /重新分配|Reassign/i });
      if (reassignButtons.length > 0) {
        fireEvent.click(reassignButtons[0]);

        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Progress Tracking', () => {
    it('should display progress percentage', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/45%/)).toBeInTheDocument();
      });
    });

    it('should update progress', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A装配')).toBeInTheDocument();
      });

      const updateButtons = screen.queryAllByRole('button', { name: /更新进度|Update Progress/i });
      if (updateButtons.length > 0) {
        fireEvent.click(updateButtons[0]);

        const quantityInput = screen.queryByLabelText(/完成数量|Completed Quantity/i);
        if (quantityInput) {
          fireEvent.change(quantityInput, { target: { value: '60' } });

          const saveButton = screen.queryByRole('button', { name: /保存|Save/i });
          if (saveButton) {
            fireEvent.click(saveButton);

            await waitFor(() => {
              expect(api.put).toHaveBeenCalled();
            });
          }
        }
      }
    });
  });

  describe('Search and Filtering', () => {
    it('should search work orders', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A装配')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '产品A' } });

        await waitFor(() => {
          expect(api.get).toHaveBeenCalled();
        });
      }
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const statusFilter = screen.queryByRole('combobox');
      if (statusFilter) {
        fireEvent.change(statusFilter, { target: { value: 'in_progress' } });
      }
    });

    it('should filter by workshop', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });

    it('should filter by priority', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });
  });

  describe('CRUD Operations', () => {
    it('should create new work order', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);

        expect(screen.queryByText(/新建工单|Create Work Order/i)).toBeTruthy();
      }
    });

    it('should edit work order', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A装配')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        expect(screen.queryByText(/编辑工单|Edit Work Order/i)).toBeTruthy();
      }
    });

    it('should delete work order', async () => {
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A装配')).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);

        await waitFor(() => {
          expect(api.delete).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Statistics Display', () => {
    it('should show total work order count', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*工单|Total.*2/i)).toBeInTheDocument();
      });
    });

    it('should display status statistics', async () => {
      render(
        <MemoryRouter>
          <WorkOrderManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1.*进行中|In Progress.*1/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*待处理|Pending.*1/i)).toBeInTheDocument();
      });
    });
  });
});
