import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import OpportunityManagement from '../OpportunityManagement';
import {
  opportunityApi,
  customerApi,
  userApi,
  presaleApi,
  presaleWorkbenchApi,
} from '../../services/api';

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

vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    opportunityApi: {
      ...actual.opportunityApi,
      list: vi.fn(),
      get: vi.fn(),
      update: vi.fn(),
      create: vi.fn(),
      submitGate: vi.fn(),
    },
    customerApi: {
      ...actual.customerApi,
      list: vi.fn(),
    },
    userApi: {
      ...actual.userApi,
      list: vi.fn(),
    },
    presaleApi: {
      ...actual.presaleApi,
      tickets: {
        list: vi.fn(),
        create: vi.fn(),
      },
    },
    presaleWorkbenchApi: {
      ...actual.presaleWorkbenchApi,
      loadContext: vi.fn(),
    },
  };
});

vi.mock('../OpportunityManagement/CreateDialog', () => ({
  default: ({ open }) => <div data-testid="create-dialog">{open ? 'open' : 'closed'}</div>,
}));

vi.mock('../OpportunityManagement/GateDialog', () => ({
  default: ({ open }) => <div data-testid="gate-dialog">{open ? 'open' : 'closed'}</div>,
}));

vi.mock('../OpportunityManagement/DetailDialog', () => ({
  default: ({ open, selectedOpp }) => (
    <div data-testid="detail-dialog">
      {open ? selectedOpp?.opp_name || 'open' : 'closed'}
    </div>
  ),
}));

vi.mock('../OpportunityManagement/ReviewDialog', () => ({
  default: ({ open, reviewForm, setReviewForm, onCreateReviewTicket, onTicketTypeChange }) => (
    <div data-testid="review-dialog">
      {open ? (
        <>
          <span>{reviewForm.title}</span>
          <select
            aria-label="支持类型"
            value={reviewForm.ticket_type}
            onChange={(event) =>
              onTicketTypeChange
                ? onTicketTypeChange(event.target.value)
                : setReviewForm({ ...reviewForm, ticket_type: event.target.value })
            }
          >
            <option value="TECHNICAL_SUPPORT">售前支持</option>
            <option value="FEASIBILITY_ASSESSMENT">技术评估</option>
            <option value="SOLUTION_REVIEW">方案评审</option>
          </select>
          <button type="button" onClick={onCreateReviewTicket}>
            提交支持
          </button>
        </>
      ) : 'closed'}
    </div>
  ),
}));

function renderPage(props = {}) {
  return render(
    <MemoryRouter>
      <OpportunityManagement {...props} />
    </MemoryRouter>,
  );
}

describe('OpportunityManagement', () => {
  const opportunities = [
    {
      id: 1,
      opp_code: 'OPP-001',
      opp_name: '智能制造升级项目',
      customer_id: 101,
      customer_name: '某大型企业',
      owner_name: '张三',
      stage: 'DISCOVERY',
      project_type: '自动化测试线',
      equipment_type: 'FCT',
      est_amount: 1200000,
      probability: 65,
      created_at: '2026-04-01T10:00:00Z',
      gate_status: 'PASS',
      requirement: {
        product_object: '动力电池模组',
        ct_seconds: 12,
        interface_desc: 'MES 对接',
        site_constraints: '三班倒不停线',
        acceptance_criteria: 'UPH 达标',
      },
    },
    {
      id: 2,
      opp_code: 'OPP-002',
      opp_name: 'ERP 改造项目',
      lead_id: 2026,
      customer_id: 102,
      customer_name: '科技公司',
      owner_name: '李四',
      stage: 'PROPOSAL',
      est_amount: 800000,
      probability: 45,
      created_at: '2026-04-02T10:00:00Z',
      gate_status: 'FAIL',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    window.alert = vi.fn();
    opportunityApi.list.mockResolvedValue({
      data: { items: opportunities, total: opportunities.length },
    });
    customerApi.list.mockResolvedValue({
      data: {
        items: [
          { id: 101, customer_name: '某大型企业' },
          { id: 102, customer_name: '科技公司' },
        ],
      },
    });
    userApi.list.mockResolvedValue({
      data: {
        items: [
          { id: 201, real_name: '张三' },
          { id: 202, real_name: '李四' },
        ],
      },
      formatted: {
        items: [
          { id: 201, real_name: '张三' },
          { id: 202, real_name: '李四' },
        ],
      },
    });
    opportunityApi.get.mockResolvedValue({ data: opportunities[0] });
    opportunityApi.update.mockResolvedValue({ data: { ...opportunities[0], stage: 'WON' } });
    presaleApi.tickets.list.mockResolvedValue({ data: { items: [], total: 0 } });
    presaleApi.tickets.create.mockResolvedValue({ data: { id: 501 } });
    presaleWorkbenchApi.loadContext.mockResolvedValue({ ticket: null });
  });

  it('renders the real page skeleton and loads opportunities on mount', async () => {
    renderPage();

    expect(screen.getByText('商机管理')).toBeInTheDocument();
    expect(screen.getByText('管理销售商机，跟踪项目进展')).toBeInTheDocument();

    await waitFor(() => {
      expect(opportunityApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 1,
          page_size: 20,
          keyword: undefined,
          stage: undefined,
        }),
      );
    });

    expect(screen.getByText('总商机数')).toBeInTheDocument();
    expect(screen.getByText('销售漏斗概览')).toBeInTheDocument();
    expect(screen.getByText('智能制造升级项目')).toBeInTheDocument();
    expect(screen.getByText('ERP 改造项目')).toBeInTheDocument();
    expect(screen.getByDisplayValue('需求澄清')).toBeInTheDocument();
  });

  it('supports search and stage updates against the current implementation', async () => {
    renderPage();

    await screen.findByText('智能制造升级项目');

    fireEvent.change(screen.getByPlaceholderText('搜索商机编码、名称...'), {
      target: { value: '智能' },
    });

    await waitFor(() => {
      expect(opportunityApi.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ keyword: '智能' }),
      );
    });

    fireEvent.change(screen.getAllByDisplayValue('需求澄清')[0], {
      target: { value: 'WON' },
    });

    await waitFor(() => {
      expect(opportunityApi.update).toHaveBeenCalledWith(1, { stage: 'WON' });
    });
  });

  it('handles embedded and empty states from the real page', async () => {
    opportunityApi.list.mockResolvedValueOnce({ data: { items: [], total: 0 } });

    renderPage({ embedded: true });

    expect(screen.queryByText('新建商机')).not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('暂无商机数据')).toBeInTheDocument();
    });
  });

  it('creates a general presales support ticket from an opportunity without requiring the gate to pass', async () => {
    renderPage();

    await screen.findByText('ERP 改造项目');

    fireEvent.click(screen.getAllByRole('button', { name: /发起支持/ })[1]);
    expect(screen.getByText('售前支持申请 - ERP 改造项目')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '提交支持' }));

    await waitFor(() => {
      expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
        sourceType: 'opportunity',
        sourceId: 2,
      });
      expect(presaleApi.tickets.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: '售前支持申请 - ERP 改造项目',
          ticket_type: 'TECHNICAL_SUPPORT',
          customer_id: 102,
          customer_name: '科技公司',
          lead_id: 2026,
          opportunity_id: 2,
          estimated_amount: 80,
          description: expect.stringContaining('商机编号：OPP-002'),
        }),
      );
    });

    const payload = presaleApi.tickets.create.mock.calls[0][0];
    expect(payload.description).toContain('预计金额：800000');
    expect(mockNavigate).toHaveBeenCalledWith(
      '/presales/technical-solutions?tab=reviews&type=support&status=pending&lead_id=2026&opportunity_id=2&ticket_id=501',
    );
  });

  it('reuses an active opportunity presales support ticket instead of creating duplicates', async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      ticket: {
        id: 777,
        ticket_type: 'TECHNICAL_SUPPORT',
        status: 'IN_PROGRESS',
      },
    });

    renderPage();

    await screen.findByText('智能制造升级项目');

    fireEvent.click(screen.getAllByRole('button', { name: /发起支持/ })[0]);
    fireEvent.click(screen.getByRole('button', { name: '提交支持' }));

    await waitFor(() => {
      expect(presaleWorkbenchApi.loadContext).toHaveBeenCalledWith({
        sourceType: 'opportunity',
        sourceId: 1,
      });
      expect(presaleApi.tickets.create).not.toHaveBeenCalled();
    });

    expect(mockNavigate).toHaveBeenCalledWith(
      '/presales/technical-solutions?tab=reviews&type=support&status=in_progress&opportunity_id=1&ticket_id=777',
    );
  });

  it('finds an older active support ticket when the workbench current ticket is another type', async () => {
    presaleWorkbenchApi.loadContext.mockResolvedValueOnce({
      ticket: {
        id: 778,
        ticket_type: 'FEASIBILITY_ASSESSMENT',
        status: 'PENDING',
      },
    });
    presaleApi.tickets.list.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 779,
            ticket_type: 'TECHNICAL_SUPPORT',
            status: 'ACCEPTED',
            lead_id: 2026,
          },
        ],
        total: 1,
      },
    });

    renderPage();

    await screen.findByText('ERP 改造项目');

    fireEvent.click(screen.getAllByRole('button', { name: /发起支持/ })[1]);
    fireEvent.click(screen.getByRole('button', { name: '提交支持' }));

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 50,
        opportunity_id: 2,
        status: 'PENDING,ACCEPTED,IN_PROGRESS,PROCESSING',
      });
      expect(presaleApi.tickets.create).not.toHaveBeenCalled();
    });

    expect(mockNavigate).toHaveBeenCalledWith(
      '/presales/technical-solutions?tab=reviews&type=support&status=in_progress&lead_id=2026&opportunity_id=2&ticket_id=779',
    );
  });

  it('creates a solution review ticket through the same presales support dialog', async () => {
    renderPage();

    await screen.findByText('智能制造升级项目');

    fireEvent.click(screen.getAllByRole('button', { name: /发起支持/ })[0]);
    fireEvent.change(screen.getByLabelText('支持类型'), {
      target: { value: 'SOLUTION_REVIEW' },
    });
    expect(screen.getByText('方案评审申请 - 智能制造升级项目')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '提交支持' }));

    await waitFor(() => {
      expect(presaleApi.tickets.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: '方案评审申请 - 智能制造升级项目',
          ticket_type: 'SOLUTION_REVIEW',
          customer_id: 101,
          customer_name: '某大型企业',
          opportunity_id: 1,
          description: expect.stringContaining('商机编号：OPP-001'),
        }),
      );
    });

    const payload = presaleApi.tickets.create.mock.calls[0][0];
    expect(payload.description).toContain('预计金额：1200000');
    expect(payload.description).toContain('阶段：需求澄清');
    expect(payload.description).toContain('项目类型：自动化测试线');
    expect(payload.description).toContain('设备类型：FCT');
    expect(payload.description).toContain('产品对象：动力电池模组');
    expect(payload.description).toContain('节拍：12 秒');
    expect(payload.description).toContain('接口：MES 对接');
    expect(payload.description).toContain('现场约束：三班倒不停线');
    expect(payload.description).toContain('验收依据：UPH 达标');

    expect(mockNavigate).toHaveBeenCalledWith(
      '/presales/technical-solutions?tab=reviews&type=review&status=reviewing&opportunity_id=1&ticket_id=501',
    );
  });

  it('creates a technical assessment presales ticket from an opportunity', async () => {
    renderPage();

    await screen.findByText('智能制造升级项目');

    fireEvent.click(screen.getAllByRole('button', { name: /发起支持/ })[0]);
    fireEvent.change(screen.getByLabelText('支持类型'), {
      target: { value: 'FEASIBILITY_ASSESSMENT' },
    });
    expect(screen.getByText('技术评估申请 - 智能制造升级项目')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '提交支持' }));

    await waitFor(() => {
      expect(presaleApi.tickets.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: '技术评估申请 - 智能制造升级项目',
          ticket_type: 'FEASIBILITY_ASSESSMENT',
          customer_id: 101,
          customer_name: '某大型企业',
          opportunity_id: 1,
          description: expect.stringContaining('商机编号：OPP-001'),
        }),
      );
    });

    expect(mockNavigate).toHaveBeenCalledWith(
      '/presales/technical-solutions?tab=reviews&type=assessment&status=pending&opportunity_id=1&ticket_id=501',
    );
  });
});
