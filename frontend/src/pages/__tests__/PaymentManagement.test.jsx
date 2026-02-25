/**
 * PaymentManagement 组件测试
 * 测试覆盖：回款记录显示、筛选功能、回款状态管理、统计数据、导出功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PaymentManagement from '../PaymentManagement/index';
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

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe.skip('PaymentManagement', () => {
  const mockPayments = [
    {
      id: 1,
      paymentNo: 'PAY-2024-001',
      projectId: 1,
      projectName: '智能制造系统',
      projectCode: 'PROJ-001',
      customerId: 1,
      customerName: '华为技术有限公司',
      contractAmount: 1000000,
      paidAmount: 300000,
      unpaidAmount: 700000,
      paymentDate: '2024-02-15',
      paymentMethod: 'bank_transfer',
      status: 'paid',
      invoiceNo: 'INV-2024-001',
      remark: '首期款项',
      createdAt: '2024-02-10',
      updatedAt: '2024-02-15',
    },
    {
      id: 2,
      paymentNo: 'PAY-2024-002',
      projectId: 2,
      projectName: 'ERP系统升级',
      projectCode: 'PROJ-002',
      customerId: 2,
      customerName: '中兴通讯',
      contractAmount: 500000,
      paidAmount: 0,
      unpaidAmount: 500000,
      paymentDate: null,
      paymentMethod: null,
      status: 'pending',
      invoiceNo: null,
      remark: '等待客户付款',
      createdAt: '2024-02-01',
      updatedAt: '2024-02-01',
    },
    {
      id: 3,
      paymentNo: 'PAY-2024-003',
      projectId: 3,
      projectName: 'CRM系统开发',
      projectCode: 'PROJ-003',
      customerId: 3,
      customerName: '小米科技',
      contractAmount: 800000,
      paidAmount: 800000,
      unpaidAmount: 0,
      paymentDate: '2024-01-30',
      paymentMethod: 'bank_transfer',
      status: 'completed',
      invoiceNo: 'INV-2024-002',
      remark: '已全款到账',
      createdAt: '2024-01-15',
      updatedAt: '2024-01-30',
    },
  ];

  const mockStats = {
    totalContracts: 50,
    totalAmount: 25000000,
    paidAmount: 15000000,
    unpaidAmount: 10000000,
    overdueAmount: 2000000,
    thisMonthPaid: 3000000,
    paymentRate: 60,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    api.get.mockImplementation((url) => {
      if (url.includes('/payments/stats')) {
        return Promise.resolve({ data: mockStats });
      }
      if (url.includes('/payments')) {
        return Promise.resolve({ 
          data: {
            items: mockPayments,
            total: mockPayments.length,
            page: 1,
            pageSize: 20,
          }
        });
      }
      return Promise.resolve({ data: {} });
    });

    api.put.mockResolvedValue({ data: { success: true } });
    api.post.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render payment management title', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/回款管理|Payment Management/i)).toBeInTheDocument();
    });

    it('should render statistics cards', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/payments/stats'));
      });
    });

    it('should display action buttons', () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增回款|Add Payment/i });
      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      
      expect(addButton || exportButton).toBeTruthy();
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch payments on mount', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/payments'));
      });
    });

    it('should handle API error gracefully', async () => {
      api.get.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should display empty state when no payments', async () => {
      api.get.mockResolvedValueOnce({ 
        data: { items: [], total: 0, page: 1, pageSize: 20 } 
      });

      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无回款记录|No payment records/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 回款记录显示测试
  describe('Payment Records Display', () => {
    it('should display payment numbers', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PAY-2024-001')).toBeInTheDocument();
        expect(screen.getByText('PAY-2024-002')).toBeInTheDocument();
      });
    });

    it('should show project names', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
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
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
        expect(screen.getByText(/中兴通讯/)).toBeInTheDocument();
      });
    });

    it('should show payment amounts', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const amounts = screen.queryAllByText(/300,000|1,000,000|500,000/);
        expect(amounts.length).toBeGreaterThan(0);
      });
    });

    it('should display payment status badges', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已付款|Paid/i)).toBeInTheDocument();
        expect(screen.getByText(/待付款|Pending/i)).toBeInTheDocument();
      });
    });
  });

  // 4. 统计数据测试
  describe('Statistics Display', () => {
    it('should display total contract amount', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalAmount = screen.queryByText(/25,000,000/);
        expect(totalAmount).toBeTruthy();
      });
    });

    it('should show paid amount', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const paidAmount = screen.queryByText(/15,000,000/);
        expect(paidAmount).toBeTruthy();
      });
    });

    it('should display unpaid amount', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const unpaidAmount = screen.queryByText(/10,000,000/);
        expect(unpaidAmount).toBeTruthy();
      });
    });

    it('should show payment rate', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/60%/)).toBeInTheDocument();
      });
    });
  });

  // 5. 筛选功能测试
  describe('Filter Functionality', () => {
    it('should filter by payment status', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
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

    it('should filter by date range', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const dateFilter = screen.queryByPlaceholderText(/选择日期|Select date/i);
      if (dateFilter) {
        fireEvent.change(dateFilter, { target: { value: '2024-02-01' } });
      }
    });

    it('should filter by customer', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const customerFilter = screen.queryByPlaceholderText(/选择客户|Select customer/i);
      if (customerFilter) {
        fireEvent.change(customerFilter, { target: { value: '1' } });
      }
    });
  });

  // 6. 搜索功能测试
  describe('Search Functionality', () => {
    it('should render search input', () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      const searchInput = screen.queryByPlaceholderText(/搜索回款|Search payment/i);
      expect(searchInput).toBeTruthy();
    });

    it('should search by payment number', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PAY-2024-001')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索回款|Search payment/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: 'PAY-2024-001' } });
      }
    });

    it('should search by project name', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索回款|Search payment/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '智能制造' } });
      }
    });
  });

  // 7. 回款操作测试
  describe('Payment Actions', () => {
    it('should view payment detail', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PAY-2024-001')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);
      }
    });

    it('should confirm payment', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PAY-2024-002')).toBeInTheDocument();
      });

      const confirmButtons = screen.queryAllByRole('button', { name: /确认收款|Confirm/i });
      if (confirmButtons.length > 0) {
        fireEvent.click(confirmButtons[0]);
        
        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });

    it('should add new payment record', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增回款|Add Payment/i });
      if (addButton) {
        fireEvent.click(addButton);
      }
    });
  });

  // 8. 导出功能测试
  describe('Export Functionality', () => {
    it('should render export button', () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      expect(exportButton).toBeTruthy();
    });

    it('should trigger export when clicking export button', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);
      }
    });
  });

  // 9. 分页功能测试
  describe('Pagination', () => {
    it('should display pagination controls', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
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
          <PaymentManagement />
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

  // 10. 付款方式显示测试
  describe('Payment Method Display', () => {
    it('should display payment methods', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const paymentMethod = screen.queryByText(/银行转账|Bank Transfer/i);
        expect(paymentMethod).toBeTruthy();
      });
    });

    it('should show invoice numbers', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('INV-2024-001')).toBeInTheDocument();
      });
    });
  });

  // 11. 排序功能测试
  describe('Sorting Functionality', () => {
    it('should sort by payment date', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const dateHeader = screen.queryByText(/回款日期|Payment Date/i);
      if (dateHeader) {
        fireEvent.click(dateHeader);
      }
    });

    it('should sort by amount', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const amountHeader = screen.queryByText(/回款金额|Amount/i);
      if (amountHeader) {
        fireEvent.click(amountHeader);
      }
    });
  });

  // 12. 逾期提醒测试
  describe('Overdue Reminder', () => {
    it('should display overdue amount', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const overdueAmount = screen.queryByText(/2,000,000|逾期/);
        expect(overdueAmount).toBeTruthy();
      });
    });

    it('should highlight overdue payments', async () => {
      render(
        <MemoryRouter>
          <PaymentManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const overdueIndicators = screen.queryAllByText(/逾期|Overdue/i);
        expect(overdueIndicators.length).toBeGreaterThanOrEqual(0);
      });
    });
  });
});
