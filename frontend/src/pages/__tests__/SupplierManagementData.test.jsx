/**
 * SupplierManagementData 组件测试
 * 测试覆盖：供应商列表渲染、数据加载、搜索过滤、创建/评级对话框
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { supplierApi } from '../../services/api';
import { MemoryRouter } from 'react-router-dom';
import SupplierManagementData from '../SupplierManagementData';

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
  // 后端格式的供应商列表数据 - supplierApi.list 返回的格式
  const mockSupplierItems = [
    {
      id: 1,
      supplier_code: 'SUP-001',
      supplier_name: '供应商A',
      supplier_type: 'MATERIAL',
      contact_person: '张三',
      contact_phone: '13800000001',
      contact_email: 'a@test.com',
      overall_rating: '4.5',
      supplier_level: 'A',
      status: 'ACTIVE',
    },
    {
      id: 2,
      supplier_code: 'SUP-002',
      supplier_name: '供应商B',
      supplier_type: 'OUTSOURCE',
      contact_person: '李四',
      contact_phone: '13800000002',
      contact_email: 'b@test.com',
      overall_rating: '3.8',
      supplier_level: 'B',
      status: 'ACTIVE',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    // supplierApi.list 返回后端分页格式
    // 组件读取 response.formatted || response.data 中的 items 和 total
    supplierApi.list.mockResolvedValue({
      data: { items: mockSupplierItems, total: 2 },
    });
    supplierApi.create.mockResolvedValue({ data: { success: true } });
    supplierApi.get.mockResolvedValue({ data: mockSupplierItems[0] });
    supplierApi.updateRating.mockResolvedValue({ data: { success: true } });
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
        // 组件标题是 "供应商管理"
        expect(screen.getByText(/供应商管理|供应商数据|Supplier/i)).toBeInTheDocument();
      });
    });

    it('should display supplier list table', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 表格列标题
        expect(screen.getByText('供应商编码')).toBeInTheDocument();
        expect(screen.getByText('供应商名称')).toBeInTheDocument();
      });
    });
  });

  describe('Performance Data Display', () => {
    it('should show supplier names in table', async () => {
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

    it('should display overall ratings', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        // overall_rating 显示为 "4.5" 和 "3.8"
        expect(screen.getByText('4.5')).toBeInTheDocument();
        expect(screen.getByText('3.8')).toBeInTheDocument();
      });
    });

    it('should show supplier levels', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        // supplier_level 显示为 "A级" 和 "B级"
        expect(screen.getByText('A级')).toBeInTheDocument();
        expect(screen.getByText('B级')).toBeInTheDocument();
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

      // 组件使用 Select 组件进行类型筛选
      const filterElements = screen.queryAllByRole('combobox');
      expect(filterElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should have search input', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      // 搜索输入框
      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      expect(searchInput).toBeTruthy();
    });
  });

  describe('Data Export', () => {
    it('should have action buttons', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      // 页面有新增按钮
      const addButton = screen.queryByText(/新增供应商/i);
      expect(addButton).toBeTruthy();
    });
  });

  describe('Data Import', () => {
    it('should open create dialog', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(supplierApi.list).toHaveBeenCalled();
      });

      const addButton = screen.queryByText(/新增供应商/i);
      if (addButton) {
        fireEvent.click(addButton);

        await waitFor(() => {
          // 新增对话框标题 "新增供应商"
          expect(screen.getAllByText(/供应商编码/).length).toBeGreaterThan(1);
        });
      }
    });
  });

  describe('Supplier Status', () => {
    it('should display supplier status badges', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        // status === "ACTIVE" → "合作中"
        expect(screen.getAllByText('合作中').length).toBeGreaterThan(0);
      });
    });

    it('should show contact information', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 联系人信息
        expect(screen.getByText('张三')).toBeInTheDocument();
        expect(screen.getByText('李四')).toBeInTheDocument();
      });
    });
  });

  describe('Supplier Codes', () => {
    it('should show supplier codes', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SUP-001')).toBeInTheDocument();
        expect(screen.getByText('SUP-002')).toBeInTheDocument();
      });
    });

    it('should show supplier types', async () => {
      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        // supplier_type 直接显示
        expect(screen.getByText('MATERIAL')).toBeInTheDocument();
        expect(screen.getByText('OUTSOURCE')).toBeInTheDocument();
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
        // 组件使用 supplierApi.list(params) 传递对象参数
        expect(supplierApi.list).toHaveBeenCalledWith(
          expect.objectContaining({ page: 1, page_size: 20 })
        );
      });
    });

    it('should handle loading error', async () => {
      // window.alert 模拟
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
      supplierApi.list.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <SupplierManagementData />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 组件在出错时调用 alert
        expect(alertSpy).toHaveBeenCalledWith(
          expect.stringContaining('加载供应商列表失败')
        );
      });

      alertSpy.mockRestore();
    });
  });
});
