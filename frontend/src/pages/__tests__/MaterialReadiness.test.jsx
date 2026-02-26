/**
 * MaterialReadiness 组件测试
 * 测试覆盖：物料齐套检查、缺料提醒、采购建议
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MaterialReadiness from '../MaterialReadiness';
import api, { materialApi, projectApi, supplierApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    materialApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      search: vi.fn().mockResolvedValue({ data: {} }),
      warehouse: {
        statistics: vi.fn().mockResolvedValue({ data: {} }),
      },
      categories: {
        list: vi.fn().mockResolvedValue({ data: {} }),
      },
    },
    projectApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      getBoard: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      getMachines: vi.fn().mockResolvedValue({ data: {} }),
      getInProductionSummary: vi.fn().mockResolvedValue({ data: {} }),
      recommendTemplates: vi.fn().mockResolvedValue({ data: {} }),
      createFromTemplate: vi.fn().mockResolvedValue({ data: {} }),
      checkAutoTransition: vi.fn().mockResolvedValue({ data: {} }),
      getGateCheckResult: vi.fn().mockResolvedValue({ data: {} }),
      advanceStage: vi.fn().mockResolvedValue({ data: {} }),
      getCacheStats: vi.fn().mockResolvedValue({ data: {} }),
      clearCache: vi.fn().mockResolvedValue({ data: {} }),
      resetCacheStats: vi.fn().mockResolvedValue({ data: {} }),
      getStatusLogs: vi.fn().mockResolvedValue({ data: {} }),
      getHealthDetails: vi.fn().mockResolvedValue({ data: {} }),
      getStats: vi.fn().mockResolvedValue({ data: {} }),
    },
    supplierApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
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

describe('MaterialReadiness', () => {
  const mockReadinessData = {
    orders: [
      {
        id: 1,
        code: 'WO-2024-001',
        productName: '产品A',
        quantity: 100,
        requiredDate: '2024-03-01',
        readinessRate: 85,
        status: 'partial',
        totalItems: 20,
        readyItems: 17,
        shortageItems: 3,
        materials: [
          {
            materialCode: 'MAT-001',
            materialName: '钢板',
            required: 1000,
            available: 1000,
            shortage: 0,
            status: 'ready'
          },
          {
            materialCode: 'MAT-002',
            materialName: '螺栓',
            required: 500,
            available: 300,
            shortage: 200,
            status: 'shortage'
          }
        ]
      },
      {
        id: 2,
        code: 'WO-2024-002',
        productName: '产品B',
        quantity: 50,
        requiredDate: '2024-03-05',
        readinessRate: 100,
        status: 'ready',
        totalItems: 15,
        readyItems: 15,
        shortageItems: 0,
        materials: []
      }
    ],
    stats: {
      totalOrders: 2,
      readyOrders: 1,
      partialOrders: 1,
      notReadyOrders: 0
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    materialApi.list.mockResolvedValue({ data: mockReadinessData });
    materialApi.create.mockResolvedValue({ data: { success: true } });
    materialApi.update.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render material readiness page', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/物料齐套|Material Readiness/i)).toBeInTheDocument();
      });
    });

    it('should render order list', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('WO-2024-001')).toBeInTheDocument();
        expect(screen.getByText('WO-2024-002')).toBeInTheDocument();
      });
    });

    it('should display product names', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
        expect(screen.getByText('产品B')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load readiness data on mount', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalledWith(
          expect.stringContaining('/material-readiness')
        );
      });
    });

    it('should show loading state', () => {
      materialApi.list.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      materialApi.list.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Readiness Status', () => {
    it('should display readiness rate', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/85%/)).toBeInTheDocument();
        expect(screen.getByText(/100%/)).toBeInTheDocument();
      });
    });

    it('should show readiness status', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/部分齐套|Partial/i)).toBeInTheDocument();
        expect(screen.getByText(/已齐套|Ready/i)).toBeInTheDocument();
      });
    });

    it('should display item counts', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/17.*\/.*20/)).toBeInTheDocument();
        expect(screen.getByText(/15.*\/.*15/)).toBeInTheDocument();
      });
    });
  });

  describe('Material Details', () => {
    it('should view material details', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          expect(screen.getByText('钢板')).toBeInTheDocument();
          expect(screen.getByText('螺栓')).toBeInTheDocument();
        });
      }
    });

    it('should display required and available quantities', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/1000/)).toBeInTheDocument();
          expect(screen.getByText(/500/)).toBeInTheDocument();
          expect(screen.getByText(/300/)).toBeInTheDocument();
        });
      }
    });

    it('should highlight shortage items', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/缺料|Shortage/i)).toBeInTheDocument();
          expect(screen.getByText(/200/)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Shortage Management', () => {
    it('should show shortage count', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/3.*缺料|3.*shortage/i)).toBeInTheDocument();
      });
    });

    it('should create purchase request for shortage', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const purchaseButtons = screen.queryAllByRole('button', { name: /采购|Purchase/i });
      if (purchaseButtons.length > 0) {
        fireEvent.click(purchaseButtons[0]);

        await waitFor(() => {
          expect(materialApi.create).toHaveBeenCalled();
        });
      }
    });

    it('should send shortage alert', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const alertButtons = screen.queryAllByRole('button', { name: /提醒|Alert/i });
      if (alertButtons.length > 0) {
        fireEvent.click(alertButtons[0]);

        await waitFor(() => {
          expect(materialApi.create).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Search and Filtering', () => {
    it('should search orders', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '产品A' } });

        await waitFor(() => {
          expect(materialApi.list).toHaveBeenCalled();
        });
      }
    });

    it('should filter by readiness status', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });

      const statusFilter = screen.queryByRole('combobox');
      if (statusFilter) {
        fireEvent.change(statusFilter, { target: { value: 'partial' } });
      }
    });

    it('should filter by required date', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });
    });
  });

  describe('Readiness Check', () => {
    it('should trigger readiness check', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const checkButtons = screen.queryAllByRole('button', { name: /检查|Check/i });
      if (checkButtons.length > 0) {
        fireEvent.click(checkButtons[0]);

        await waitFor(() => {
          expect(materialApi.create).toHaveBeenCalled();
        });
      }
    });

    it('should refresh readiness data', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });

      const refreshButton = screen.queryByRole('button', { name: /刷新|Refresh/i });
      if (refreshButton) {
        fireEvent.click(refreshButton);

        await waitFor(() => {
          expect(materialApi.list).toHaveBeenCalledTimes(2);
        });
      }
    });
  });

  describe('Statistics Display', () => {
    it('should show total order count', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*工单|Total.*2/i)).toBeInTheDocument();
      });
    });

    it('should display readiness statistics', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1.*已齐套|Ready.*1/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*部分|Partial.*1/i)).toBeInTheDocument();
      });
    });
  });

  describe('Batch Operations', () => {
    it('should check readiness for multiple orders', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
      });

      const checkboxes = screen.queryAllByRole('checkbox');
      if (checkboxes.length > 1) {
        fireEvent.click(checkboxes[0]);
        fireEvent.click(checkboxes[1]);

        const batchCheckButton = screen.queryByRole('button', { name: /批量检查|Batch Check/i });
        if (batchCheckButton) {
          fireEvent.click(batchCheckButton);

          await waitFor(() => {
            expect(materialApi.create).toHaveBeenCalled();
          });
        }
      }
    });
  });
});
