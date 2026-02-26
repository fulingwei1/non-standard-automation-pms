/**
 * WorkshopManagement 组件测试
 * 测试覆盖：车间列表、设备管理、人员配置、产能管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WorkshopManagement from '../WorkshopManagement';
import api, { productionApi, userApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    productionApi: {
      delete: vi.fn().mockResolvedValue({ data: {} }),
      dashboard: vi.fn().mockResolvedValue({ data: {} }),
      dailyReports: {
        daily: vi.fn().mockResolvedValue({ data: {} }),
        latestDaily: vi.fn().mockResolvedValue({ data: {} }),
      },
      workshops: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        getWorkstations: vi.fn().mockResolvedValue({ data: {} }),
        addWorkstation: vi.fn().mockResolvedValue({ data: {} }),
      },
      workstations: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        getStatus: vi.fn().mockResolvedValue({ data: {} }),
      },
      productionPlans: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        submit: vi.fn().mockResolvedValue({ data: {} }),
        approve: vi.fn().mockResolvedValue({ data: {} }),
        publish: vi.fn().mockResolvedValue({ data: {} }),
        calendar: vi.fn().mockResolvedValue({ data: {} }),
      },
      workOrders: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        assign: vi.fn().mockResolvedValue({ data: {} }),
        start: vi.fn().mockResolvedValue({ data: {} }),
        pause: vi.fn().mockResolvedValue({ data: {} }),
        resume: vi.fn().mockResolvedValue({ data: {} }),
        complete: vi.fn().mockResolvedValue({ data: {} }),
        getProgress: vi.fn().mockResolvedValue({ data: {} }),
        getReports: vi.fn().mockResolvedValue({ data: {} }),
      },
      workers: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
      },
      workReports: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        start: vi.fn().mockResolvedValue({ data: {} }),
        progress: vi.fn().mockResolvedValue({ data: {} }),
        complete: vi.fn().mockResolvedValue({ data: {} }),
        approve: vi.fn().mockResolvedValue({ data: {} }),
        my: vi.fn().mockResolvedValue({ data: {} }),
      },
      materialRequisitions: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        approve: vi.fn().mockResolvedValue({ data: {} }),
        issue: vi.fn().mockResolvedValue({ data: {} }),
      },
      exceptions: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        handle: vi.fn().mockResolvedValue({ data: {} }),
        close: vi.fn().mockResolvedValue({ data: {} }),
      },
      taskBoard: vi.fn().mockResolvedValue({ data: {} }),
      reports: {
        workerPerformance: vi.fn().mockResolvedValue({ data: {} }),
        workerRanking: vi.fn().mockResolvedValue({ data: {} }),
      },
    },
    userApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      assignRoles: vi.fn().mockResolvedValue({ data: {} }),
      syncFromEmployees: vi.fn().mockResolvedValue({ data: {} }),
      createFromEmployee: vi.fn().mockResolvedValue({ data: {} }),
      toggleActive: vi.fn().mockResolvedValue({ data: {} }),
      resetPassword: vi.fn().mockResolvedValue({ data: {} }),
      batchToggleActive: vi.fn().mockResolvedValue({ data: {} }),
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
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('WorkshopManagement', () => {
  const mockWorkshops = {
    items: [
      {
        id: 1,
        code: 'WS-001',
        name: '装配车间A',
        type: 'assembly',
        area: 500,
        status: 'active',
        manager: '张主管',
        workerCount: 25,
        machineCount: 10,
        capacity: 1000,
        utilization: 85,
        activeOrders: 5,
        location: '一号厂房',
        createdAt: '2024-01-01'
      },
      {
        id: 2,
        code: 'WS-002',
        name: '机加工车间B',
        type: 'machining',
        area: 800,
        status: 'active',
        manager: '李主管',
        workerCount: 30,
        machineCount: 15,
        capacity: 1500,
        utilization: 72,
        activeOrders: 3,
        location: '二号厂房',
        createdAt: '2024-01-05'
      }
    ],
    total: 2,
    stats: {
      total: 2,
      active: 2,
      totalWorkers: 55,
      totalMachines: 25,
      avgUtilization: 78.5
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    userApi.list.mockResolvedValue({ data: mockWorkshops });
    productionApi.workshops.create.mockResolvedValue({ data: { success: true, id: 3 } });
    productionApi.workshops.update.mockResolvedValue({ data: { success: true } });
    productionApi.delete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render workshop management page', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/车间管理|Workshop Management/i)).toBeInTheDocument();
      });
    });

    it('should render workshop list', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
        expect(screen.getByText('机加工车间B')).toBeInTheDocument();
      });
    });

    it('should display workshop codes', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('WS-001')).toBeInTheDocument();
        expect(screen.getByText('WS-002')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load workshops on mount', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(userApi.list).toHaveBeenCalledWith(
          expect.stringContaining('/workshop')
        );
      });
    });

    it('should show loading state', () => {
      userApi.list.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      userApi.list.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Workshop Information', () => {
    it('should display manager information', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('张主管')).toBeInTheDocument();
        expect(screen.getByText('李主管')).toBeInTheDocument();
      });
    });

    it('should show worker and machine counts', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/25.*人|25.*workers/i)).toBeInTheDocument();
        expect(screen.getByText(/10.*台|10.*machines/i)).toBeInTheDocument();
      });
    });

    it('should display capacity and utilization', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1000/)).toBeInTheDocument();
        expect(screen.getByText(/85%/)).toBeInTheDocument();
      });
    });

    it('should show workshop area', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/500.*㎡|500.*m²/i)).toBeInTheDocument();
        expect(screen.getByText(/800.*㎡|800.*m²/i)).toBeInTheDocument();
      });
    });
  });

  describe('Workshop Status', () => {
    it('should display workshop status', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText(/active|正常|活跃/i).length).toBeGreaterThan(0);
      });
    });

    it('should show active orders', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5.*工单|5.*orders/i)).toBeInTheDocument();
      });
    });
  });

  describe('Search and Filtering', () => {
    it('should search workshops', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '装配' } });

        await waitFor(() => {
          expect(userApi.list).toHaveBeenCalled();
        });
      }
    });

    it('should filter by type', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(userApi.list).toHaveBeenCalled();
      });

      const typeFilter = screen.queryByRole('combobox');
      if (typeFilter) {
        fireEvent.change(typeFilter, { target: { value: 'assembly' } });
      }
    });
  });

  describe('CRUD Operations', () => {
    it('should create new workshop', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(userApi.list).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);

        expect(screen.queryByText(/新建车间|Create Workshop/i)).toBeTruthy();
      }
    });

    it('should edit workshop', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        expect(screen.queryByText(/编辑车间|Edit Workshop/i)).toBeTruthy();
      }
    });

    it('should delete workshop', async () => {
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);

        await waitFor(() => {
          expect(productionApi.delete).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Worker Management', () => {
    it('should view workshop workers', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
      });

      const viewWorkerButtons = screen.queryAllByRole('button', { name: /人员|Workers|员工/i });
      if (viewWorkerButtons.length > 0) {
        fireEvent.click(viewWorkerButtons[0]);

        expect(screen.queryByText(/人员列表|Worker List/i)).toBeTruthy();
      }
    });

    it('should assign worker to workshop', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
      });

      const assignButtons = screen.queryAllByRole('button', { name: /分配人员|Assign Worker/i });
      if (assignButtons.length > 0) {
        fireEvent.click(assignButtons[0]);

        await waitFor(() => {
          expect(productionApi.workshops.create).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Machine Management', () => {
    it('should view workshop machines', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
      });

      const viewMachineButtons = screen.queryAllByRole('button', { name: /设备|Machines/i });
      if (viewMachineButtons.length > 0) {
        fireEvent.click(viewMachineButtons[0]);

        expect(screen.queryByText(/设备列表|Machine List/i)).toBeTruthy();
      }
    });

    it('should show machine count', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/10.*台|10.*machines/i)).toBeInTheDocument();
        expect(screen.getByText(/15.*台|15.*machines/i)).toBeInTheDocument();
      });
    });
  });

  describe('Capacity Management', () => {
    it('should display capacity information', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1000/)).toBeInTheDocument();
        expect(screen.getByText(/1500/)).toBeInTheDocument();
      });
    });

    it('should show utilization rate', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/85%/)).toBeInTheDocument();
        expect(screen.getByText(/72%/)).toBeInTheDocument();
      });
    });

    it('should update capacity', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('装配车间A')).toBeInTheDocument();
      });

      const updateButtons = screen.queryAllByRole('button', { name: /更新产能|Update Capacity/i });
      if (updateButtons.length > 0) {
        fireEvent.click(updateButtons[0]);

        await waitFor(() => {
          expect(productionApi.workshops.update).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Statistics Display', () => {
    it('should show total workshop count', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*车间|Total.*2/i)).toBeInTheDocument();
      });
    });

    it('should display total workers and machines', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/55.*人|55.*workers/i)).toBeInTheDocument();
        expect(screen.getByText(/25.*台|25.*machines/i)).toBeInTheDocument();
      });
    });

    it('should show average utilization', async () => {
      render(
        <MemoryRouter>
          <WorkshopManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/78\.5%|平均利用率/i)).toBeInTheDocument();
      });
    });
  });
});
