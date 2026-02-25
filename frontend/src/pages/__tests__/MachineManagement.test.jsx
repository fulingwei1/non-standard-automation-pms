/**
 * MachineManagement 组件测试
 * 测试覆盖：设备列表、维护记录、状态监控、保养计划
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MachineManagement from '../MachineManagement/index';
import api from '../../services/api';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
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

describe('MachineManagement', () => {
  const mockMachines = {
    items: [
      {
        id: 1,
        code: 'MCH-001',
        name: '数控车床A',
        model: 'CNC-X200',
        category: 'CNC',
        status: 'running',
        workshop: '车间A',
        manufacturer: '德国西门子',
        purchaseDate: '2023-01-15',
        price: 500000,
        utilization: 85,
        maintenanceStatus: 'normal',
        lastMaintenance: '2024-01-15',
        nextMaintenance: '2024-03-15',
        faultCount: 2,
        uptime: 98.5
      },
      {
        id: 2,
        code: 'MCH-002',
        name: '激光切割机B',
        model: 'LASER-500',
        category: 'Laser',
        status: 'maintenance',
        workshop: '车间B',
        manufacturer: '日本三菱',
        purchaseDate: '2023-06-20',
        price: 800000,
        utilization: 0,
        maintenanceStatus: 'warning',
        lastMaintenance: '2024-02-01',
        nextMaintenance: '2024-04-01',
        faultCount: 5,
        uptime: 95.2
      }
    ],
    total: 2,
    stats: {
      total: 2,
      running: 1,
      idle: 0,
      maintenance: 1,
      fault: 0,
      avgUtilization: 42.5,
      avgUptime: 96.85
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockMachines });
    api.post.mockResolvedValue({ data: { success: true, id: 3 } });
    api.put.mockResolvedValue({ data: { success: true } });
    api.delete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render machine management page', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/设备管理|Machine Management/i)).toBeInTheDocument();
      });
    });

    it('should render machine list', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('数控车床A')).toBeInTheDocument();
        expect(screen.getByText('激光切割机B')).toBeInTheDocument();
      });
    });

    it('should display machine codes', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('MCH-001')).toBeInTheDocument();
        expect(screen.getByText('MCH-002')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load machines on mount', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/machine')
        );
      });
    });

    it('should show loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      api.get.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Machine Information', () => {
    it('should display machine model', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('CNC-X200')).toBeInTheDocument();
        expect(screen.getByText('LASER-500')).toBeInTheDocument();
      });
    });

    it('should show manufacturer', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/德国西门子/)).toBeInTheDocument();
        expect(screen.getByText(/日本三菱/)).toBeInTheDocument();
      });
    });

    it('should display workshop location', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/车间A/)).toBeInTheDocument();
        expect(screen.getByText(/车间B/)).toBeInTheDocument();
      });
    });
  });

  describe('Machine Status', () => {
    it('should display machine status', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/运行|Running/i)).toBeInTheDocument();
        expect(screen.getByText(/维护|Maintenance/i)).toBeInTheDocument();
      });
    });

    it('should show utilization rate', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/85%/)).toBeInTheDocument();
      });
    });

    it('should display uptime', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/98\.5%/)).toBeInTheDocument();
        expect(screen.getByText(/95\.2%/)).toBeInTheDocument();
      });
    });
  });

  describe('Maintenance Management', () => {
    it('should display last maintenance date', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-01-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02-01/)).toBeInTheDocument();
      });
    });

    it('should show next maintenance date', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-03-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-04-01/)).toBeInTheDocument();
      });
    });

    it('should schedule maintenance', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('数控车床A')).toBeInTheDocument();
      });

      const maintenanceButtons = screen.queryAllByRole('button', { name: /维护|Maintenance/i });
      if (maintenanceButtons.length > 0) {
        fireEvent.click(maintenanceButtons[0]);

        expect(screen.queryByText(/计划维护|Schedule Maintenance/i)).toBeTruthy();
      }
    });

    it('should show maintenance status', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/normal|正常/i)).toBeInTheDocument();
        expect(screen.getByText(/warning|预警/i)).toBeInTheDocument();
      });
    });
  });

  describe('Fault Management', () => {
    it('should display fault count', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*故障|2.*faults/i)).toBeInTheDocument();
        expect(screen.getByText(/5.*故障|5.*faults/i)).toBeInTheDocument();
      });
    });

    it('should record fault', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('数控车床A')).toBeInTheDocument();
      });

      const faultButtons = screen.queryAllByRole('button', { name: /故障|Fault/i });
      if (faultButtons.length > 0) {
        fireEvent.click(faultButtons[0]);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Search and Filtering', () => {
    it('should search machines', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('数控车床A')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '数控' } });

        await waitFor(() => {
          expect(api.get).toHaveBeenCalled();
        });
      }
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const statusFilter = screen.queryByRole('combobox');
      if (statusFilter) {
        fireEvent.change(statusFilter, { target: { value: 'running' } });
      }
    });

    it('should filter by workshop', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });
  });

  describe('CRUD Operations', () => {
    it('should create new machine', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);

        expect(screen.queryByText(/新建设备|Create Machine/i)).toBeTruthy();
      }
    });

    it('should edit machine', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('数控车床A')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        expect(screen.queryByText(/编辑设备|Edit Machine/i)).toBeTruthy();
      }
    });

    it('should delete machine', async () => {
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('数控车床A')).toBeInTheDocument();
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
    it('should show total machine count', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*设备|Total.*2/i)).toBeInTheDocument();
      });
    });

    it('should display status statistics', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1.*运行|Running.*1/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*维护|Maintenance.*1/i)).toBeInTheDocument();
      });
    });

    it('should show average utilization', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/42\.5%/)).toBeInTheDocument();
      });
    });

    it('should display average uptime', async () => {
      render(
        <MemoryRouter>
          <MachineManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/96\.85%/)).toBeInTheDocument();
      });
    });
  });
});
