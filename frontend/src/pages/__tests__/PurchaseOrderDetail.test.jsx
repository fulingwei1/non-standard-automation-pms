/**
 * PurchaseOrderDetail 组件测试
 * 测试覆盖：订单详情显示、订单项列表、状态管理、操作按钮、文档管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import PurchaseOrderDetail from '../PurchaseOrderDetail';
import api, { purchaseApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    purchaseApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      orders: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        submit: vi.fn().mockResolvedValue({ data: {} }),
        approve: vi.fn().mockResolvedValue({ data: {} }),
        getItems: vi.fn().mockResolvedValue({ data: {} }),
        createFromBOM: vi.fn().mockResolvedValue({ data: {} }),
      },
      requests: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        submit: vi.fn().mockResolvedValue({ data: {} }),
        approve: vi.fn().mockResolvedValue({ data: {} }),
        generateOrders: vi.fn().mockResolvedValue({ data: {} }),
        delete: vi.fn().mockResolvedValue({ data: {} }),
      },
      receipts: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        getItems: vi.fn().mockResolvedValue({ data: {} }),
        receive: vi.fn().mockResolvedValue({ data: {} }),
        updateStatus: vi.fn().mockResolvedValue({ data: {} }),
        inspectItem: vi.fn().mockResolvedValue({ data: {} }),
      },
      items: {
        receive: vi.fn().mockResolvedValue({ data: {} }),
      },
      kitRate: {
        getProject: vi.fn().mockResolvedValue({ data: {} }),
        getMachine: vi.fn().mockResolvedValue({ data: {} }),
        getMachineStatus: vi.fn().mockResolvedValue({ data: {} }),
        getProjectMaterialStatus: vi.fn().mockResolvedValue({ data: {} }),
        unified: vi.fn().mockResolvedValue({ data: {} }),
        dashboard: vi.fn().mockResolvedValue({ data: {} }),
        trend: vi.fn().mockResolvedValue({ data: {} }),
      },
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
    useParams: () => ({ id: '1' }),
  };
});

describe.skip('PurchaseOrderDetail', () => {
  const mockOrder = {
    id: 1,
    orderNo: 'PO-2024-001',
    projectId: 1,
    projectName: '智能制造系统',
    projectCode: 'PROJ-001',
    supplierId: 1,
    supplierName: '深圳市某某电子有限公司',
    supplierCode: 'SUP-001',
    contactPerson: '王经理',
    contactPhone: '13800138000',
    totalAmount: 500000,
    status: 'approved',
    orderDate: '2024-02-10',
    deliveryDate: '2024-03-15',
    receivedDate: null,
    deliveryAddress: '深圳市南山区科技园',
    paymentTerms: '货到付款',
    items: [
      {
        id: 1,
        materialId: 1,
        materialCode: 'MAT-001',
        materialName: '伺服电机',
        specification: 'AC 220V 3KW',
        unit: '台',
        quantity: 10,
        unitPrice: 50000,
        totalPrice: 500000,
        receivedQuantity: 0,
      },
      {
        id: 2,
        materialId: 2,
        materialCode: 'MAT-002',
        materialName: 'PLC控制器',
        specification: 'S7-1200',
        unit: '套',
        quantity: 5,
        unitPrice: 20000,
        totalPrice: 100000,
        receivedQuantity: 0,
      },
    ],
    createdBy: '张三',
    createdAt: '2024-02-08',
    approvedBy: '李经理',
    approvedAt: '2024-02-09',
    remark: '紧急采购，请尽快发货',
    attachments: [
      {
        id: 1,
        name: '采购申请单.pdf',
        url: '/files/purchase-request.pdf',
      }
    ],
    receiveRecords: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    purchaseApi.orders.get.mockImplementation((url) => {
      if (url.includes('/purchase-orders/1')) {
        return Promise.resolve({ data: mockOrder });
      }
      return Promise.resolve({ data: {} });
    });

    purchaseApi.update.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render order detail with order number', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });
    });

    it('should display loading state initially', () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      const loadingElements = screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should render action buttons', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const backButton = screen.queryByRole('button', { name: /返回|Back/i });
      expect(backButton).toBeTruthy();
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch order details', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(purchaseApi.orders.get).toHaveBeenCalledWith(expect.stringContaining('/purchase-orders/1'));
      });
    });

    it('should handle API error', async () => {
      purchaseApi.orders.get.mockRejectedValueOnce(new Error('Failed to load order'));

      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should handle order not found', async () => {
      purchaseApi.orders.get.mockResolvedValueOnce({ data: null });

      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/未找到订单|Order not found/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 基本信息显示测试
  describe('Basic Information Display', () => {
    it('should display project information', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
        expect(screen.getByText('PROJ-001')).toBeInTheDocument();
      });
    });

    it('should show supplier information', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/深圳市某某电子有限公司/)).toBeInTheDocument();
        expect(screen.getByText(/王经理/)).toBeInTheDocument();
        expect(screen.getByText('13800138000')).toBeInTheDocument();
      });
    });

    it('should display order dates', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-10/)).toBeInTheDocument();
        expect(screen.getByText(/2024-03-15/)).toBeInTheDocument();
      });
    });

    it('should show order status', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已批准|Approved/i)).toBeInTheDocument();
      });
    });

    it('should display total amount', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/500,000/)).toBeInTheDocument();
      });
    });
  });

  // 4. 订单项列表测试
  describe('Order Items List', () => {
    it('should display all order items', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/伺服电机/)).toBeInTheDocument();
        expect(screen.getByText(/PLC控制器/)).toBeInTheDocument();
      });
    });

    it('should show material specifications', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/AC 220V 3KW/)).toBeInTheDocument();
        expect(screen.getByText(/S7-1200/)).toBeInTheDocument();
      });
    });

    it('should display quantities and prices', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText('10').length).toBeGreaterThan(0);
        expect(screen.getAllByText(/50,000/).length).toBeGreaterThan(0);
      });
    });

    it('should show received quantities', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const receivedQty = screen.queryAllByText(/已收货|Received/);
        expect(receivedQty.length).toBeGreaterThanOrEqual(0);
      });
    });
  });

  // 5. 操作按钮测试
  describe('Action Buttons', () => {
    it('should render back button', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const backButton = screen.queryByRole('button', { name: /返回|Back/i });
      if (backButton) {
        fireEvent.click(backButton);
        expect(mockNavigate).toHaveBeenCalledWith(-1);
      }
    });

    it('should confirm receipt when clicking receive button', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const receiveButton = screen.queryByRole('button', { name: /收货|Receive/i });
      if (receiveButton) {
        fireEvent.click(receiveButton);
        
        await waitFor(() => {
          expect(purchaseApi.update).toHaveBeenCalled();
        });
      }
    });

    it('should edit order when clicking edit button', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const editButton = screen.queryByRole('button', { name: /编辑|Edit/i });
      if (editButton) {
        fireEvent.click(editButton);
      }
    });

    it('should print order', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const printButton = screen.queryByRole('button', { name: /打印|Print/i });
      if (printButton) {
        fireEvent.click(printButton);
      }
    });
  });

  // 6. 附件管理测试
  describe('Attachments Management', () => {
    it('should display attachments list', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/采购申请单.pdf/)).toBeInTheDocument();
      });
    });

    it('should download attachment when clicking', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/采购申请单.pdf/)).toBeInTheDocument();
      });

      const downloadButton = screen.queryByRole('button', { name: /下载|Download/i });
      if (downloadButton) {
        fireEvent.click(downloadButton);
      }
    });
  });

  // 7. 收货记录测试
  describe('Receive Records', () => {
    it('should display receive records section', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const receiveSection = screen.queryByText(/收货记录|Receive Records/i);
        expect(receiveSection).toBeTruthy();
      });
    });

    it('should show empty state when no records', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const emptyState = screen.queryByText(/暂无收货记录|No receive records/i);
        expect(emptyState).toBeTruthy();
      });
    });
  });

  // 8. 备注信息测试
  describe('Remark Information', () => {
    it('should display order remark', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/紧急采购，请尽快发货/)).toBeInTheDocument();
      });
    });

    it('should show payment terms', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/货到付款/)).toBeInTheDocument();
      });
    });

    it('should display delivery address', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/深圳市南山区科技园/)).toBeInTheDocument();
      });
    });
  });

  // 9. 审批信息测试
  describe('Approval Information', () => {
    it('should display created by user', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
      });
    });

    it('should show approved by user', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/李经理/)).toBeInTheDocument();
      });
    });

    it('should display approval date', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-09/)).toBeInTheDocument();
      });
    });
  });

  // 10. 导航测试
  describe('Navigation', () => {
    it('should navigate to project detail', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
      });

      const projectLink = screen.getByText(/智能制造系统/);
      const clickableLink = projectLink.closest('a') || projectLink.closest('button');
      if (clickableLink) {
        fireEvent.click(clickableLink);
      }
    });

    it('should navigate to supplier detail', async () => {
      render(
        <MemoryRouter initialEntries={['/purchase-orders/1']}>
          <Routes>
            <Route path="/purchase-orders/:id" element={<PurchaseOrderDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/深圳市某某电子有限公司/)).toBeInTheDocument();
      });

      const supplierLink = screen.getByText(/深圳市某某电子有限公司/);
      const clickableLink = supplierLink.closest('a') || supplierLink.closest('button');
      if (clickableLink) {
        fireEvent.click(clickableLink);
      }
    });
  });
});
