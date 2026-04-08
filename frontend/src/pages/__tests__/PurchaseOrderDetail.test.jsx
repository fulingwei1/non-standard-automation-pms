import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PurchaseOrderDetail from '../PurchaseOrderDetail';

const mockNavigate = vi.fn();
const mockUsePurchaseOrder = vi.fn();

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: '1' }),
  };
});

vi.mock('../PurchaseOrderDetail/usePurchaseOrder', () => ({
  usePurchaseOrder: (...args) => mockUsePurchaseOrder(...args),
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(
        Object.entries(props).filter(
          ([k]) =>
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
            ].includes(k)
        )
      );
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    },
  }),
  AnimatePresence: ({ children }) => children,
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useInView: () => true,
}));

const mockPo = {
  id: '1',
  poNumber: 'PO-2024-001',
  projectName: '智能制造系统',
  supplier: {
    id: '1',
    name: '深圳市某某电子有限公司',
    contact: '王经理',
    phone: '13800138000',
    email: 'buyer@example.com',
    address: '深圳市南山区科技园',
    paymentTerm: '货到付款',
  },
  status: 'draft',
  issueDate: '2024-02-10',
  requiredDate: '2024-03-15',
  expectedDelivery: '2024-03-15',
  actualDelivery: '',
  totalAmount: 500000,
  taxRate: 13,
  taxAmount: 65000,
  totalWithTax: 565000,
  paymentStatus: 'unpaid',
  paidAmount: 0,
  invoiceStatus: 'pending',
  invoicedAmount: 0,
  items: [
    {
      id: '1',
      itemNo: 1,
      materialCode: 'MAT-001',
      description: '伺服电机',
      specification: 'AC 220V 3KW',
      quantity: 10,
      unit: '台',
      unitPrice: 50000,
      amount: 500000,
      receivedQty: 0,
      status: 'confirmed',
    },
  ],
  timeline: [
    { stage: 'draft', label: '草稿', status: 'completed', date: '2024-02-10', description: '采购订单创建' },
    { stage: 'submitted', label: '已提交', status: 'completed', date: '2024-02-11', description: '订单已提交给供应商' },
    { stage: 'confirmed', label: '已确认', status: 'pending', date: null, description: '供应商已确认订单' },
  ],
  documents: [
    { id: '1', name: '采购申请单.pdf', size: '120KB', uploadDate: '2024-02-08', url: '/files/purchase-request.pdf' },
  ],
  remarks: '紧急采购，请尽快发货',
  attachedProject: {
    id: '1',
    name: '智能制造系统',
    stage: '采购阶段',
  },
};

const renderPage = () =>
  render(
    <MemoryRouter>
      <PurchaseOrderDetail />
    </MemoryRouter>
  );

describe('PurchaseOrderDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePurchaseOrder.mockReturnValue({
      po: mockPo,
      loading: false,
      error: null,
      progress: 67,
      totalItems: 500000,
    });
  });

  it('renders purchase order header and project name', () => {
    renderPage();

    expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
    expect(screen.getByText('智能制造系统')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /编辑/i })).toBeInTheDocument();
  });

  it('renders supplier and line item information', () => {
    renderPage();

    expect(screen.getByText('深圳市某某电子有限公司')).toBeInTheDocument();
    expect(screen.getByText('王经理')).toBeInTheDocument();
    expect(screen.getByText('13800138000')).toBeInTheDocument();
    expect(screen.getByText('伺服电机')).toBeInTheDocument();
    expect(screen.getByText('AC 220V 3KW')).toBeInTheDocument();
  });

  it('renders documents and notes content after switching current custom tabs', () => {
    renderPage();

    expect(screen.getByText('物料清单')).toBeInTheDocument();
    expect(screen.getByText('伺服电机')).toBeInTheDocument();

    fireEvent.click(screen.getByText('文件附件'));
    expect(screen.getByText('采购申请单.pdf')).toBeInTheDocument();

    fireEvent.click(screen.getByText('备注'));
    expect(screen.getByText('紧急采购，请尽快发货')).toBeInTheDocument();
    expect(screen.getByText('1 - 智能制造系统')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    mockUsePurchaseOrder.mockReturnValueOnce({
      po: null,
      loading: true,
      error: null,
      progress: 0,
      totalItems: 0,
    });

    renderPage();

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('renders not found state when hook returns no order', () => {
    mockUsePurchaseOrder.mockReturnValueOnce({
      po: null,
      loading: false,
      error: null,
      progress: 0,
      totalItems: 0,
    });

    renderPage();

    expect(screen.getByText('采购订单不存在')).toBeInTheDocument();
  });
});
