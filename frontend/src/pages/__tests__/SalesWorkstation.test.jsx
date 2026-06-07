import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SalesWorkstation from '../SalesWorkstation';

const mockNavigate = vi.fn();
const mockRefetch = vi.fn();

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('../../hooks/useSalesWorkstation', () => ({
  useSalesWorkstationData: () => ({
    loading: false,
    refetch: mockRefetch,
    data: {
      followUpSummary: {
        total_count: 6,
        by_urgency: { overdue: { count: 2 } },
      },
      collectionSummary: {
        total_count: 4,
        critical_count: 1,
        total_overdue_amount: 380000,
      },
      healthSummary: {
        average_score: 62,
        by_level: { critical: { count: 3 } },
      },
      milestoneSummary: {
        total_count: 5,
        by_urgency: {
          overdue: { count: 1 },
          urgent: { count: 2 },
        },
      },
      salesFunnelSummary: {
        leads: 2,
        opportunities: 3,
        quotes: 4,
        contracts: 5,
        total_contract_amount: 120000,
      },
      initiationSummary: {
        unique_count: 6,
      },
    },
  }),
  useFollowUpReminders: () => ({
    data: {
      items: [
        {
          entity_type: 'lead',
          entity_id: 21,
          entity_name: '华东线索A',
          entity_code: 'L-2026-001',
          reminder_type: 'overdue',
          urgency: 'overdue',
          next_follow_date: '2026-06-05',
          days_overdue: 2,
          suggestion: '补充需求并安排拜访',
        },
        {
          entity_type: 'opportunity',
          entity_id: 32,
          entity_name: '视觉检测商机',
          entity_code: 'OP-2026-032',
          reminder_type: 'stage_push',
          urgency: 'urgent',
          next_follow_date: '2026-06-08',
          days_until: 1,
          suggestion: '推动技术方案确认',
        },
      ],
    },
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useCollectionPriority: () => ({
    data: {
      items: [
        {
          invoice_id: 7,
          customer_id: 12,
          contract_id: 34,
          customer_name: '金凯博',
          contract_code: 'HT-2026-001',
          overdue_amount: 380000,
          days_overdue: 35,
          priority_level: 'critical',
          priority_score: 82,
          suggestion: '立即催收',
        },
      ],
    },
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useOpportunityHealthList: () => ({
    data: {
      items: [
        {
          opportunity_id: 55,
          opportunity_name: '装配线商机',
          opportunity_code: 'OP-2026-055',
          customer_name: '蓝海科技',
          stage: '方案确认',
          total_score: 48,
          health_level: 'warning',
          est_amount: 1260000,
          key_issues: ['超过 14 天未更新报价'],
          top_suggestions: ['尽快确认报价版本'],
        },
      ],
    },
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useContractMilestones: () => ({
    data: {
      items: [
        {
          contract_id: 77,
          contract_name: '整线自动化合同',
          contract_code: 'HT-2026-077',
          customer_name: '星河装备',
          milestone_name: '预付款到账',
          milestone_type: 'payment',
          due_date: '2026-06-09',
          days_until: 2,
          urgency: 'urgent',
          amount: 280000,
          suggestion: '确认客户付款计划',
        },
      ],
    },
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

describe('SalesWorkstation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.getComputedStyle = vi.fn(() => ({
      getPropertyValue: () => '',
    }));
  });

  it('首屏展示销售闭环阶段和今日行动入口', async () => {
    const user = userEvent.setup();

    render(<SalesWorkstation />);

    expect(screen.getByText('今日销售动作')).toBeInTheDocument();
    expect(screen.getByText('线索')).toBeInTheDocument();
    expect(screen.getByText('商机')).toBeInTheDocument();
    expect(screen.getByText('报价')).toBeInTheDocument();
    expect(screen.getByText('合同')).toBeInTheDocument();
    expect(screen.getByText('项目立项')).toBeInTheDocument();
    expect(screen.getByLabelText('线索数量 2')).toBeInTheDocument();
    expect(screen.getByLabelText('商机数量 3')).toBeInTheDocument();
    expect(screen.getByLabelText('报价数量 4')).toBeInTheDocument();
    expect(screen.getByLabelText('合同数量 5')).toBeInTheDocument();
    expect(screen.getByLabelText('项目立项数量 6')).toBeInTheDocument();

    expect(screen.getByRole('button', { name: '处理待跟进' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '推进报价' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '跟进合同' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '催收回款' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '推进报价' }));

    expect(mockNavigate).toHaveBeenCalledWith('/sales/quotes');

    await user.click(screen.getByRole('button', { name: '催收回款' }));

    expect(mockNavigate).toHaveBeenCalledWith(
      '/sales/receivables?source=sales_workstation&view=overdue_receivables&overdue_only=true'
    );
  });

  it('催款列表可以下钻到客户合同应收明细', async () => {
    const user = userEvent.setup();

    render(<SalesWorkstation />);

    await user.click(screen.getByText(/催款管理/));
    await user.click(await screen.findByRole('button', { name: '查看应收' }));

    expect(mockNavigate).toHaveBeenCalledWith(
      '/sales/receivables?source=sales_workstation&view=collection_risk&overdue_only=true&customer_id=12&contract_id=34'
    );
  });

  it('跟进提醒可以直接进入线索或商机处理页', async () => {
    const user = userEvent.setup();

    render(<SalesWorkstation />);

    await user.click(
      await screen.findByRole('button', { name: '查看线索 华东线索A' })
    );

    expect(mockNavigate).toHaveBeenCalledWith('/sales/leads/21');

    await user.click(
      await screen.findByRole('button', { name: '查看商机 视觉检测商机' })
    );

    expect(mockNavigate).toHaveBeenCalledWith('/sales/opportunities/32');
  });

  it('跟进提醒可以直接进入线索或商机技术评估页', async () => {
    const user = userEvent.setup();

    render(<SalesWorkstation />);

    await user.click(
      await screen.findByRole('button', { name: '技术评估 华东线索A' })
    );

    expect(mockNavigate).toHaveBeenCalledWith('/sales/assessments/lead/21');

    await user.click(
      await screen.findByRole('button', { name: '技术评估 视觉检测商机' })
    );

    expect(mockNavigate).toHaveBeenCalledWith('/sales/assessments/opportunity/32');
  });

  it('商机健康和合同里程碑可以直接下钻到业务详情', async () => {
    const user = userEvent.setup();

    render(<SalesWorkstation />);

    await user.click(screen.getByRole('tab', { name: /商机健康/ }));
    await user.click(
      await screen.findByRole('button', { name: '查看商机 装配线商机' })
    );

    expect(mockNavigate).toHaveBeenCalledWith('/sales/opportunities/55');

    await user.click(screen.getByRole('tab', { name: /合同里程碑/ }));
    await user.click(
      await screen.findByRole('button', { name: '查看合同 整线自动化合同' })
    );

    expect(mockNavigate).toHaveBeenCalledWith('/sales/contracts/77');
  });
});
