import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const {
  mockInvoiceList,
  mockInvoiceCreate,
  mockInvoiceGet,
  mockInvoiceUpdate,
  mockInvoiceIssue,
  mockInvoiceReceivePayment,
  mockContractList,
  consoleErrorMock,
  alertMock,
} = vi.hoisted(() => ({
  mockInvoiceList: vi.fn(),
  mockInvoiceCreate: vi.fn(),
  mockInvoiceGet: vi.fn(),
  mockInvoiceUpdate: vi.fn(),
  mockInvoiceIssue: vi.fn(),
  mockInvoiceReceivePayment: vi.fn(),
  mockContractList: vi.fn(),
  consoleErrorMock: vi.fn(),
  alertMock: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  invoiceApi: {
    list: mockInvoiceList,
    create: mockInvoiceCreate,
    get: mockInvoiceGet,
    update: mockInvoiceUpdate,
    issue: mockInvoiceIssue,
    receivePayment: mockInvoiceReceivePayment,
  },
  contractApi: {
    list: mockContractList,
  },
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const Tag = typeof tag === 'string' ? tag : 'div';
        const filteredProps = Object.fromEntries(
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
              ].includes(key),
          ),
        );
        return <Tag {...filteredProps}>{children}</Tag>;
      },
    },
  ),
  AnimatePresence: ({ children }) => <>{children}</>,
}));

vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, description, subtitle, action }) => (
    <div>
      <h1>{title}</h1>
      <p>{description || subtitle}</p>
      {action}
    </div>
  ),
}));

vi.mock('../../components/ui', () => ({
  Card: ({ children }) => <div>{children}</div>,
  CardHeader: ({ children }) => <div>{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>,
  CardTitle: ({ children }) => <h2>{children}</h2>,
  Button: ({ children, onClick, disabled, type = 'button' }) => (
    <button type={type} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock('../../components/invoice-management/InvoiceStats', () => ({
  default: ({ stats }) => (
    <div>
      <p>统计-总数:{stats.totalInvoices}</p>
      <p>统计-总金额:{stats.totalAmount}</p>
      <p>统计-已收款:{stats.paidAmount}</p>
      <p>统计-待收款:{stats.pendingAmount}</p>
    </div>
  ),
}));

vi.mock('../../components/invoice-management/InvoiceFilters', () => ({
  default: ({
    searchText,
    onSearchChange,
    filterStatus,
    onStatusChange,
    filterPayment,
    onPaymentChange,
  }) => (
    <div>
      <label htmlFor="invoice-search">搜索</label>
      <input
        id="invoice-search"
        value={searchText}
        onChange={(event) => onSearchChange(event.target.value)}
      />
      <p>状态:{filterStatus}</p>
      <button type="button" onClick={() => onStatusChange('draft')}>
        筛选草稿
      </button>
      <button type="button" onClick={() => onStatusChange('issued')}>
        筛选已开票
      </button>
      <p>收款:{filterPayment}</p>
      <button type="button" onClick={() => onPaymentChange('pending')}>
        筛选待收款
      </button>
      <button type="button" onClick={() => onPaymentChange('paid')}>
        筛选已收款
      </button>
    </div>
  ),
}));

vi.mock('../../components/invoice-management/InvoiceRow', () => ({
  default: ({ invoice, onView, onEdit, onDelete, onIssue, onReceivePayment }) => (
    <div data-testid={`invoice-row-${invoice.id}`}>
      <span>{invoice.id}</span>
      <span>{invoice.projectName}</span>
      <span>{invoice.customerName}</span>
      <span>{invoice.status}</span>
      <span>{invoice.paymentStatus}</span>
      <button type="button" onClick={() => onView(invoice)}>
        查看-{invoice.id}
      </button>
      {invoice.status === 'draft' ? (
        <>
          <button type="button" onClick={() => onEdit(invoice)}>
            编辑-{invoice.id}
          </button>
          <button type="button" onClick={() => onDelete(invoice)}>
            删除-{invoice.id}
          </button>
        </>
      ) : null}
      {invoice.status === 'approved' ? (
        <button type="button" onClick={() => onIssue(invoice)}>
          开票-{invoice.id}
        </button>
      ) : null}
      {invoice.status === 'issued' && invoice.paymentStatus !== 'paid' ? (
        <button type="button" onClick={() => onReceivePayment(invoice)}>
          收款-{invoice.id}
        </button>
      ) : null}
    </div>
  ),
}));

vi.mock('../../components/invoice-management/dialogs', () => ({
  CreateInvoiceDialog: ({ open, onSubmit }) =>
    open ? (
      <div>
        <h3>新建发票弹窗</h3>
        <button type="button" onClick={onSubmit}>
          提交新建发票
        </button>
      </div>
    ) : null,
  EditInvoiceDialog: ({ open, formData, onSubmit }) =>
    open ? (
      <div>
        <h3>编辑发票弹窗</h3>
        <p>合同:{formData.contract_id}</p>
        <p>税率:{formData.tax_rate}</p>
        <button type="button" onClick={onSubmit}>
          提交编辑发票
        </button>
      </div>
    ) : null,
  IssueInvoiceDialog: ({ open, onSubmit }) =>
    open ? (
      <div>
        <h3>开票弹窗</h3>
        <button type="button" onClick={onSubmit}>
          提交开票
        </button>
      </div>
    ) : null,
  PaymentDialog: ({ open, selectedInvoice, paymentData, onConfirm }) =>
    open ? (
      <div>
        <h3>收款弹窗</h3>
        <p>收款对象:{selectedInvoice?.id}</p>
        <p>收款金额:{paymentData.paid_amount}</p>
        <button type="button" onClick={onConfirm}>
          提交收款
        </button>
      </div>
    ) : null,
  DeleteConfirmDialog: ({ open, description, onConfirm }) =>
    open ? (
      <div>
        <h3>删除确认弹窗</h3>
        <p>{description}</p>
        <button type="button" onClick={onConfirm}>
          确认删除发票
        </button>
      </div>
    ) : null,
}));

import InvoiceManagement from '../invoice/InvoiceManagement';

const invoiceItems = [
  {
    id: 101,
    invoice_code: 'INV-001',
    contract_code: 'HT-001',
    project_name: '智能产线',
    customer_name: '华为',
    amount: '100',
    tax_rate: '13',
    tax_amount: '13',
    total_amount: '113',
    invoice_type: 'SPECIAL',
    status: 'DRAFT',
    issue_date: null,
    due_date: '2026-04-30',
    payment_status: 'PENDING',
    paid_amount: '0',
    paid_date: null,
    remark: '待处理',
  },
  {
    id: 102,
    invoice_code: 'INV-002',
    contract_code: 'HT-002',
    project_name: '视觉检测',
    customer_name: '中兴',
    amount: '200',
    tax_rate: '13',
    tax_amount: '26',
    total_amount: '226',
    invoice_type: 'SPECIAL',
    status: 'APPROVED',
    issue_date: null,
    due_date: '2026-05-05',
    payment_status: 'PENDING',
    paid_amount: '0',
    paid_date: null,
    remark: '待开票',
  },
  {
    id: 103,
    invoice_code: 'INV-003',
    contract_code: 'HT-003',
    project_name: '售后系统',
    customer_name: '小米',
    amount: '300',
    tax_rate: '13',
    tax_amount: '39',
    total_amount: '339',
    invoice_type: 'ORDINARY',
    status: 'ISSUED',
    issue_date: '2026-04-01',
    due_date: '2026-04-20',
    payment_status: 'PARTIAL',
    paid_amount: '100',
    paid_date: '2026-04-02',
    remark: '已部分收款',
  },
];

const contractItems = [
  { id: 'contract-1', contract_code: 'HT-001', name: '合同1' },
  { id: 'contract-2', contract_code: 'HT-002', name: '合同2' },
];

const invoiceDetail = {
  contract_id: 'contract-1',
  invoice_type: 'SPECIAL',
  amount: '100',
  tax_rate: '13',
  issue_date: '2026-04-08',
  due_date: '2026-04-30',
  remark: '详情备注',
};

describe('InvoiceManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(consoleErrorMock);
    vi.spyOn(window, 'alert').mockImplementation(alertMock);

    mockInvoiceList.mockResolvedValue({
      data: {
        items: invoiceItems,
        total: 45,
      },
    });
    mockContractList.mockResolvedValue({
      data: {
        items: contractItems,
      },
    });
    mockInvoiceCreate.mockResolvedValue({ data: { success: true } });
    mockInvoiceGet.mockResolvedValue({ data: invoiceDetail });
    mockInvoiceUpdate.mockResolvedValue({ data: { success: true } });
    mockInvoiceIssue.mockResolvedValue({ data: { success: true } });
    mockInvoiceReceivePayment.mockResolvedValue({ data: { success: true } });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <InvoiceManagement />
      </MemoryRouter>,
    );
  }

  it('默认加载发票和合同并渲染页面统计', async () => {
    renderPage();

    await waitFor(() => {
      expect(mockInvoiceList).toHaveBeenCalledWith({
        page: 1,
        page_size: 20,
        keyword: undefined,
        status: undefined,
        payment_status: undefined,
      });
    });

    expect(mockContractList).toHaveBeenCalledWith({ page: 1, page_size: 100 });
    expect(screen.getByText('对账开票管理')).toBeInTheDocument();
    expect(screen.getByText('发票申请、开票、收款跟踪')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /新建发票/i })).toBeInTheDocument();
    expect(await screen.findByText('统计-总数:3')).toBeInTheDocument();
    expect(screen.getByText('统计-总金额:678')).toBeInTheDocument();
    expect(screen.getByText('统计-已收款:0')).toBeInTheDocument();
    expect(screen.getByText('统计-待收款:339')).toBeInTheDocument();
    expect(screen.getByText('共 3 份发票')).toBeInTheDocument();
    expect(screen.getByText('INV-001')).toBeInTheDocument();
    expect(screen.getByText('INV-002')).toBeInTheDocument();
    expect(screen.getByText('INV-003')).toBeInTheDocument();
    expect(screen.getByText('第 1 页，共 3 页')).toBeInTheDocument();
  });

  it('搜索和筛选变化时按真实参数重新请求列表', async () => {
    renderPage();

    await waitFor(() => {
      expect(mockInvoiceList).toHaveBeenCalledTimes(1);
    });

    vi.clearAllMocks();

    fireEvent.change(screen.getByLabelText('搜索'), {
      target: { value: '华为' },
    });
    fireEvent.click(screen.getByRole('button', { name: '筛选已开票' }));
    fireEvent.click(screen.getByRole('button', { name: '筛选已收款' }));

    await waitFor(() => {
      expect(mockInvoiceList).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 20,
        keyword: '华为',
        status: 'ISSUED',
        payment_status: 'PAID',
      });
    });
  });

  it('支持打开新建发票弹窗并提交创建', async () => {
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: /新建发票/i }));

    expect(screen.getByText('新建发票弹窗')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '提交新建发票' }));

    await waitFor(() => {
      expect(mockInvoiceCreate).toHaveBeenCalledWith({
        contract_id: '',
        invoice_type: 'SPECIAL',
        amount: '',
        tax_rate: '13',
        issue_date: '',
        due_date: '',
        remark: '',
      });
    });

    await waitFor(() => {
      expect(mockInvoiceList).toHaveBeenCalledTimes(2);
    });
  });

  it('支持编辑草稿发票并按详情回填后更新', async () => {
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: '编辑-INV-001' }));

    await waitFor(() => {
      expect(mockInvoiceGet).toHaveBeenCalledWith(101);
    });

    expect(await screen.findByText('编辑发票弹窗')).toBeInTheDocument();
    expect(screen.getByText('合同:contract-1')).toBeInTheDocument();
    expect(screen.getByText('税率:13')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '提交编辑发票' }));

    await waitFor(() => {
      expect(mockInvoiceUpdate).toHaveBeenCalledWith(101, {
        contract_id: 'contract-1',
        invoice_type: 'SPECIAL',
        amount: '100',
        tax_rate: '13',
        issue_date: '2026-04-08',
        due_date: '2026-04-30',
        remark: '详情备注',
      });
    });
  });

  it('支持删除草稿发票并调用作废更新接口', async () => {
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: '删除-INV-001' }));

    expect(await screen.findByText('删除确认弹窗')).toBeInTheDocument();
    expect(screen.getByText('确定要删除发票 INV-001 吗？此操作不可撤销。')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '确认删除发票' }));

    await waitFor(() => {
      expect(mockInvoiceUpdate).toHaveBeenCalledWith(101, { status: 'VOID' });
    });

    expect(alertMock).toHaveBeenCalledWith('发票已删除');
  });

  it('列表接口失败时记录日志并显示空列表态', async () => {
    mockInvoiceList.mockRejectedValueOnce(new Error('Load failed'));

    renderPage();

    await waitFor(() => {
      expect(consoleErrorMock).toHaveBeenCalled();
    });

    expect(await screen.findByText('没有符合条件的发票')).toBeInTheDocument();
  });

  it('应该处理创建发票失败的情况', async () => {
    mockInvoiceCreate.mockRejectedValueOnce(new Error('Create failed'));
    
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: /新建发票/i }));
    fireEvent.click(screen.getByRole('button', { name: '提交新建发票' }));

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith('创建发票失败: Create failed');
    });
  });

  it('应该处理开票失败的情况', async () => {
    mockInvoiceIssue.mockRejectedValueOnce(new Error('Issue failed'));
    
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: '开票-INV-002' }));
    fireEvent.click(screen.getByRole('button', { name: '提交开票' }));

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith('开票失败: Issue failed');
    });
  });

  it('应该处理收款失败的情况', async () => {
    mockInvoiceReceivePayment.mockRejectedValueOnce(new Error('Payment failed'));
    
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: '收款-INV-003' }));
    fireEvent.click(screen.getByRole('button', { name: '提交收款' }));

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith('记录收款失败: Payment failed');
    });
  });

  it('应该处理更新发票失败的情况', async () => {
    mockInvoiceUpdate.mockRejectedValueOnce(new Error('Update failed'));
    
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: '编辑-INV-001' }));
    
    // 等待编辑对话框出现并找到提交按钮
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '提交编辑发票' })).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: '提交编辑发票' }));

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith('更新发票失败: Update failed');
    });
  });

  it('应该处理删除发票失败的情况', async () => {
    mockInvoiceUpdate.mockRejectedValueOnce(new Error('Delete failed'));
    
    renderPage();

    await screen.findByText('INV-001');

    fireEvent.click(screen.getByRole('button', { name: '删除-INV-001' }));
    
    // 等待确认对话框出现并找到确认按钮
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '确认删除发票' })).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: '确认删除发票' }));

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith('删除发票失败: Delete failed');
    });
  });

  it('应该处理加载合同失败的情况', async () => {
    mockContractList.mockRejectedValueOnce(new Error('Contract load failed'));
    
    renderPage();

    // Should still render the page even if contract loading fails
    await waitFor(() => {
      expect(screen.getByText('对账开票管理')).toBeInTheDocument();
    });
  });
});
