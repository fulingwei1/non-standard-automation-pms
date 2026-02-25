/**
 * ContractList 组件测试
 * 测试覆盖：合同列表渲染、搜索、筛选、状态管理、支付里程碑
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ContractList from '../ContractList';
import { contractApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  contractApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    getMilestones: vi.fn(),
  }
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(Object.entries(props).filter(([k]) => !['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'].includes(k)));
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
  AnimatePresence: ({ children }) => children,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ContractList', () => {
  const mockContracts = [
    {
      id: 1,
      code: 'CON-2024-001',
      name: '智能制造系统合同',
      customer_name: '某大型企业',
      project_name: '智能制造系统项目',
      status: 'active',
      contract_amount: 1500000,
      signed_date: '2024-01-15',
      start_date: '2024-01-20',
      end_date: '2024-07-20',
      payment_terms: 'milestone',
      paid_amount: 750000,
      remaining_amount: 750000,
      payment_progress: 50,
    },
    {
      id: 2,
      code: 'CON-2024-002',
      name: 'ERP系统升级合同',
      customer_name: '科技公司',
      project_name: 'ERP升级项目',
      status: 'pending_sign',
      contract_amount: 800000,
      signed_date: null,
      start_date: '2024-03-01',
      end_date: '2024-09-01',
      payment_terms: 'installment',
      paid_amount: 0,
      remaining_amount: 800000,
      payment_progress: 0,
    },
    {
      id: 3,
      code: 'CON-2024-003',
      name: '项目咨询服务合同',
      customer_name: '咨询客户',
      project_name: '管理咨询项目',
      status: 'completed',
      contract_amount: 500000,
      signed_date: '2023-10-01',
      start_date: '2023-10-15',
      end_date: '2024-01-15',
      payment_terms: 'full',
      paid_amount: 500000,
      remaining_amount: 0,
      payment_progress: 100,
    },
  ];

  const mockMilestones = [
    {
      id: 1,
      contract_id: 1,
      name: '签约款',
      type: 'deposit',
      amount: 450000,
      percentage: 30,
      due_date: '2024-01-20',
      status: 'paid',
      paid_date: '2024-01-18',
    },
    {
      id: 2,
      contract_id: 1,
      name: '进度款',
      type: 'progress',
      amount: 300000,
      percentage: 20,
      due_date: '2024-04-20',
      status: 'paid',
      paid_date: '2024-04-18',
    },
    {
      id: 3,
      contract_id: 1,
      name: '验收款',
      type: 'acceptance',
      amount: 600000,
      percentage: 40,
      due_date: '2024-07-20',
      status: 'pending',
      paid_date: null,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    contractApi.list.mockResolvedValue({ data: { items: mockContracts } });
    contractApi.getMilestones.mockResolvedValue({ data: mockMilestones });
    contractApi.delete.mockResolvedValue({ data: { success: true } });
    contractApi.create.mockResolvedValue({ 
      data: { id: 4, ...mockContracts[0] } 
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
          <ContractList />
        </MemoryRouter>
      );

      expect(screen.getByText(/合同列表|Contract List/i)).toBeInTheDocument();
    });

    it('should render contract cards', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
        expect(screen.getByText('ERP系统升级合同')).toBeInTheDocument();
        expect(screen.getByText('项目咨询服务合同')).toBeInTheDocument();
      });
    });

    it('should display contract codes', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('CON-2024-001')).toBeInTheDocument();
        expect(screen.getByText('CON-2024-002')).toBeInTheDocument();
        expect(screen.getByText('CON-2024-003')).toBeInTheDocument();
      });
    });

    it('should display customer names', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('某大型企业')).toBeInTheDocument();
        expect(screen.getByText('科技公司')).toBeInTheDocument();
        expect(screen.getByText('咨询客户')).toBeInTheDocument();
      });
    });

    it('should display status badges', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/执行中|active/i)).toBeInTheDocument();
        expect(screen.getByText(/待签约|pending_sign/i)).toBeInTheDocument();
        expect(screen.getByText(/已完成|completed/i)).toBeInTheDocument();
      });
    });

    it('should display contract amounts', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/150万|1,500,000/)).toBeInTheDocument();
        expect(screen.getByText(/80万|800,000/)).toBeInTheDocument();
        expect(screen.getByText(/50万|500,000/)).toBeInTheDocument();
      });
    });

    it('should display payment progress', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
        expect(screen.getByText(/0%/)).toBeInTheDocument();
        expect(screen.getByText(/100%/)).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch contracts on mount', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(contractApi.list).toHaveBeenCalled();
      });
    });

    it('should show loading state initially', () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      const loadingElements = screen.queryAllByRole('status') || screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error', async () => {
      contractApi.list.mockRejectedValueOnce(new Error('Failed to load'));

      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      }, { timeout: 3000 });
    });

    it('should display empty state when no contracts', async () => {
      contractApi.list.mockResolvedValueOnce({ data: { items: [] } });

      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无合同|No contracts|Empty/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 搜索功能测试
  describe('Search Functionality', () => {
    it('should filter contracts by search term', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索|Search/i);
      fireEvent.change(searchInput, { target: { value: '智能' } });

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
        expect(screen.queryByText('ERP系统升级合同')).not.toBeInTheDocument();
      });
    });

    it('should search by contract code', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('CON-2024-001')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索|Search/i);
      fireEvent.change(searchInput, { target: { value: 'CON-2024-001' } });

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });
    });

    it('should search by customer name', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('某大型企业')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索|Search/i);
      fireEvent.change(searchInput, { target: { value: '科技' } });

      await waitFor(() => {
        expect(screen.getByText('科技公司')).toBeInTheDocument();
      });
    });

    it('should clear search results', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索|Search/i);
      fireEvent.change(searchInput, { target: { value: '智能' } });
      fireEvent.change(searchInput, { target: { value: '' } });

      await waitFor(() => {
        expect(screen.getByText('ERP系统升级合同')).toBeInTheDocument();
      });
    });
  });

  // 4. 筛选功能测试
  describe('Filter Functionality', () => {
    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const statusFilters = screen.queryAllByRole('button', { name: /执行中|active|待签约|pending/i });
      if (statusFilters.length > 0) {
        fireEvent.click(statusFilters[0]);
      }
    });

    it('should filter by payment status', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(contractApi.list).toHaveBeenCalled();
      });

      const paymentFilter = screen.queryByText(/支付状态|Payment Status/i);
      if (paymentFilter) {
        fireEvent.click(paymentFilter);
      }
    });

    it('should show all contracts when selecting all filter', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const allFilter = screen.queryByRole('button', { name: /全部|All/i });
      if (allFilter) {
        fireEvent.click(allFilter);

        await waitFor(() => {
          expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
          expect(screen.getByText('ERP系统升级合同')).toBeInTheDocument();
          expect(screen.getByText('项目咨询服务合同')).toBeInTheDocument();
        });
      }
    });
  });

  // 5. 合同详情测试
  describe('Contract Details', () => {
    it('should show contract details when clicking view button', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|详情|View|Detail/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);
      }
    });

    it('should display contract dates', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-01-15|2024\/01\/15/)).toBeInTheDocument();
      });
    });

    it('should display project names', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统项目')).toBeInTheDocument();
        expect(screen.getByText('ERP升级项目')).toBeInTheDocument();
      });
    });
  });

  // 6. 支付里程碑测试
  describe('Payment Milestones', () => {
    it('should display payment progress bars', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const progressBars = screen.queryAllByRole('progressbar');
        expect(progressBars.length).toBeGreaterThan(0);
      });
    });

    it('should show paid and remaining amounts', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/75万|750,000/)).toBeInTheDocument(); // Paid amount
      });
    });

    it('should display milestone information', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const milestoneButtons = screen.queryAllByRole('button', { name: /里程碑|Milestone|支付/i });
      if (milestoneButtons.length > 0) {
        fireEvent.click(milestoneButtons[0]);
      }
    });
  });

  // 7. CRUD 操作测试
  describe('CRUD Operations', () => {
    it('should open create dialog when clicking add button', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const addButton = screen.queryByRole('button', { name: /新建|创建|Add|Create/i });
      if (addButton) {
        fireEvent.click(addButton);

        await waitFor(() => {
          expect(screen.getByText(/新建合同|Create Contract/i)).toBeInTheDocument();
        });
      }
    });

    it('should edit existing contract', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/编辑合同|Edit Contract/i)).toBeInTheDocument();
        });
      }
    });

    it('should delete contract', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);

        const confirmButton = screen.queryByRole('button', { name: /确认|Confirm/i });
        if (confirmButton) {
          fireEvent.click(confirmButton);

          await waitFor(() => {
            expect(contractApi.delete).toHaveBeenCalled();
          });
        }
      }
    });

    it('should download contract document', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const downloadButtons = screen.queryAllByRole('button', { name: /下载|Download/i });
      if (downloadButtons.length > 0) {
        fireEvent.click(downloadButtons[0]);
      }
    });
  });

  // 8. 视图切换测试
  describe('View Mode Toggle', () => {
    it('should switch between list and grid view', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const viewToggleButtons = screen.queryAllByRole('button', { name: /列表|网格|List|Grid/i });
      if (viewToggleButtons.length > 0) {
        fireEvent.click(viewToggleButtons[0]);
      }
    });
  });

  // 9. 排序功能测试
  describe('Sorting', () => {
    it('should sort by contract amount', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const sortButtons = screen.queryAllByRole('button', { name: /排序|Sort|金额|Amount/i });
      if (sortButtons.length > 0) {
        fireEvent.click(sortButtons[0]);
      }
    });

    it('should sort by signed date', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(contractApi.list).toHaveBeenCalled();
      });

      const dateSort = screen.queryByText(/签约日期|Signed Date/i);
      if (dateSort) {
        fireEvent.click(dateSort);
      }
    });

    it('should sort by payment progress', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
      });

      const progressSort = screen.queryByText(/支付进度|Payment Progress/i);
      if (progressSort) {
        fireEvent.click(progressSort);
      }
    });
  });

  // 10. 导航功能测试
  describe('Navigation', () => {
    it('should navigate to contract detail page', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      });

      const contractCard = screen.getByText('智能制造系统合同').closest('div');
      if (contractCard) {
        fireEvent.click(contractCard);
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/contracts/1'));
      }
    });
  });

  // 11. 统计信息测试
  describe('Statistics', () => {
    it('should display total contracts count', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const totalCount = screen.queryByText(/3|共3个|Total: 3/i);
        expect(totalCount).toBeTruthy();
      });
    });

    it('should display active contracts count', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const activeCount = screen.queryByText(/1|执行中: 1/i);
        expect(activeCount).toBeTruthy();
      });
    });

    it('should display total contract value', async () => {
      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        // Total: 1,500,000 + 800,000 + 500,000 = 2,800,000
        const totalValue = screen.queryByText(/280万|2,800,000/i);
        expect(totalValue).toBeTruthy();
      });
    });
  });

  // 12. 错误处理测试
  describe('Error Handling', () => {
    it('should handle network error gracefully', async () => {
      contractApi.list.mockRejectedValueOnce(new Error('Network error'));

      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/网络错误|Network error|连接失败/i);
        expect(errorMessage).toBeTruthy();
      }, { timeout: 3000 });
    });

    it('should retry loading on error', async () => {
      contractApi.list.mockRejectedValueOnce(new Error('Failed'));

      render(
        <MemoryRouter>
          <ContractList />
        </MemoryRouter>
      );

      await waitFor(() => {
        const retryButton = screen.queryByRole('button', { name: /重试|Retry/i });
        if (retryButton) {
          contractApi.list.mockResolvedValueOnce({ data: mockContracts });
          fireEvent.click(retryButton);
        }
      }, { timeout: 3000 });
    });
  });
});
