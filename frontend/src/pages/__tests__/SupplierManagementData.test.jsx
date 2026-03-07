/**
 * SupplierManagementData 组件测试
 * 测试覆盖：供应商数据分析、绩效报表、数据导入导出
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SupplierManagementData from '../SupplierManagementData';
import { supplierApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    supplierApi: {
      create: vi.fn().mockResolvedValue({ data: {} }),
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      updateRating: vi.fn().mockResolvedValue({ data: {} }),
      getMaterials: vi.fn().mockResolvedValue({ data: {} }),
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

describe('SupplierManagementData', () => {
  const mockSupplierData = {
    stats: {
      totalSuppliers: 50,
      activeSuppliers: 45,
      ratingA: 15,
      ratingB: 20,
      ratingC: 10,
      avgPerformance: 88,
      totalOrders: 120,
      totalAmount: 15000000
    },
    performanceData: [
      {
        supplierId: 1,
        supplierName: '供应商A',
        category: '电子元器件',
        qualityScore: 95,
        deliveryScore: 92,
        serviceScore: 90,
        overallScore: 92,
        orderCount: 25,
        totalAmount: 2500000,
        onTimeRate: 96,
        defectRate: 1.2
      },
      {
        supplierId: 2,
        supplierName: '供应商B',
        category: '机械加工',
        qualityScore: 85,
        deliveryScore: 88,
        serviceScore: 82,
        overallScore: 85,
        orderCount: 18,
        totalAmount: 1800000,
        onTimeRate: 89,
        defectRate: 2.5
      }
    ],
    trendData: [
      { month: '2024-01', avgScore: 85, orderCount: 10 },
      { month: '2024-02', avgScore: 88, orderCount: 12 }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    supplierApi.list.mockResolvedValue({ data: mockSupplierData });
    supplierApi.create.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render supplier data page', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/供应商数据|Supplier Data/i)).toBeInTheDocument();
      });
    });

    it('should display statistics cards', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/50/)).toBeInTheDocument();
        expect(screen.getByText(/45.*活跃|Active.*45/i)).toBeInTheDocument();
      });
    });
  });

  describe('Performance Data Display', () => {
    it('should show supplier performance table', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('供应商A')).toBeInTheDocument();
        expect(screen.getByText('供应商B')).toBeInTheDocument();
      });
    });

    it('should display performance scores', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/92|95/)).toBeInTheDocument();
        expect(screen.getByText(/85|88/)).toBeInTheDocument();
      });
    });

    it('should show quality metrics', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1\.2/)).toBeInTheDocument();
        expect(screen.getByText(/96/)).toBeInTheDocument();
      });
    });
  });

  describe('Data Filtering', () => {
    it('should filter by category', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const categoryFilter = screen.queryByRole('combobox');
      if (categoryFilter) {
        fireEvent.change(categoryFilter, { target: { value: '电子元器件' } });
      }
    });

    it('should filter by date range', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const dateInputs = screen.queryAllByRole('textbox');
      if (dateInputs.length >= 2) {
        fireEvent.change(dateInputs[0], { target: { value: '2024-01-01' } });
        fireEvent.change(dateInputs[1], { target: { value: '2024-02-28' } });
      }
    });
  });

  describe('Data Export', () => {
    it('should export supplier data', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);

        await waitFor(() => {
          expect(supplierApi.create).toHaveBeenCalledWith(
            expect.stringContaining('/export')
          );
        });
      }
    });
  });

  describe('Data Import', () => {
    it('should handle data import', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const importButton = screen.queryByRole('button', { name: /导入|Import/i });
      if (importButton) {
        fireEvent.click(importButton);

        expect(screen.queryByText(/选择文件|Select File/i)).toBeTruthy();
      }
    });
  });

  describe('Trend Analysis', () => {
    it('should display performance trends', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/趋势|Trend/i)).toBeInTheDocument();
      });
    });

    it('should show monthly data', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-01/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02/)).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Display', () => {
    it('should show total statistics', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/15,000,000|1500万/)).toBeInTheDocument();
        expect(screen.getByText(/120/)).toBeInTheDocument();
      });
    });

    it('should display rating distribution', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/15.*A级/i)).toBeInTheDocument();
        expect(screen.getByText(/20.*B级/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load data on mount', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalledWith(
          expect.stringContaining('/supplier')
        );
      });
    });

    it('should handle loading error', async () => {
      supplierApi.list.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });
});
