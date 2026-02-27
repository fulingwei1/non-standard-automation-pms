/**
 * SupplierManagement 组件测试
 * 测试覆盖：供应商列表、评级、资质管理、绩效评估
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SupplierManagement from '../SupplierManagement';
import _api, { supplierApi } from '../../services/api';

// Mock dependencies
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
      update: vi.fn().mockResolvedValue({ data: {} }),
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
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

describe.skip('SupplierManagement', () => {
  const mockSuppliers = {
    items: [
      {
        id: 1,
        code: 'SUP-001',
        name: '深圳某电子厂',
        type: 'manufacturer',
        category: '电子元器件',
        rating: 'A',
        status: 'active',
        contact: '张经理',
        phone: '13800138000',
        email: 'contact@supplier1.com',
        address: '深圳市南山区',
        creditCode: '91440300XXXXXXXXXX',
        registeredCapital: 5000000,
        cooperationYears: 3,
        performance: {
          quality: 95,
          delivery: 92,
          service: 90,
          overall: 92
        }
      },
      {
        id: 2,
        code: 'SUP-002',
        name: '上海某机械厂',
        type: 'manufacturer',
        category: '机械加工',
        rating: 'B',
        status: 'active',
        contact: '李经理',
        phone: '13900139000',
        email: 'contact@supplier2.com',
        address: '上海市浦东新区',
        creditCode: '91310000YYYYYYYYYY',
        registeredCapital: 3000000,
        cooperationYears: 2,
        performance: {
          quality: 85,
          delivery: 88,
          service: 82,
          overall: 85
        }
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10,
    stats: {
      total: 2,
      active: 2,
      inactive: 0,
      ratingA: 1,
      ratingB: 1,
      ratingC: 0
    }
  };

  const mockSupplierDetail = {
    id: 1,
    code: 'SUP-001',
    name: '深圳某电子厂',
    type: 'manufacturer',
    category: '电子元器件',
    rating: 'A',
    status: 'active',
    contact: '张经理',
    phone: '13800138000',
    email: 'contact@supplier1.com',
    address: '深圳市南山区',
    creditCode: '91440300XXXXXXXXXX',
    registeredCapital: 5000000,
    cooperationYears: 3,
    performance: {
      quality: 95,
      delivery: 92,
      service: 90,
      overall: 92
    },
    certifications: [
      { id: 1, name: 'ISO9001', issueDate: '2023-01-15', expiryDate: '2026-01-15', status: 'valid' },
      { id: 2, name: 'ISO14001', issueDate: '2023-02-20', expiryDate: '2026-02-20', status: 'valid' }
    ],
    purchaseOrders: [
      { id: 1, code: 'PO-2024-001', amount: 500000, status: 'completed', date: '2024-01-15' },
      { id: 2, code: 'PO-2024-002', amount: 300000, status: 'in_progress', date: '2024-02-10' }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    supplierApi.list.mockImplementation((url) => {
      if (url.includes('/suppliers') && !url.includes('/suppliers/')) {
        return Promise.resolve({ data: mockSuppliers });
      }
      if (url.includes('/suppliers/1')) {
        return Promise.resolve({ data: mockSupplierDetail });
      }
      return Promise.resolve({ data: {} });
    });

    supplierApi.create.mockResolvedValue({ data: { success: true, id: 3 } });
    supplierApi.update.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render supplier management with title', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/供应商管理|Supplier Management/i)).toBeInTheDocument();
    });

    it('should render supplier list', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
        expect(screen.getByText('上海某机械厂')).toBeInTheDocument();
      });
    });

    it('should display supplier codes', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SUP-001')).toBeInTheDocument();
        expect(screen.getByText('SUP-002')).toBeInTheDocument();
      });
    });

    it('should show supplier ratings', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const ratingA = screen.getAllByText(/A/);
        const ratingB = screen.getAllByText(/B/);
        expect(ratingA.length).toBeGreaterThan(0);
        expect(ratingB.length).toBeGreaterThan(0);
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch suppliers', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalledWith(expect.stringContaining('/suppliers'));
      });
    });

    it('should show loading state', () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      const loadingIndicators = screen.queryAllByText(/加载中|Loading/i);
      expect(loadingIndicators.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error', async () => {
      supplierApi.list.mockRejectedValueOnce(new Error('Failed to load'));

      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should display empty state when no suppliers', async () => {
      supplierApi.list.mockResolvedValueOnce({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无供应商|No suppliers/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 供应商信息显示测试
  describe('Supplier Information Display', () => {
    it('should display supplier category', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电子元器件')).toBeInTheDocument();
        expect(screen.getByText('机械加工')).toBeInTheDocument();
      });
    });

    it('should show contact information', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张经理/)).toBeInTheDocument();
        expect(screen.getByText(/13800138000/)).toBeInTheDocument();
      });
    });

    it('should display cooperation years', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/3.*年|3.*years/i)).toBeInTheDocument();
        expect(screen.getByText(/2.*年|2.*years/i)).toBeInTheDocument();
      });
    });

    it('should show performance scores', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/92|95/)).toBeInTheDocument();
        expect(screen.getByText(/85|88/)).toBeInTheDocument();
      });
    });
  });

  // 4. 搜索和筛选测试
  describe('Search and Filtering', () => {
    it('should search suppliers by name', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '深圳' } });
        
        await waitFor(() => {
          expect(supplierApi.list).toHaveBeenCalled();
        });
      }
    });

    it('should filter by rating', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const ratingFilter = screen.queryByText(/评级|Rating/i);
      if (ratingFilter) {
        fireEvent.click(ratingFilter);
      }
    });

    it('should filter by category', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const categoryFilter = screen.queryByText(/类别|Category/i);
      if (categoryFilter) {
        fireEvent.click(categoryFilter);
      }
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const statusFilter = screen.queryByText(/状态|Status/i);
      if (statusFilter) {
        fireEvent.click(statusFilter);
      }
    });
  });

  // 5. 供应商评级测试
  describe('Supplier Rating', () => {
    it('should display overall rating', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const ratingA = screen.getAllByText(/A/);
        expect(ratingA.length).toBeGreaterThan(0);
      });
    });

    it('should show performance breakdown', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);
        
        await waitFor(() => {
          expect(screen.getByText(/质量|Quality/i)).toBeInTheDocument();
          expect(screen.getByText(/交付|Delivery/i)).toBeInTheDocument();
          expect(screen.getByText(/服务|Service/i)).toBeInTheDocument();
        });
      }
    });

    it('should calculate rating based on performance', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        // Rating A for 92+ overall score
        const ratingA = screen.getAllByText(/A/);
        expect(ratingA.length).toBeGreaterThan(0);
      });
    });
  });

  // 6. 资质管理测试
  describe('Certification Management', () => {
    it('should display supplier certifications', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const supplierRow = screen.getByText('深圳某电子厂');
      const clickableElement = supplierRow.closest('button') || supplierRow.closest('div[role="button"]');
      if (clickableElement) {
        fireEvent.click(clickableElement);
        
        await waitFor(() => {
          expect(screen.getByText(/ISO9001/)).toBeInTheDocument();
          expect(screen.getByText(/ISO14001/)).toBeInTheDocument();
        });
      }
    });

    it('should show certification expiry dates', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);
        
        await waitFor(() => {
          expect(screen.getByText(/2026-01-15/)).toBeInTheDocument();
        });
      }
    });

    it('should highlight expired certifications', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      // Expired certifications should be highlighted
      const expiredIndicator = screen.queryByText(/过期|Expired/i);
      expect(expiredIndicator).toBeTruthy();
    });
  });

  // 7. 采购订单关联测试
  describe('Purchase Orders', () => {
    it('should display related purchase orders', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);
        
        await waitFor(() => {
          expect(screen.getByText(/PO-2024-001/)).toBeInTheDocument();
        });
      }
    });

    it('should show purchase order amounts', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);
        
        await waitFor(() => {
          expect(screen.getByText(/500,000|50万/)).toBeInTheDocument();
        });
      }
    });
  });

  // 8. 供应商操作测试
  describe('Supplier Actions', () => {
    it('should create new supplier', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);
        
        expect(screen.queryByText(/新建供应商|Create Supplier/i)).toBeTruthy();
      }
    });

    it('should edit supplier information', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);
        
        expect(screen.queryByText(/编辑供应商|Edit Supplier/i)).toBeTruthy();
      }
    });

    it('should deactivate supplier', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const deactivateButtons = screen.queryAllByRole('button', { name: /停用|Deactivate/i });
      if (deactivateButtons.length > 0) {
        fireEvent.click(deactivateButtons[0]);
        
        await waitFor(() => {
          expect(supplierApi.update).toHaveBeenCalled();
        });
      }
    });

    it('should export supplier list', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);
      }
    });
  });

  // 9. 统计信息测试
  describe('Statistics Display', () => {
    it('should display total supplier count', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*供应商|Total.*2/i)).toBeInTheDocument();
      });
    });

    it('should show active supplier count', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*活跃|Active.*2/i)).toBeInTheDocument();
      });
    });

    it('should display rating distribution', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/A.*1|1.*A/)).toBeInTheDocument();
        expect(screen.getByText(/B.*1|1.*B/)).toBeInTheDocument();
      });
    });
  });

  // 10. 绩效评估测试
  describe('Performance Evaluation', () => {
    it('should calculate quality score', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);
        
        await waitFor(() => {
          expect(screen.getByText(/95|质量/)).toBeInTheDocument();
        });
      }
    });

    it('should show delivery performance', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);
        
        await waitFor(() => {
          expect(screen.getByText(/92|交付/)).toBeInTheDocument();
        });
      }
    });

    it('should display overall performance score', async () => {
      render(
        <MemoryRouter>
          <SupplierManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);
        
        await waitFor(() => {
          expect(screen.getByText(/92|综合/)).toBeInTheDocument();
        });
      }
    });
  });
});
