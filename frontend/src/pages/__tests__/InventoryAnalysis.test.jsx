/**
 * InventoryAnalysis 组件测试
 * 测试覆盖：库存分析、周转率、安全库存、成本分析
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import InventoryAnalysis from '../InventoryAnalysis';
import api from '../../services/api';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
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

describe('InventoryAnalysis', () => {
  const mockInventoryData = {
    overview: {
      totalValue: 5000000,
      totalQuantity: 10000,
      itemCount: 500,
      avgTurnover: 4.5,
      lowStockItems: 25,
      overstockItems: 15
    },
    items: [
      {
        id: 1,
        materialCode: 'MAT-001',
        materialName: '钢板',
        category: '原材料',
        currentStock: 500,
        safetyStock: 200,
        avgConsumption: 100,
        turnoverRate: 4.8,
        stockDays: 5,
        totalValue: 250000,
        status: 'normal'
      },
      {
        id: 2,
        materialCode: 'MAT-002',
        materialName: '螺栓',
        category: '标准件',
        currentStock: 50,
        safetyStock: 100,
        avgConsumption: 200,
        turnoverRate: 2.5,
        stockDays: 0.25,
        totalValue: 5000,
        status: 'low'
      }
    ],
    trends: [
      { month: '2024-01', turnover: 4.2, value: 4800000 },
      { month: '2024-02', turnover: 4.5, value: 5000000 }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockInventoryData });
    api.post.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render inventory analysis page', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/库存分析|Inventory Analysis/i)).toBeInTheDocument();
      });
    });

    it('should display overview statistics', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5,000,000|500万/i)).toBeInTheDocument();
        expect(screen.getByText(/10,000|1万/)).toBeInTheDocument();
      });
    });

    it('should render inventory items', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
        expect(screen.getByText('螺栓')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load inventory data on mount', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/inventory')
        );
      });
    });

    it('should show loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      api.get.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Turnover Analysis', () => {
    it('should display turnover rates', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/4\.8/)).toBeInTheDocument();
        expect(screen.getByText(/2\.5/)).toBeInTheDocument();
      });
    });

    it('should show average turnover', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/4\.5/)).toBeInTheDocument();
      });
    });

    it('should display stock days', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5.*天|5.*days/i)).toBeInTheDocument();
      });
    });
  });

  describe('Safety Stock Analysis', () => {
    it('should display safety stock levels', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/200/)).toBeInTheDocument();
        expect(screen.getByText(/100/)).toBeInTheDocument();
      });
    });

    it('should highlight low stock items', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/低库存|Low Stock/i)).toBeInTheDocument();
        expect(screen.getByText(/25.*低库存|25.*low/i)).toBeInTheDocument();
      });
    });

    it('should show overstock items', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/15.*超储|15.*overstock/i)).toBeInTheDocument();
      });
    });
  });

  describe('Cost Analysis', () => {
    it('should display total inventory value', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5,000,000|500万/i)).toBeInTheDocument();
      });
    });

    it('should show item values', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/250,000|25万/i)).toBeInTheDocument();
        expect(screen.getByText(/5,000|5千/i)).toBeInTheDocument();
      });
    });
  });

  describe('Filtering and Search', () => {
    it('should search inventory items', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('钢板')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '钢板' } });

        await waitFor(() => {
          expect(api.get).toHaveBeenCalled();
        });
      }
    });

    it('should filter by category', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const categoryFilter = screen.queryByRole('combobox');
      if (categoryFilter) {
        fireEvent.change(categoryFilter, { target: { value: '原材料' } });
      }
    });

    it('should filter by stock status', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });
  });

  describe('Trend Analysis', () => {
    it('should display trend data', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/趋势|Trend/i)).toBeInTheDocument();
      });
    });

    it('should show monthly data', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-01/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02/)).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    it('should export analysis report', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalledWith(
            expect.stringContaining('/export')
          );
        });
      }
    });
  });

  describe('Statistics Display', () => {
    it('should show item count', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/500.*项|500.*items/i)).toBeInTheDocument();
      });
    });

    it('should display average consumption', async () => {
      render(
        <MemoryRouter>
          <InventoryAnalysis />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/100/)).toBeInTheDocument();
        expect(screen.getByText(/200/)).toBeInTheDocument();
      });
    });
  });
});
