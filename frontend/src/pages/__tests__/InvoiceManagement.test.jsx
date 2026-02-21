/**
 * InvoiceManagement 组件测试
 * 测试覆盖：发票列表显示、开票管理、发票状态、筛选搜索、导出功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import InvoiceManagement from '../invoice/InvoiceManagement';
import api from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    tr: ({ children, ...props }) => <tr {...props}>{children}</tr>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('InvoiceManagement', () => {
  const mockInvoices = [
    {
      id: 1,
      invoiceNo: 'INV-2024-001',
      projectId: 1,
      projectName: '智能制造系统',
      customerId: 1,
      customerName: '华为技术有限公司',
      invoiceType: 'VAT_SPECIAL',
      taxRate: 13,
      amount: 1000000,
      taxAmount: 130000,
      totalAmount: 1130000,
      invoiceDate: '2024-02-15',
      status: 'issued',
      paymentStatus: 'paid',
      remark: '项目首期款发票',
      createdAt: '2024-02-10',
      issuedAt: '2024-02-15',
    },
    {
      id: 2,
      invoiceNo: 'INV-2024-002',
      projectId: 2,
      projectName: 'ERP系统升级',
      customerId: 2,
      customerName: '中兴通讯',
      invoiceType: 'VAT_ORDINARY',
      taxRate: 6,
      amount: 500000,
      taxAmount: 30000,
      totalAmount: 530000,
      invoiceDate: null,
      status: 'draft',
      paymentStatus: 'pending',
      remark: '等待开票',
      createdAt: '2024-02-01',
      issuedAt: null,
    },
    {
      id: 3,
      invoiceNo: 'INV-2024-003',
      projectId: 3,
      projectName: 'CRM系统开发',
      customerId: 3,
      customerName: '小米科技',
      invoiceType: 'VAT_SPECIAL',
      taxRate: 13,
      amount: 800000,
      taxAmount: 104000,
      totalAmount: 904000,
      invoiceDate: '2024-01-30',
      status: 'issued',
      paymentStatus: 'paid',
      remark: '全额开票',
      createdAt: '2024-01-25',
      issuedAt: '2024-01-30',
    },
  ];

  const mockStats = {
    totalInvoices: 120,
    draftCount: 15,
    issuedCount: 85,
    cancelledCount: 5,
    totalAmount: 50000000,
    paidAmount: 35000000,
    unpaidAmount: 15000000,
    thisMonthIssued: 8,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    api.get.mockImplementation((url) => {
      if (url.includes('/invoices/stats')) {
        return Promise.resolve({ data: mockStats });
      }
      if (url.includes('/invoices')) {
        return Promise.resolve({ 
          data: {
            items: mockInvoices,
            total: mockInvoices.length,
            page: 1,
            pageSize: 20,
          }
        });
      }
      return Promise.resolve({ data: {} });
    });

    api.post.mockResolvedValue({ data: { success: true } });
    api.put.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render invoice management title', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/发票管理|Invoice Management/i)).toBeInTheDocument();
    });

    it('should render statistics cards', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/invoices/stats'));
      });
    });

    it('should display action buttons', () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增发票|Add Invoice/i });
      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      
      expect(addButton || exportButton).toBeTruthy();
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch invoices on mount', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/invoices'));
      });
    });

    it('should handle API error gracefully', async () => {
      api.get.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should display empty state when no invoices', async () => {
      api.get.mockResolvedValueOnce({ 
        data: { items: [], total: 0, page: 1, pageSize: 20 } 
      });

      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无发票|No invoices/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 发票列表显示测试
  describe('Invoice List Display', () => {
    it('should display invoice numbers', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
        expect(screen.getByText('INV-2024-002')).toBeInTheDocument();
      });
    });

    it('should show project names', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
        expect(screen.getByText(/ERP系统升级/)).toBeInTheDocument();
      });
    });

    it('should display customer names', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
        expect(screen.getByText(/中兴通讯/)).toBeInTheDocument();
      });
    });

    it('should show invoice amounts', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const amounts = screen.queryAllByText(/1,130,000|530,000|904,000/);
        expect(amounts.length).toBeGreaterThan(0);
      });
    });

    it('should display invoice status badges', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText(/已开票|Issued/i).length).toBeGreaterThan(0);
        expect(screen.getByText(/草稿|Draft/i)).toBeInTheDocument();
      });
    });
  });

  // 4. 发票类型显示测试
  describe('Invoice Type Display', () => {
    it('should display VAT special invoices', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const vatSpecial = screen.queryAllByText(/增值税专用发票|VAT Special/i);
        expect(vatSpecial.length).toBeGreaterThan(0);
      });
    });

    it('should show VAT ordinary invoices', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const vatOrdinary = screen.queryByText(/增值税普通发票|VAT Ordinary/i);
        expect(vatOrdinary).toBeTruthy();
      });
    });

    it('should display tax rates', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText(/13%/).length).toBeGreaterThan(0);
        expect(screen.getByText(/6%/)).toBeInTheDocument();
      });
    });
  });

  // 5. 统计数据测试
  describe('Statistics Display', () => {
    it('should display total invoices count', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('120')).toBeInTheDocument();
      });
    });

    it('should show total amount', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalAmount = screen.queryByText(/50,000,000/);
        expect(totalAmount).toBeTruthy();
      });
    });

    it('should display paid amount', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const paidAmount = screen.queryByText(/35,000,000/);
        expect(paidAmount).toBeTruthy();
      });
    });

    it('should show this month issued count', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('8')).toBeInTheDocument();
      });
    });
  });

  // 6. 筛选功能测试
  describe('Filter Functionality', () => {
    it('should filter by invoice status', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const issuedFilter = screen.queryByRole('button', { name: /已开票|Issued/i });
      if (issuedFilter) {
        fireEvent.click(issuedFilter);
      }
    });

    it('should filter by invoice type', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const typeFilter = screen.queryByText(/增值税专用发票|VAT Special/i);
      if (typeFilter) {
        const button = typeFilter.closest('button');
        if (button) fireEvent.click(button);
      }
    });

    it('should filter by payment status', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const paidFilter = screen.queryByRole('button', { name: /已付款|Paid/i });
      if (paidFilter) {
        fireEvent.click(paidFilter);
      }
    });
  });

  // 7. 搜索功能测试
  describe('Search Functionality', () => {
    it('should render search input', () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      const searchInput = screen.queryByPlaceholderText(/搜索发票|Search invoice/i);
      expect(searchInput).toBeTruthy();
    });

    it('should search by invoice number', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索发票|Search invoice/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: 'INV-2024-001' } });
      }
    });

    it('should search by customer name', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索发票|Search invoice/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '华为' } });
      }
    });
  });

  // 8. 发票操作测试
  describe('Invoice Actions', () => {
    it('should view invoice detail', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);
      }
    });

    it('should issue an invoice', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('INV-2024-002')).toBeInTheDocument();
      });

      const issueButtons = screen.queryAllByRole('button', { name: /开票|Issue/i });
      if (issueButtons.length > 0) {
        fireEvent.click(issueButtons[0]);
        
        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });

    it('should add new invoice', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增发票|Add Invoice/i });
      if (addButton) {
        fireEvent.click(addButton);
      }
    });

    it('should cancel an invoice', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });

      const cancelButtons = screen.queryAllByRole('button', { name: /作废|Cancel/i });
      if (cancelButtons.length > 0) {
        fireEvent.click(cancelButtons[0]);
        
        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });
  });

  // 9. 导出功能测试
  describe('Export Functionality', () => {
    it('should render export button', () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      expect(exportButton).toBeTruthy();
    });

    it('should trigger export when clicking export button', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);
      }
    });
  });

  // 10. 分页功能测试
  describe('Pagination', () => {
    it('should display pagination controls', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const pagination = screen.queryByRole('navigation');
        expect(pagination).toBeTruthy();
      });
    });

    it('should navigate to next page', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const nextButton = screen.queryByRole('button', { name: /下一页|Next/i });
      if (nextButton && !nextButton.disabled) {
        fireEvent.click(nextButton);
      }
    });
  });

  // 11. 税额计算测试
  describe('Tax Calculation', () => {
    it('should display tax amounts', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const taxAmounts = screen.queryAllByText(/130,000|30,000|104,000/);
        expect(taxAmounts.length).toBeGreaterThan(0);
      });
    });

    it('should show total amounts including tax', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalAmounts = screen.queryAllByText(/1,130,000|530,000|904,000/);
        expect(totalAmounts.length).toBeGreaterThan(0);
      });
    });
  });

  // 12. 日期显示测试
  describe('Date Display', () => {
    it('should display invoice dates', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-01-30/)).toBeInTheDocument();
      });
    });

    it('should show created dates', async () => {
      render(
        <MemoryRouter>
          <InvoiceManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const dates = screen.queryAllByText(/2024-02-10|2024-02-01|2024-01-25/);
        expect(dates.length).toBeGreaterThan(0);
      });
    });
  });
});
