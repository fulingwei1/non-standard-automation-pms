import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SalesStatistics from './SalesStatistics';
import { salesStatisticsApi } from '../services/api';

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const filtered = Object.fromEntries(
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
        const Tag = typeof tag === 'string' ? tag : 'div';
        return <Tag {...filtered}>{children}</Tag>;
      },
    },
  ),
}));

vi.mock('../components/ui', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    DropdownMenu: ({ children }) => <div>{children}</div>,
    DropdownMenuTrigger: ({ children }) => <>{children}</>,
    DropdownMenuContent: ({ children }) => <div>{children}</div>,
    DropdownMenuItem: ({ children, onClick }) => (
      <button type="button" onClick={onClick}>
        {children}
      </button>
    ),
  };
});

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    salesStatisticsApi: {
      ...actual.salesStatisticsApi,
      funnel: vi.fn(),
      revenueForecast: vi.fn(),
      opportunitiesByStage: vi.fn(),
      summary: vi.fn(),
    },
  };
});

function renderPage() {
  return render(
    <MemoryRouter>
      <SalesStatistics />
    </MemoryRouter>,
  );
}

describe('SalesStatistics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    salesStatisticsApi.funnel.mockResolvedValue({
      data: {
        data: {
          leads: 150,
          opportunities: 80,
          quotes: 45,
          contracts: 20,
          total_opportunity_amount: 3500000,
          total_contract_amount: 2200000,
        },
      },
    });
    salesStatisticsApi.revenueForecast.mockResolvedValue({
      data: {
        data: {
          confirmed_amount: 800000,
          forecast: [
            { month: '2026-04', estimated_revenue: 300000 },
            { month: '2026-05', estimated_revenue: 500000 },
          ],
        },
      },
    });
    salesStatisticsApi.opportunitiesByStage.mockResolvedValue({
      data: {
        data: {
          DISCOVERY: { count: 10, total_amount: 1000000 },
          PROPOSAL: { count: 5, total_amount: 600000 },
          WON: { count: 2, total_amount: 500000 },
        },
      },
    });
    salesStatisticsApi.summary.mockResolvedValue({
      data: {
        data: {
          total_leads: 150,
          converted_leads: 30,
          total_opportunities: 80,
          won_opportunities: 12,
          total_contract_amount: 2200000,
          paid_amount: 1200000,
          conversion_rate: 20,
          win_rate: 15,
        },
      },
    });
  });

  it('renders the real page and loads all statistics APIs', async () => {
    renderPage();

    expect(screen.getByText('销售统计')).toBeInTheDocument();
    expect(screen.getByText('销售数据分析与报表')).toBeInTheDocument();

    await waitFor(() => {
      expect(salesStatisticsApi.funnel).toHaveBeenCalled();
      expect(salesStatisticsApi.revenueForecast).toHaveBeenCalledWith({ months: 3 });
      expect(salesStatisticsApi.opportunitiesByStage).toHaveBeenCalled();
      expect(salesStatisticsApi.summary).toHaveBeenCalled();
    });

    expect(screen.getByText('线索总数')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('销售漏斗')).toBeInTheDocument();
    expect(screen.getByText('商机阶段分布')).toBeInTheDocument();
    expect(screen.getByText('收入预测')).toBeInTheDocument();
    expect(screen.getByText('成交率')).toBeInTheDocument();
    expect(screen.getByText('30 已转化')).toBeInTheDocument();
  });

  it('reloads statistics when switching time range', async () => {
    renderPage();

    await waitFor(() => {
      expect(salesStatisticsApi.funnel).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByRole('button', { name: '本季度' }));

    await waitFor(() => {
      expect(salesStatisticsApi.funnel).toHaveBeenCalledTimes(2);
    });
  });

  it('keeps the page rendered when summary API fails and falls back to funnel data', async () => {
    salesStatisticsApi.summary.mockRejectedValueOnce(new Error('summary failed'));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('销售统计')).toBeInTheDocument();
      expect(screen.getByText('线索总数')).toBeInTheDocument();
    });
  });
});
