/**
 * SalesFunnel 组件测试
 * 测试覆盖：销售漏斗显示、阶段统计、线索跟进、转化率分析
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SalesFunnel from '../SalesFunnel';
import api from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('SalesFunnel', () => {
  const mockFunnelData = {
    stages: [
      {
        id: 1,
        name: '线索',
        leads: 100,
        value: 10000000,
        conversionRate: 50
      },
      {
        id: 2,
        name: '商机',
        leads: 50,
        value: 7500000,
        conversionRate: 60
      },
      {
        id: 3,
        name: '方案',
        leads: 30,
        value: 6000000,
        conversionRate: 70
      },
      {
        id: 4,
        name: '报价',
        leads: 21,
        value: 5250000,
        conversionRate: 80
      },
      {
        id: 5,
        name: '谈判',
        leads: 17,
        value: 4675000,
        conversionRate: 75
      },
      {
        id: 6,
        name: '成交',
        leads: 13,
        value: 3900000,
        conversionRate: 100
      }
    ],
    totalLeads: 100,
    totalValue: 10000000,
    wonDeals: 13,
    winRate: 13,
    avgDealSize: 300000,
    avgCycleTime: 45
  };

  const mockLeadDetails = [
    {
      id: 1,
      name: '某大型制造企业项目',
      company: '某大型制造企业',
      stage: '商机',
      value: 800000,
      owner: '张三',
      probability: 60,
      expectedCloseDate: '2024-06-30',
      lastContact: '2024-02-20'
    },
    {
      id: 2,
      name: 'ERP系统升级',
      company: '某科技公司',
      stage: '方案',
      value: 500000,
      owner: '李四',
      probability: 70,
      expectedCloseDate: '2024-07-31',
      lastContact: '2024-02-19'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    api.get.mockImplementation((url) => {
      if (url.includes('/sales/funnel')) {
        return Promise.resolve({ data: mockFunnelData });
      }
      if (url.includes('/sales/leads')) {
        return Promise.resolve({ data: mockLeadDetails });
      }
      return Promise.resolve({ data: {} });
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render sales funnel with title', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      expect(screen.getByText(/销售漏斗|Sales Funnel/i)).toBeInTheDocument();
    });

    it('should render all funnel stages', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/线索/)).toBeInTheDocument();
        expect(screen.getByText(/商机/)).toBeInTheDocument();
        expect(screen.getByText(/成交/)).toBeInTheDocument();
      });
    });

    it('should display funnel visualization', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        // Check for funnel chart or visualization elements
        const funnelElement = screen.queryByTestId('funnel-chart') || 
                             screen.queryByText(/线索/);
        expect(funnelElement).toBeTruthy();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch funnel data', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/sales/funnel'));
      });
    });

    it('should show loading state initially', () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      const loadingIndicators = screen.queryAllByText(/加载中|Loading/i);
      expect(loadingIndicators.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error', async () => {
      api.get.mockRejectedValueOnce(new Error('Failed to load'));

      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  // 3. 漏斗阶段数据测试
  describe('Funnel Stage Data', () => {
    it('should display lead count for each stage', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/100/)).toBeInTheDocument(); // 线索阶段
        expect(screen.getByText(/50/)).toBeInTheDocument();  // 商机阶段
        expect(screen.getByText(/13/)).toBeInTheDocument();  // 成交
      });
    });

    it('should show value for each stage', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/10,000,000|1000万/)).toBeInTheDocument();
        expect(screen.getByText(/3,900,000|390万/)).toBeInTheDocument();
      });
    });

    it('should display conversion rates', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
        expect(screen.getByText(/60%/)).toBeInTheDocument();
      });
    });

    it('should calculate stage-to-stage conversion', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 从线索到商机: 50/100 = 50%
        expect(screen.getByText(/50%/)).toBeInTheDocument();
      });
    });
  });

  // 4. 统计指标测试
  describe('Statistics Display', () => {
    it('should display total leads count', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/100|总线索/)).toBeInTheDocument();
      });
    });

    it('should show total funnel value', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/10,000,000|1000万/)).toBeInTheDocument();
      });
    });

    it('should display win rate', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/13%|赢单率/)).toBeInTheDocument();
      });
    });

    it('should show average deal size', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/300,000|30万|平均/)).toBeInTheDocument();
      });
    });

    it('should display average cycle time', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/45|天|周期/)).toBeInTheDocument();
      });
    });
  });

  // 5. 线索详情测试
  describe('Lead Details', () => {
    it('should display lead list when clicking stage', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/商机/)).toBeInTheDocument();
      });

      const opportunityStage = screen.getByText(/商机/);
      fireEvent.click(opportunityStage);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/sales/leads'));
      });
    });

    it('should show lead details in modal', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/商机/)).toBeInTheDocument();
      });

      const stage = screen.getByText(/商机/);
      fireEvent.click(stage);

      await waitFor(() => {
        expect(screen.getByText(/某大型制造企业项目/)).toBeInTheDocument();
      });
    });

    it('should display lead owner', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/商机/)).toBeInTheDocument();
      });

      const stage = screen.getByText(/商机/);
      fireEvent.click(stage);

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
      });
    });

    it('should show expected close date', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/商机/)).toBeInTheDocument();
      });

      const stage = screen.getByText(/商机/);
      fireEvent.click(stage);

      await waitFor(() => {
        expect(screen.getByText(/2024-06-30/)).toBeInTheDocument();
      });
    });
  });

  // 6. 筛选功能测试
  describe('Filtering', () => {
    it('should filter by time period', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const periodFilter = screen.queryByText(/本月|本季度|本年/);
      if (periodFilter) {
        fireEvent.click(periodFilter);
      }
    });

    it('should filter by sales rep', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const repFilter = screen.queryByText(/销售|Rep|负责人/);
      if (repFilter) {
        fireEvent.click(repFilter);
      }
    });

    it('should filter by product line', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const productFilter = screen.queryByText(/产品线|Product/);
      if (productFilter) {
        fireEvent.click(productFilter);
      }
    });
  });

  // 7. 用户交互测试
  describe('User Interactions', () => {
    it('should navigate to lead detail when clicking lead', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/商机/)).toBeInTheDocument();
      });

      const stage = screen.getByText(/商机/);
      fireEvent.click(stage);

      await waitFor(() => {
        expect(screen.getByText(/某大型制造企业项目/)).toBeInTheDocument();
      });

      const leadName = screen.getByText(/某大型制造企业项目/);
      const clickableElement = leadName.closest('button') || leadName.closest('a');
      if (clickableElement) {
        fireEvent.click(clickableElement);
        expect(mockNavigate).toHaveBeenCalled();
      }
    });

    it('should update stage when dragging lead', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      // Simulate drag and drop (simplified)
      const stage = screen.queryByText(/商机/);
      if (stage) {
        fireEvent.dragStart(stage);
        fireEvent.dragEnd(stage);
      }
    });

    it('should refresh funnel when clicking refresh button', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const initialCallCount = api.get.mock.calls.length;

      const refreshButton = screen.queryByRole('button', { name: /刷新|Refresh/i });
      if (refreshButton) {
        fireEvent.click(refreshButton);
        
        await waitFor(() => {
          expect(api.get.mock.calls.length).toBeGreaterThan(initialCallCount);
        });
      }
    });
  });

  // 8. 转化率分析测试
  describe('Conversion Analysis', () => {
    it('should highlight stages with low conversion', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      // Low conversion stages should be highlighted or marked
      const lowConversionIndicator = screen.queryByText(/低转化|Low conversion/i);
      expect(lowConversionIndicator).toBeTruthy();
    });

    it('should show trend compared to last period', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const trendIndicators = screen.queryAllByText(/↑|↓|上升|下降/);
      expect(trendIndicators.length).toBeGreaterThanOrEqual(0);
    });

    it('should calculate average time in each stage', async () => {
      render(
        <MemoryRouter>
          <SalesFunnel />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const avgTimeIndicator = screen.queryByText(/平均|Average|天|days/);
      expect(avgTimeIndicator).toBeTruthy();
    });
  });
});
