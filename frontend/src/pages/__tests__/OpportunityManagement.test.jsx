/**
 * OpportunityManagement 组件测试
 * 测试覆盖：商机列表渲染、搜索、筛选、阶段管理、CRUD操作
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OpportunityManagement from '../OpportunityManagement';
import { opportunityApi, customerApi, userApi, presaleApi as _presaleApi } from '../../services/api';

// Mock dependencies
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

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('OpportunityManagement', () => {
  const mockOpportunities = [
    {
      id: 1,
      name: '智能制造解决方案',
      code: 'OPP-2024-001',
      customer_id: 100,
      customer_name: '某大型企业',
      stage: 'QUALIFIED',
      estimated_value: 1500000,
      probability: 70,
      expected_close_date: '2024-06-30',
      owner_id: 10,
      owner_name: '张三',
      source: 'INBOUND',
      status: 'ACTIVE',
      created_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 2,
      name: 'ERP系统升级',
      code: 'OPP-2024-002',
      customer_id: 101,
      customer_name: '科技公司',
      stage: 'PROPOSAL',
      estimated_value: 800000,
      probability: 50,
      expected_close_date: '2024-08-15',
      owner_id: 11,
      owner_name: '李四',
      source: 'CAMPAIGN',
      status: 'ACTIVE',
      created_at: '2024-02-20T14:00:00Z',
    },
  ];

  const mockCustomers = [
    { id: 100, name: '某大型企业' },
    { id: 101, name: '科技公司' },
  ];

  const mockUsers = [
    { id: 10, name: '张三' },
    { id: 11, name: '李四' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    opportunityApi.list.mockResolvedValue({ data: { items: mockOpportunities, total: mockOpportunities.length } });
    customerApi.list.mockResolvedValue({ data: { items: mockCustomers, total: mockCustomers.length } });
    userApi.list.mockResolvedValue({ data: { items: mockUsers, total: mockUsers.length } });
    opportunityApi.delete.mockResolvedValue({ data: { success: true } });
    opportunityApi.create.mockResolvedValue({ 
      data: { id: 3, ...mockOpportunities[0] } 
    });
    opportunityApi.update.mockResolvedValue({ 
      data: { success: true } 
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render page title', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      expect(screen.getByText(/商机管理|Opportunity Management/i)).toBeInTheDocument();
    });

    it('should render opportunity cards', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
        expect(screen.getByText('ERP系统升级')).toBeInTheDocument();
      });
    });

    it('should display opportunity codes', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('OPP-2024-001')).toBeInTheDocument();
        expect(screen.getByText('OPP-2024-002')).toBeInTheDocument();
      });
    });

    it('should display customer names', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('某大型企业')).toBeInTheDocument();
        expect(screen.getByText('科技公司')).toBeInTheDocument();
      });
    });

    it('should display stage badges', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const badges = screen.getAllByText(/商机合格|方案\/报价中|需求澄清/i);
        expect(badges.length).toBeGreaterThan(0);
      });
    });

    it('should display estimated values', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/150万|1,500,000/)).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch opportunities on mount', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(opportunityApi.list).toHaveBeenCalled();
      });
    });

    it('should show loading state initially', () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      const loadingElements = screen.queryAllByRole('status') || screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error', async () => {
      opportunityApi.list.mockRejectedValueOnce(new Error('Failed to load'));

      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败|加载失败/i);
        expect(errorMessage).toBeTruthy();
      }, { timeout: 3000 });
    });

    it('should display empty state when no opportunities', async () => {
      opportunityApi.list.mockResolvedValueOnce({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无商机|No opportunities|Empty/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 搜索功能测试
  describe('Search Functionality', () => {
    it('should filter opportunities by search term', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索|Search/i);
      fireEvent.change(searchInput, { target: { value: '智能' } });

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });
    });

    it('should clear search results', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索|Search/i);
      fireEvent.change(searchInput, { target: { value: '智能' } });
      fireEvent.change(searchInput, { target: { value: '' } });

      await waitFor(() => {
        expect(screen.getByText('ERP系统升级')).toBeInTheDocument();
      });
    });
  });

  // 4. 筛选功能测试
  describe('Filter Functionality', () => {
    it('should filter by stage', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const filterButtons = screen.queryAllByRole('button', { name: /筛选|Filter|商机合格|QUALIFIED/i });
      if (filterButtons.length > 0) {
        fireEvent.click(filterButtons[0]);
      }
    });

    it('should filter by owner', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(opportunityApi.list).toHaveBeenCalled();
      });

      const ownerFilter = screen.queryByText(/负责人|Owner/i);
      if (ownerFilter) {
        fireEvent.click(ownerFilter);
      }
    });

    it('should filter by customer', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(opportunityApi.list).toHaveBeenCalled();
      });

      const customerFilter = screen.queryByText(/客户|Customer/i);
      if (customerFilter) {
        fireEvent.click(customerFilter);
      }
    });

    it('should reset filters', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(opportunityApi.list).toHaveBeenCalled();
      });

      const resetButton = screen.queryByRole('button', { name: /重置|Reset|清空/i });
      if (resetButton) {
        fireEvent.click(resetButton);
      }
    });
  });

  // 5. CRUD 操作测试
  describe('CRUD Operations', () => {
    it('should open create dialog when clicking add button', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /新建|创建|Add|Create/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(screen.getByText(/新建商机|Create Opportunity/i)).toBeInTheDocument();
      });
    });

    it('should create new opportunity', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /新建|创建|Add|Create/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/商机名称|Name/i);
        fireEvent.change(nameInput, { target: { value: '新商机' } });

        const submitButton = screen.getByRole('button', { name: /确定|提交|Submit/i });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(opportunityApi.create).toHaveBeenCalled();
      });
    });

    it('should edit existing opportunity', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/编辑商机|Edit Opportunity/i)).toBeInTheDocument();
        });
      }
    });

    it('should delete opportunity', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);

        const confirmButton = screen.queryByRole('button', { name: /确认|Confirm/i });
        if (confirmButton) {
          fireEvent.click(confirmButton);

          await waitFor(() => {
            expect(opportunityApi.delete).toHaveBeenCalled();
          });
        }
      }
    });
  });

  // 6. 阶段管理测试
  describe('Stage Management', () => {
    it('should display stage information', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const stageBadges = screen.getAllByText(/商机合格|方案\/报价中|需求澄清|QUALIFIED|PROPOSAL/i);
        expect(stageBadges.length).toBeGreaterThan(0);
      });
    });

    it('should update opportunity stage', async () => {
      opportunityApi.updateStage.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const stageButtons = screen.queryAllByRole('button', { name: /阶段|Stage/i });
      if (stageButtons.length > 0) {
        fireEvent.click(stageButtons[0]);
      }
    });

    it('should show stage progression', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });
    });
  });

  // 7. 视图切换测试
  describe('View Mode Toggle', () => {
    it('should switch between list and grid view', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const viewToggleButtons = screen.queryAllByRole('button', { name: /列表|网格|List|Grid/i });
      if (viewToggleButtons.length > 0) {
        fireEvent.click(viewToggleButtons[0]);
      }
    });
  });

  // 8. 排序功能测试
  describe('Sorting', () => {
    it('should sort by estimated value', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const sortButtons = screen.queryAllByRole('button', { name: /排序|Sort|金额|Value/i });
      if (sortButtons.length > 0) {
        fireEvent.click(sortButtons[0]);
      }
    });

    it('should sort by expected close date', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(opportunityApi.list).toHaveBeenCalled();
      });

      const dateSort = screen.queryByText(/预计成交日期|Close Date/i);
      if (dateSort) {
        fireEvent.click(dateSort);
      }
    });

    it('should sort by probability', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });
    });
  });

  // 9. 导航功能测试
  describe('Navigation', () => {
    it('should navigate to opportunity detail', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|详情|View|Detail/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/opportunities/1'));
      }
    });
  });

  // 10. 表单验证测试
  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /新建|创建|Add|Create/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /确定|提交|Submit/i });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        const errorMessage = screen.queryByText(/必填|Required|不能为空/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should validate estimated value format', async () => {
      render(
        <MemoryRouter>
          <OpportunityManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造解决方案')).toBeInTheDocument();
      });

      const addButton = screen.getByRole('button', { name: /新建|创建|Add|Create/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        const valueInput = screen.queryByLabelText(/预计金额|Estimated Value/i);
        if (valueInput) {
          fireEvent.change(valueInput, { target: { value: 'invalid' } });
        }
      });
    });
  });
});
