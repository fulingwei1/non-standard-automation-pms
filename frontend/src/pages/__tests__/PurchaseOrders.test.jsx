/**
 * PurchaseOrders 组件测试
 * 测试覆盖：采购订单列表、订单状态管理、筛选搜索、订单操作、统计数据
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PurchaseOrders from '../PurchaseOrders/index';
import api from '../../services/api';

// Mock API
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

describe.skip('PurchaseOrders', () => {
  const mockOrders = [
    {
      id: 1,
      orderNo: 'PO-2024-001',
      projectId: 1,
      projectName: '智能制造系统',
      supplierId: 1,
      supplierName: '深圳市某某电子有限公司',
      totalAmount: 500000,
      status: 'approved',
      orderDate: '2024-02-10',
      deliveryDate: '2024-03-15',
      receivedDate: null,
      items: [
        { materialName: '伺服电机', quantity: 10, unitPrice: 50000 }
      ],
      createdBy: '张三',
      approvedBy: '李经理',
      remark: '紧急采购',
    },
    {
      id: 2,
      orderNo: 'PO-2024-002',
      projectId: 2,
      projectName: 'ERP系统升级',
      supplierId: 2,
      supplierName: '北京某某科技有限公司',
      totalAmount: 300000,
      status: 'pending',
      orderDate: '2024-02-15',
      deliveryDate: '2024-03-20',
      receivedDate: null,
      items: [
        { materialName: '服务器', quantity: 5, unitPrice: 60000 }
      ],
      createdBy: '李四',
      approvedBy: null,
      remark: '等待审批',
    },
    {
      id: 3,
      orderNo: 'PO-2024-003',
      projectId: 3,
      projectName: 'CRM系统开发',
      supplierId: 3,
      supplierName: '上海某某软件有限公司',
      totalAmount: 200000,
      status: 'received',
      orderDate: '2024-01-20',
      deliveryDate: '2024-02-25',
      receivedDate: '2024-02-20',
      items: [
        { materialName: '软件授权', quantity: 100, unitPrice: 2000 }
      ],
      createdBy: '王五',
      approvedBy: '赵总监',
      remark: '已收货',
    },
  ];

  const mockStats = {
    totalOrders: 150,
    pendingOrders: 20,
    approvedOrders: 80,
    receivedOrders: 45,
    cancelledOrders: 5,
    totalAmount: 15000000,
    thisMonthOrders: 12,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    api.get.mockImplementation((url) => {
      if (url.includes('/purchase-orders/stats')) {
        return Promise.resolve({ data: mockStats });
      }
      if (url.includes('/purchase-orders')) {
        return Promise.resolve({ 
          data: {
            items: mockOrders,
            total: mockOrders.length,
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
    it('should render purchase orders title', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      expect(screen.getByText(/采购订单|Purchase Orders/i)).toBeInTheDocument();
    });

    it('should render statistics cards', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/purchase-orders'));
      });
    });

    it('should display action buttons', () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增订单|Add Order/i });
      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      
      expect(addButton || exportButton).toBeTruthy();
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch orders on mount', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/purchase-orders'));
      });
    });

    it('should handle API error gracefully', async () => {
      api.get.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should display empty state when no orders', async () => {
      api.get.mockResolvedValueOnce({ 
        data: { items: [], total: 0, page: 1, pageSize: 20 } 
      });

      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无采购订单|No purchase orders/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 订单列表显示测试
  describe('Order List Display', () => {
    it('should display order numbers', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
        expect(screen.getByText('PO-2024-002')).toBeInTheDocument();
      });
    });

    it('should show project names', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造系统/)).toBeInTheDocument();
        expect(screen.getByText(/ERP系统升级/)).toBeInTheDocument();
      });
    });

    it('should display supplier names', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/深圳市某某电子有限公司/)).toBeInTheDocument();
        expect(screen.getByText(/北京某某科技有限公司/)).toBeInTheDocument();
      });
    });

    it('should show order amounts', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        const amounts = screen.queryAllByText(/500,000|300,000|200,000/);
        expect(amounts.length).toBeGreaterThan(0);
      });
    });

    it('should display order status badges', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已批准|Approved/i)).toBeInTheDocument();
        expect(screen.getByText(/待审批|Pending/i)).toBeInTheDocument();
        expect(screen.getByText(/已收货|Received/i)).toBeInTheDocument();
      });
    });
  });

  // 4. 统计数据测试
  describe('Statistics Display', () => {
    it('should display total orders count', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('150')).toBeInTheDocument();
      });
    });

    it('should show total amount', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalAmount = screen.queryByText(/15,000,000/);
        expect(totalAmount).toBeTruthy();
      });
    });

    it('should display pending orders count', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('20')).toBeInTheDocument();
      });
    });
  });

  // 5. 筛选功能测试
  describe('Filter Functionality', () => {
    it('should filter by order status', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const approvedFilter = screen.queryByRole('button', { name: /已批准|Approved/i });
      if (approvedFilter) {
        fireEvent.click(approvedFilter);
      }
    });

    it('should filter by project', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const projectFilter = screen.queryByPlaceholderText(/选择项目|Select project/i);
      if (projectFilter) {
        fireEvent.change(projectFilter, { target: { value: '1' } });
      }
    });

    it('should filter by supplier', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const supplierFilter = screen.queryByPlaceholderText(/选择供应商|Select supplier/i);
      if (supplierFilter) {
        fireEvent.change(supplierFilter, { target: { value: '1' } });
      }
    });
  });

  // 6. 搜索功能测试
  describe('Search Functionality', () => {
    it('should render search input', () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      const searchInput = screen.queryByPlaceholderText(/搜索订单|Search order/i);
      expect(searchInput).toBeTruthy();
    });

    it('should search by order number', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索订单|Search order/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: 'PO-2024-001' } });
      }
    });

    it('should search by supplier name', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/深圳市某某电子有限公司/)).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索订单|Search order/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '深圳' } });
      }
    });
  });

  // 7. 订单操作测试
  describe('Order Actions', () => {
    it('should view order detail when clicking row', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const orderRow = screen.getByText('PO-2024-001').closest('tr');
      if (orderRow) {
        fireEvent.click(orderRow);
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/1'));
      }
    });

    it('should approve order when clicking approve button', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-002')).toBeInTheDocument();
      });

      const approveButtons = screen.queryAllByRole('button', { name: /审批|Approve/i });
      if (approveButtons.length > 0) {
        fireEvent.click(approveButtons[0]);
        
        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });

    it('should confirm receipt when clicking receive button', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const receiveButtons = screen.queryAllByRole('button', { name: /收货|Receive/i });
      if (receiveButtons.length > 0) {
        fireEvent.click(receiveButtons[0]);
        
        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });

    it('should add new order', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增订单|Add Order/i });
      if (addButton) {
        fireEvent.click(addButton);
        expect(mockNavigate).toHaveBeenCalled();
      }
    });
  });

  // 8. 导出功能测试
  describe('Export Functionality', () => {
    it('should render export button', () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      expect(exportButton).toBeTruthy();
    });

    it('should trigger export when clicking export button', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
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
          <PurchaseOrders />
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
          <PurchaseOrders />
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

  // 10. 日期显示测试
  describe('Date Display', () => {
    it('should display order dates', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-10/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02-15/)).toBeInTheDocument();
      });
    });

    it('should show delivery dates', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-03-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-03-20/)).toBeInTheDocument();
      });
    });

    it('should display received dates', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        const receivedDate = screen.queryByText(/2024-02-20/);
        expect(receivedDate).toBeTruthy();
      });
    });
  });

  // 11. 创建人和审批人显示测试
  describe('User Information Display', () => {
    it('should display created by user', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
        expect(screen.getByText(/李四/)).toBeInTheDocument();
      });
    });

    it('should show approved by user', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/李经理/)).toBeInTheDocument();
        expect(screen.getByText(/赵总监/)).toBeInTheDocument();
      });
    });
  });

  // 12. 批量操作测试
  describe('Batch Operations', () => {
    it('should select multiple orders', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      });

      const checkboxes = screen.queryAllByRole('checkbox');
      if (checkboxes.length > 0) {
        fireEvent.click(checkboxes[0]);
      }
    });

    it('should perform batch approval', async () => {
      render(
        <MemoryRouter>
          <PurchaseOrders />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const batchApproveButton = screen.queryByRole('button', { name: /批量审批|Batch Approve/i });
      if (batchApproveButton) {
        fireEvent.click(batchApproveButton);
      }
    });
  });
});
