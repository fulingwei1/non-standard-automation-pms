import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SupplierManagement from '../SupplierManagement';
import { supplierApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  supplierApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    get: vi.fn(),
    updateRating: vi.fn(),
    getMaterials: vi.fn(),
  },
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const validProps = [
        'initial',
        'animate',
        'exit',
        'variants',
        'transition',
        'whileHover',
        'whileTap',
        'whileInView',
        'layout',
        'layoutId',
        'drag',
        'dragConstraints',
        'onDragEnd',
      ];
      const filtered = props && Object.entries(props).length > 0
        ? Object.fromEntries(Object.entries(props).filter(([k]) => !validProps.includes(k)))
        : {};
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    },
  }),
  AnimatePresence: ({ children }) => children,
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useInView: () => true,
}));

describe('SupplierManagement', () => {
  const mockSuppliers = {
    items: [
      {
        id: 1,
        code: 'SUP-001',
        name: '深圳某电子厂',
        category: '电子元器件',
        rating: 'A',
        status: 'active',
        contact: '张经理',
        phone: '13800138000',
        email: 'contact@supplier1.com',
        address: '深圳市南山区',
        performance: {
          quality: 95,
          delivery: 92,
          service: 90,
          overall: 92,
        },
        cooperationYears: 3,
      },
      {
        id: 2,
        code: 'SUP-002',
        name: '上海某机械厂',
        category: '机械加工',
        rating: 'B',
        status: 'active',
        contact: '李经理',
        phone: '13900139000',
        email: 'contact@supplier2.com',
        address: '上海市浦东新区',
        performance: {
          quality: 85,
          delivery: 88,
          service: 82,
          overall: 85,
        },
        cooperationYears: 2,
      },
    ],
    total: 2,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    supplierApi.list.mockResolvedValue({ data: mockSuppliers });
    supplierApi.create.mockResolvedValue({ data: { success: true, id: 3 } });
  });

  it('renders title and fetches supplier list', async () => {
    render(
      <MemoryRouter>
        <SupplierManagement />
      </MemoryRouter>
    );

    expect(screen.getByText('供应商管理')).toBeInTheDocument();

    await waitFor(() => {
      expect(supplierApi.list).toHaveBeenCalled();
    });
  });

  it('renders normalized supplier info from current page implementation', async () => {
    render(
      <MemoryRouter>
        <SupplierManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('深圳某电子厂')).toBeInTheDocument();
      expect(screen.getByText('上海某机械厂')).toBeInTheDocument();
      expect(screen.getByText('电子元器件')).toBeInTheDocument();
      expect(screen.getByText('机械加工')).toBeInTheDocument();
      expect(screen.getByText('张经理')).toBeInTheDocument();
      expect(screen.getByText('13800138000')).toBeInTheDocument();
    });
  });

  it('shows stats cards based on loaded suppliers', async () => {
    render(
      <MemoryRouter>
        <SupplierManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('供应商总数')).toBeInTheDocument();
      expect(screen.getByText('A级供应商')).toBeInTheDocument();
      expect(screen.getByText('B级供应商')).toBeInTheDocument();
      expect(screen.getByText('活跃供应商')).toBeInTheDocument();
      expect(screen.getByText('平均评分')).toBeInTheDocument();
    });
  });

  it('filters suppliers by search text safely', async () => {
    render(
      <MemoryRouter>
        <SupplierManagement />
      </MemoryRouter>
    );

    const searchInput = await screen.findByPlaceholderText('搜索供应商名称、分类、联系人...');
    fireEvent.change(searchInput, { target: { value: '上海' } });

    await waitFor(() => {
      expect(screen.getByText('上海某机械厂')).toBeInTheDocument();
      expect(screen.queryByText('深圳某电子厂')).not.toBeInTheDocument();
    });
  });

  it('shows empty state when api returns no suppliers', async () => {
    supplierApi.list.mockResolvedValueOnce({ data: { items: [] } });

    render(
      <MemoryRouter>
        <SupplierManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('没有符合条件的供应商')).toBeInTheDocument();
    });
  });
});
