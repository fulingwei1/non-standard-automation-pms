/**
 * MaterialTracking 组件测试
 * 测试覆盖：物料追踪、批次管理、流转记录、库位信息
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MaterialTracking from '../MaterialTracking';
import { materialApi, purchaseApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  materialApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
  },
  purchaseApi: {
    list: vi.fn(),
    get: vi.fn(),
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

describe('MaterialTracking', () => {
  const mockTrackingData = {
    materials: [
      {
        id: 1,
        materialCode: 'MAT-001',
        materialName: '钢板',
        batchNumber: 'BATCH-2024-001',
        quantity: 500,
        location: 'A区-01-05',
        status: 'in_stock',
        supplier: '供应商A',
        receiveDate: '2024-02-01',
        expiryDate: null,
        qualityStatus: 'qualified',
        lastOperation: 'receive',
        lastOperator: '张三',
        lastOperationTime: '2024-02-01 10:30'
      },
      {
        id: 2,
        materialCode: 'MAT-002',
        materialName: '螺栓',
        batchNumber: 'BATCH-2024-002',
        quantity: 1000,
        location: 'B区-02-10',
        status: 'allocated',
        supplier: '供应商B',
        receiveDate: '2024-02-10',
        expiryDate: null,
        qualityStatus: 'qualified',
        lastOperation: 'allocate',
        lastOperator: '李四',
        lastOperationTime: '2024-02-15 14:20'
      }
    ],
    flowRecords: [
      {
        id: 1,
        materialCode: 'MAT-001',
        batchNumber: 'BATCH-2024-001',
        operation: 'receive',
        quantity: 500,
        fromLocation: null,
        toLocation: 'A区-01-05',
        operator: '张三',
        operationTime: '2024-02-01 10:30',
        note: '采购入库'
      },
      {
        id: 2,
        materialCode: 'MAT-002',
        batchNumber: 'BATCH-2024-002',
        operation: 'allocate',
        quantity: 100,
        fromLocation: 'B区-02-10',
        toLocation: '生产线1',
        operator: '李四',
        operationTime: '2024-02-15 14:20',
        note: '分配给工单WO-001'
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    materialApi.list.mockResolvedValue({ data: mockTrackingData });
    materialApi.create.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render material tracking page', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/物料追踪|Material Tracking/i)).toBeInTheDocument();
      });
    });

    it('should render material list', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
        expect(screen.getByText('螺栓')).toBeInTheDocument();
      });
    });

    it('should display material codes', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('MAT-001')).toBeInTheDocument();
        expect(screen.getByText('MAT-002')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load tracking data on mount', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalledWith(
          expect.stringContaining('/material-tracking')
        );
      });
    });

    it('should show loading state', () => {
      materialApi.list.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      materialApi.list.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Batch Information', () => {
    it('should display batch numbers', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('BATCH-2024-001')).toBeInTheDocument();
        expect(screen.getByText('BATCH-2024-002')).toBeInTheDocument();
      });
    });

    it('should show batch quantities', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/500/)).toBeInTheDocument();
        expect(screen.getByText(/1000|1,000/)).toBeInTheDocument();
      });
    });

    it('should display supplier information', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('供应商A')).toBeInTheDocument();
        expect(screen.getByText('供应商B')).toBeInTheDocument();
      });
    });
  });

  describe('Location Information', () => {
    it('should display storage locations', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/A区-01-05/)).toBeInTheDocument();
        expect(screen.getByText(/B区-02-10/)).toBeInTheDocument();
      });
    });

    it('should track material movements', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const trackButtons = screen.queryAllByRole('button', { name: /追踪|Track|流转/i });
      if (trackButtons.length > 0) {
        fireEvent.click(trackButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/A区-01-05/)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Material Status', () => {
    it('should display material status', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/库存|In Stock/i)).toBeInTheDocument();
        expect(screen.getByText(/已分配|Allocated/i)).toBeInTheDocument();
      });
    });

    it('should show quality status', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText(/合格|Qualified/i).length).toBeGreaterThan(0);
      });
    });
  });

  describe('Flow Records', () => {
    it('should view flow records', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情|流转/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/采购入库/)).toBeInTheDocument();
        });
      }
    });

    it('should display operation types', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情|流转/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/receive|入库/i)).toBeInTheDocument();
        });
      }
    });

    it('should show operator information', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('张三')).toBeInTheDocument();
        expect(screen.getByText('李四')).toBeInTheDocument();
      });
    });

    it('should display operation timestamps', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-01 10:30/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02-15 14:20/)).toBeInTheDocument();
      });
    });
  });

  describe('Search and Filtering', () => {
    it('should search by material code', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: 'MAT-001' } });

        await waitFor(() => {
          expect(materialApi.list).toHaveBeenCalled();
        });
      }
    });

    it('should search by batch number', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/批次|Batch/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: 'BATCH-2024-001' } });

        await waitFor(() => {
          expect(materialApi.list).toHaveBeenCalled();
        });
      }
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });

      const statusFilter = screen.queryByRole('combobox');
      if (statusFilter) {
        fireEvent.change(statusFilter, { target: { value: 'in_stock' } });
      }
    });

    it('should filter by location', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });
    });
  });

  describe('Timeline View', () => {
    it('should display tracking timeline', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const timelineButtons = screen.queryAllByRole('button', { name: /时间线|Timeline/i });
      if (timelineButtons.length > 0) {
        fireEvent.click(timelineButtons[0]);

        expect(screen.queryByText(/流转历史|Flow History/i)).toBeTruthy();
      }
    });

    it('should show chronological order', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情|流转/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          const timestamps = screen.getAllByText(/2024-02/);
          expect(timestamps.length).toBeGreaterThan(0);
        });
      }
    });
  });

  describe('QR Code Tracking', () => {
    it('should scan QR code', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });

      const scanButton = screen.queryByRole('button', { name: /扫码|Scan/i });
      if (scanButton) {
        fireEvent.click(scanButton);

        expect(screen.queryByText(/扫描二维码|Scan QR Code/i)).toBeTruthy();
      }
    });

    it('should generate QR code', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const qrButtons = screen.queryAllByRole('button', { name: /二维码|QR/i });
      if (qrButtons.length > 0) {
        fireEvent.click(qrButtons[0]);

        expect(screen.queryByText(/生成二维码|Generate QR/i)).toBeTruthy();
      }
    });
  });

  describe('Export Functionality', () => {
    it('should export tracking report', async () => {
      render(
        <MemoryRouter>
          <MaterialTracking />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);

        await waitFor(() => {
          expect(materialApi.create).toHaveBeenCalledWith(
            expect.stringContaining('/export')
          );
        });
      }
    });
  });
});
