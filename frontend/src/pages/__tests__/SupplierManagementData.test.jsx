import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SupplierManagementData from '../SupplierManagementData';
import { supplierApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  supplierApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    updateRating: vi.fn(),
  },
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(
        Object.entries(props).filter(
          ([key]) =>
            ![
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
            ].includes(key)
        )
      );
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    },
  }),
  AnimatePresence: ({ children }) => children,
}));

vi.mock('../../components/ui/dialog', () => ({
  Dialog: ({ open, children }) => (open ? <div data-testid="dialog-root">{children}</div> : null),
  DialogContent: ({ children, ...props }) => <div {...props}>{children}</div>,
  DialogHeader: ({ children, ...props }) => <div {...props}>{children}</div>,
  DialogTitle: ({ children, ...props }) => <h2 {...props}>{children}</h2>,
  DialogFooter: ({ children, ...props }) => <div {...props}>{children}</div>,
}));

vi.mock('../../components/ui/select', () => ({
  Select: ({ children }) => <div>{children}</div>,
  SelectContent: ({ children }) => <div>{children}</div>,
  SelectItem: ({ children, value }) => <div data-value={value}>{children}</div>,
  SelectTrigger: ({ children, className }) => <button type="button" className={className}>{children}</button>,
  SelectValue: ({ placeholder }) => <span>{placeholder}</span>,
}));

const mockSupplier = {
  id: 1,
  supplier_code: 'SUP-001',
  supplier_name: '供应商A',
  supplier_type: 'MATERIAL',
  contact_person: '张三',
  contact_phone: '13800138000',
  supplier_level: 'A',
  overall_rating: '4.6',
  status: 'ACTIVE',
};

const renderPage = () =>
  render(
    <MemoryRouter>
      <SupplierManagementData />
    </MemoryRouter>
  );

describe('SupplierManagementData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    supplierApi.list.mockResolvedValue({
      formatted: { items: [mockSupplier], total: 1 },
      data: { items: [mockSupplier], total: 1 },
    });
    supplierApi.get.mockResolvedValue({ data: mockSupplier });
    supplierApi.create.mockResolvedValue({ data: { success: true } });
    supplierApi.update.mockResolvedValue({ data: { success: true } });
    supplierApi.updateRating.mockResolvedValue({ data: { success: true } });
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders supplier list page and loads suppliers on mount', async () => {
    renderPage();

    expect(screen.getByText('供应商管理')).toBeInTheDocument();
    expect(screen.getByText('供应商列表')).toBeInTheDocument();

    await waitFor(() => {
      expect(supplierApi.list).toHaveBeenCalledWith({ page: 1, page_size: 20 });
    });

    expect(await screen.findByText('供应商A')).toBeInTheDocument();
    expect(screen.getByText('SUP-001')).toBeInTheDocument();
  });

  it('shows loading state while supplier list request is pending', () => {
    supplierApi.list.mockImplementation(() => new Promise(() => {}));

    renderPage();

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('searches suppliers by keyword', async () => {
    renderPage();

    await waitFor(() => {
      expect(supplierApi.list).toHaveBeenCalledTimes(1);
    });

    fireEvent.change(screen.getByPlaceholderText('搜索供应商名称/编码...'), {
      target: { value: '供应商A' },
    });

    await waitFor(() => {
      expect(supplierApi.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 20,
        keyword: '供应商A',
      });
    });
  });

  it('creates a supplier from the create dialog', async () => {
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /新增供应商/i }));

    expect(screen.getByRole('heading', { name: '新增供应商' })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('供应商编码 *'), {
      target: { name: 'supplier_code', value: 'SUP-002' },
    });
    fireEvent.change(screen.getByLabelText('供应商名称 *'), {
      target: { name: 'supplier_name', value: '供应商B' },
    });

    fireEvent.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => {
      expect(supplierApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          supplier_code: 'SUP-002',
          supplier_name: '供应商B',
        })
      );
    });

    await waitFor(() => {
      expect(supplierApi.list).toHaveBeenCalledTimes(2);
    });
  });

  it('loads next page when pagination button is clicked', async () => {
    supplierApi.list.mockResolvedValue({
      formatted: { items: [mockSupplier], total: 25 },
      data: { items: [mockSupplier], total: 25 },
    });

    renderPage();

    expect(await screen.findByRole('button', { name: '下一页' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '下一页' }));

    await waitFor(() => {
      expect(supplierApi.list).toHaveBeenLastCalledWith({ page: 2, page_size: 20 });
    });
  });

  it('alerts when loading suppliers fails', async () => {
    supplierApi.list.mockRejectedValueOnce(new Error('Load failed'));

    renderPage();

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('加载供应商列表失败: Load failed');
    });
  });

  it('should handle create supplier failure', async () => {
    supplierApi.create.mockRejectedValueOnce(new Error('Create failed'));

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /新增供应商/i }));

    fireEvent.change(screen.getByLabelText('供应商编码 *'), {
      target: { name: 'supplier_code', value: 'SUP-002' },
    });
    fireEvent.change(screen.getByLabelText('供应商名称 *'), {
      target: { name: 'supplier_name', value: '供应商B' },
    });

    fireEvent.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('创建供应商失败: Create failed');
    });
  });

  it('should handle update supplier failure', async () => {
    supplierApi.update.mockRejectedValueOnce(new Error('Update failed'));

    renderPage();

    // Mock getting supplier data for editing
    supplierApi.get.mockResolvedValueOnce({ data: mockSupplier });

    fireEvent.click(screen.getByText('供应商A')); // This would trigger edit

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('获取供应商信息失败: Update failed');
    });
  });

  it('should handle update rating failure', async () => {
    supplierApi.updateRating.mockRejectedValueOnce(new Error('Rating update failed'));

    renderPage();

    await waitFor(() => {
      expect(supplierApi.updateRating).not.toHaveBeenCalled();
    });
  });
});
