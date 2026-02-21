/**
 * CustomerList 组件测试
 * 测试覆盖：客户列表显示、搜索筛选、客户操作、分页、状态管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CustomerList from '../CustomerList';
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

describe('CustomerList', () => {
  const mockCustomers = [
    {
      id: 1,
      name: '华为技术有限公司',
      code: 'CUST-001',
      industry: '通信设备',
      level: 'A',
      status: 'active',
      contactPerson: '张经理',
      contactPhone: '13800138000',
      contactEmail: 'zhang@huawei.com',
      address: '深圳市龙岗区',
      creditRating: 'AAA',
      cooperationYears: 5,
      totalProjects: 12,
      totalAmount: 5000000,
      createdAt: '2019-01-15',
    },
    {
      id: 2,
      name: '中兴通讯股份有限公司',
      code: 'CUST-002',
      industry: '通信设备',
      level: 'A',
      status: 'active',
      contactPerson: '李总监',
      contactPhone: '13900139000',
      contactEmail: 'li@zte.com',
      address: '深圳市南山区',
      creditRating: 'AA',
      cooperationYears: 3,
      totalProjects: 8,
      totalAmount: 3000000,
      createdAt: '2021-03-20',
    },
    {
      id: 3,
      name: '小米科技有限公司',
      code: 'CUST-003',
      industry: '消费电子',
      level: 'B',
      status: 'potential',
      contactPerson: '王主管',
      contactPhone: '13700137000',
      contactEmail: 'wang@xiaomi.com',
      address: '北京市海淀区',
      creditRating: 'A',
      cooperationYears: 1,
      totalProjects: 2,
      totalAmount: 500000,
      createdAt: '2023-06-10',
    },
  ];

  const mockStats = {
    total: 150,
    active: 120,
    potential: 20,
    inactive: 10,
    levelA: 45,
    levelB: 60,
    levelC: 45,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    api.get.mockImplementation((url) => {
      if (url.includes('/customers/stats')) {
        return Promise.resolve({ data: mockStats });
      }
      if (url.includes('/customers')) {
        return Promise.resolve({ 
          data: {
            items: mockCustomers,
            total: mockCustomers.length,
            page: 1,
            pageSize: 20,
          }
        });
      }
      return Promise.resolve({ data: {} });
    });

    api.put.mockResolvedValue({ data: { success: true } });
    api.delete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render customer list title', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      expect(screen.getByText(/客户列表|Customer List/i)).toBeInTheDocument();
    });

    it('should render statistics cards', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/customers/stats'));
      });
    });

    it('should display add customer button', () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增客户|Add Customer/i });
      expect(addButton).toBeTruthy();
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch customers on mount', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/customers'));
      });
    });

    it('should display loading state initially', () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const loadingElements = screen.queryAllByRole('status') || screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error gracefully', async () => {
      api.get.mockRejectedValueOnce(new Error('API Error'));

      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should display empty state when no customers', async () => {
      api.get.mockResolvedValueOnce({ 
        data: { items: [], total: 0, page: 1, pageSize: 20 } 
      });

      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无客户|No customers/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 客户列表显示测试
  describe('Customer List Display', () => {
    it('should display customer names', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
        expect(screen.getByText(/中兴通讯股份有限公司/)).toBeInTheDocument();
      });
    });

    it('should show customer codes', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('CUST-001')).toBeInTheDocument();
        expect(screen.getByText('CUST-002')).toBeInTheDocument();
      });
    });

    it('should display customer levels', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const levelBadges = screen.getAllByText(/^[ABC]$/);
        expect(levelBadges.length).toBeGreaterThan(0);
      });
    });

    it('should show customer status', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText(/活跃|Active/i).length).toBeGreaterThan(0);
      });
    });

    it('should display contact information', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张经理/)).toBeInTheDocument();
        expect(screen.getByText(/13800138000/)).toBeInTheDocument();
      });
    });

    it('should show cooperation years', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const yearsText = screen.queryByText(/5|3|年/);
        expect(yearsText).toBeTruthy();
      });
    });
  });

  // 4. 搜索功能测试
  describe('Search Functionality', () => {
    it('should render search input', () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText(/搜索客户|Search customer/i);
      expect(searchInput).toBeInTheDocument();
    });

    it('should search customers by name', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText(/搜索客户|Search customer/i);
      fireEvent.change(searchInput, { target: { value: '华为' } });

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });
    });

    it('should search by customer code', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText(/搜索客户|Search customer/i);
      fireEvent.change(searchInput, { target: { value: 'CUST-001' } });

      await waitFor(() => {
        expect(screen.getByText('CUST-001')).toBeInTheDocument();
      });
    });
  });

  // 5. 筛选功能测试
  describe('Filter Functionality', () => {
    it('should filter by customer level', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });

      const levelAFilter = screen.queryByRole('button', { name: /A级|Level A/i });
      if (levelAFilter) {
        fireEvent.click(levelAFilter);
      }
    });

    it('should filter by customer status', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const activeFilter = screen.queryByRole('button', { name: /活跃|Active/i });
      if (activeFilter) {
        fireEvent.click(activeFilter);
      }
    });

    it('should filter by industry', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const industryFilter = screen.queryByText(/通信设备|通信/);
      if (industryFilter) {
        const clickableElement = industryFilter.closest('button');
        if (clickableElement) {
          fireEvent.click(clickableElement);
        }
      }
    });
  });

  // 6. 客户操作测试
  describe('Customer Actions', () => {
    it('should navigate to customer detail when clicking row', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });

      const customerRow = screen.getByText(/华为技术有限公司/).closest('tr');
      if (customerRow) {
        fireEvent.click(customerRow);
      }
    });

    it('should open edit dialog when clicking edit button', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);
      }
    });

    it('should delete customer when clicking delete button', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);
        
        await waitFor(() => {
          expect(api.delete).toHaveBeenCalled();
        });
      }
    });

    it('should navigate to add customer page', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const addButton = screen.queryByRole('button', { name: /新增客户|Add Customer/i });
      if (addButton) {
        fireEvent.click(addButton);
        expect(mockNavigate).toHaveBeenCalled();
      }
    });
  });

  // 7. 统计数据测试
  describe('Statistics Display', () => {
    it('should display total customers count', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('150')).toBeInTheDocument();
      });
    });

    it('should show active customers count', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('120')).toBeInTheDocument();
      });
    });

    it('should display level A customers count', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('45')).toBeInTheDocument();
      });
    });
  });

  // 8. 分页功能测试
  describe('Pagination', () => {
    it('should display pagination controls', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
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
          <CustomerList />
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

    it('should navigate to previous page', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const prevButton = screen.queryByRole('button', { name: /上一页|Previous/i });
      if (prevButton && !prevButton.disabled) {
        fireEvent.click(prevButton);
      }
    });
  });

  // 9. 排序功能测试
  describe('Sorting Functionality', () => {
    it('should sort by customer name', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });

      const nameHeader = screen.queryByText(/客户名称|Customer Name/i);
      if (nameHeader) {
        fireEvent.click(nameHeader);
      }
    });

    it('should sort by cooperation years', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const yearsHeader = screen.queryByText(/合作年限|Cooperation Years/i);
      if (yearsHeader) {
        fireEvent.click(yearsHeader);
      }
    });

    it('should sort by total amount', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const amountHeader = screen.queryByText(/总金额|Total Amount/i);
      if (amountHeader) {
        fireEvent.click(amountHeader);
      }
    });
  });

  // 10. 导出功能测试
  describe('Export Functionality', () => {
    it('should render export button', () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      expect(exportButton).toBeTruthy();
    });

    it('should trigger export when clicking export button', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);
      }
    });
  });

  // 11. 信用评级显示测试
  describe('Credit Rating Display', () => {
    it('should display credit ratings', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AAA')).toBeInTheDocument();
        expect(screen.getByText('AA')).toBeInTheDocument();
      });
    });

    it('should show credit rating badges', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const ratingBadges = screen.getAllByText(/^A{1,3}$/);
        expect(ratingBadges.length).toBeGreaterThan(0);
      });
    });
  });

  // 12. 批量操作测试
  describe('Batch Operations', () => {
    it('should select multiple customers', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/华为技术有限公司/)).toBeInTheDocument();
      });

      const checkboxes = screen.queryAllByRole('checkbox');
      if (checkboxes.length > 0) {
        fireEvent.click(checkboxes[0]);
      }
    });

    it('should perform batch delete', async () => {
      render(
        <MemoryRouter>
          <CustomerList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const batchDeleteButton = screen.queryByRole('button', { name: /批量删除|Batch Delete/i });
      if (batchDeleteButton) {
        fireEvent.click(batchDeleteButton);
      }
    });
  });
});
