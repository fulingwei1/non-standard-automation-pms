import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import PresalesTasks from '../PresalesTasks';
import { presaleApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  presaleApi: {
    tickets: {
      list: vi.fn(),
      create: vi.fn(),
      accept: vi.fn(),
      updateProgress: vi.fn(),
      createDeliverable: vi.fn(),
      complete: vi.fn(),
    },
  },
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => {
      const Tag = typeof tag === 'string' ? tag : 'div';
      return ({ children, ...props }) => {
        const motionProps = new Set([
          'initial',
          'animate',
          'exit',
          'variants',
          'transition',
          'whileHover',
          'whileTap',
          'layout',
        ]);
        const domProps = Object.fromEntries(
          Object.entries(props).filter(([key]) => !motionProps.has(key)),
        );
        return <Tag {...domProps}>{children}</Tag>;
      };
    },
  }),
  AnimatePresence: ({ children }) => children,
}));

const ticketItems = [
  {
    id: 11,
    title: '技术方案编写',
    ticket_type: 'SOLUTION_DESIGN',
    status: 'PENDING',
    urgency: 'HIGH',
    customer_name: '华东制造',
    applicant_name: '宋魁',
    deadline: '2026-06-30',
    description: '输出非标自动化方案',
    estimated_hours: 12,
    actual_hours: 0,
  },
  {
    id: 12,
    title: '投标成本核算',
    ticket_type: 'COST_ESTIMATE',
    status: 'IN_PROGRESS',
    urgency: 'MEDIUM',
    customer_name: '苏州装备',
    applicant_name: '郑琴',
    deadline: '2026-07-05',
    progress: 40,
    description: '核算关键部件成本',
    estimated_hours: 8,
    actual_hours: 3,
  },
];
const navigateSpy = vi.fn();

function toLocation(initialEntry) {
  if (typeof initialEntry === 'string') {
    const url = new URL(initialEntry, 'http://localhost');
    return {
      pathname: url.pathname,
      search: url.search,
      hash: url.hash,
      state: null,
    };
  }
  return {
    pathname: initialEntry.pathname || '/presales-tasks',
    search: initialEntry.search || '',
    hash: initialEntry.hash || '',
    state: initialEntry.state || null,
  };
}

function renderPage(initialEntry = '/presales-tasks', props = {}) {
  useLocation.mockReturnValue(toLocation(initialEntry));
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <PresalesTasks {...props} />
    </MemoryRouter>,
  );
}

describe('PresalesTasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useNavigate.mockReturnValue(navigateSpy);
    useLocation.mockReturnValue(toLocation('/presales-tasks'));
    vi.spyOn(window, 'alert').mockImplementation(() => {});
    presaleApi.tickets.list.mockResolvedValue({
      data: { items: ticketItems, total: ticketItems.length },
    });
    presaleApi.tickets.create.mockResolvedValue({
      data: {
        id: 99,
        title: '客户现场技术交流',
        ticket_type: 'TECHNICAL_EXCHANGE',
        status: 'PENDING',
      },
    });
    presaleApi.tickets.accept.mockResolvedValue({ data: { success: true } });
    presaleApi.tickets.updateProgress.mockResolvedValue({ data: { success: true } });
    presaleApi.tickets.createDeliverable.mockResolvedValue({
      data: {
        id: 70,
        deliverable_name: '新版技术方案',
        deliverable_type: 'SOLUTION',
        file_path: '/files/solution-v2.pdf',
      },
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders technical task cards from presale tickets', async () => {
    renderPage();

    expect(screen.getByText('技术任务中心')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('技术方案编写')).toBeInTheDocument();
    });
    expect(screen.getByText('华东制造')).toBeInTheDocument();
    expect(screen.getByText('销售：宋魁')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('搜索任务...')).toHaveValue('');
    expect(presaleApi.tickets.list).toHaveBeenCalledWith({ page: 1, page_size: 100 });
  });

  it('renders review tasks from formatted unified responses and keeps query filters', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      formatted: {
        items: [
          {
            id: 31,
            title: '方案评审申请 - 智能制造升级项目',
            ticket_type: 'SOLUTION_REVIEW',
            status: 'REVIEW',
            urgency: 'NORMAL',
            customer_name: '某大型企业',
            applicant_name: '张三',
            expected_date: '2026-06-20',
            description: '商机编号：OPP-001',
          },
        ],
        total: 1,
      },
    });

    renderPage({
      pathname: '/sales/presales-tasks',
      search: '?type=review&status=reviewing',
    });

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        status: 'REVIEW',
      });
    });

    expect(screen.getByText('方案评审申请 - 智能制造升级项目')).toBeInTheDocument();
    expect(screen.getByText('某大型企业')).toBeInTheDocument();
  });

  it('passes opportunity and ticket filters when opened from sales presales support', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 501,
            title: '售前支持申请 - ERP 改造项目',
            ticket_type: 'TECHNICAL_SUPPORT',
            status: 'PENDING',
            urgency: 'NORMAL',
            customer_name: '科技公司',
            applicant_name: '李四',
            expected_date: '2026-06-20',
            description: '商机编号：OPP-002',
            opportunity_id: 2,
            opportunity_name: 'ERP 改造商机',
            estimated_amount: 800000,
          },
        ],
        total: 1,
      },
    });

    renderPage({
      pathname: '/presales/technical-solutions',
      search: '?tab=reviews&type=support&status=pending&opportunity_id=2&ticket_id=501',
    });

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        status: 'PENDING',
        opportunity_id: '2',
        ticket_id: '501',
      });
    });

    expect(screen.getByText('售前支持申请 - ERP 改造项目')).toBeInTheDocument();
    expect(screen.getAllByText('售前支持').length).toBeGreaterThan(0);
    expect(screen.getByText('¥80万')).toBeInTheDocument();
  });

  it('keeps project context when loading and creating tasks from the unified center', async () => {
    renderPage(
      {
        pathname: '/presales/technical-solutions',
        search: '?tab=reviews&type=support&status=pending&opportunity_id=2&ticket_id=501&project_id=42',
      },
      { embedded: true },
    );

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        status: 'PENDING',
        opportunity_id: '2',
        ticket_id: '501',
        project_id: '42',
      });
    });

    fireEvent.click(screen.getByRole('button', { name: /新建任务/ }));
    fireEvent.change(screen.getByLabelText('任务标题'), {
      target: { value: '项目现场方案澄清' },
    });
    fireEvent.change(screen.getByLabelText('任务说明'), {
      target: { value: '补充项目现场约束和验收口径' },
    });

    fireEvent.click(screen.getByRole('button', { name: '创建任务' }));

    await waitFor(() => {
      expect(presaleApi.tickets.create).toHaveBeenCalledWith({
        title: '项目现场方案澄清',
        ticket_type: 'SOLUTION_DESIGN',
        urgency: 'NORMAL',
        description: '补充项目现场约束和验收口径',
        opportunity_id: 2,
        project_id: 42,
      });
    });
  });

  it('keeps lead context when opened from a sales lead presales center link', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 701,
            title: '线索售前技术支持',
            ticket_type: 'TECHNICAL_SUPPORT',
            status: 'PENDING',
            urgency: 'NORMAL',
            customer_name: '华东线索客户',
            applicant_name: '张销售',
            description: '线索阶段需要售前判断测试方案可行性',
            lead_id: 21,
          },
        ],
        total: 1,
      },
    });

    renderPage(
      {
        pathname: '/presales/technical-solutions',
        search: '?tab=reviews&type=support&status=pending&lead_id=21',
      },
      { embedded: true },
    );

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        status: 'PENDING',
        lead_id: '21',
      });
    });

    expect(screen.getByText('线索售前技术支持')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /新建任务/ }));
    fireEvent.change(screen.getByLabelText('任务标题'), {
      target: { value: '线索现场技术交流' },
    });
    fireEvent.change(screen.getByLabelText('任务说明'), {
      target: { value: '提前澄清节拍和治具边界' },
    });

    fireEvent.click(screen.getByRole('button', { name: '创建任务' }));

    await waitFor(() => {
      expect(presaleApi.tickets.create).toHaveBeenCalledWith({
        title: '线索现场技术交流',
        ticket_type: 'SOLUTION_DESIGN',
        urgency: 'NORMAL',
        description: '提前澄清节拍和治具边界',
        lead_id: 21,
      });
    });
  });

  it('does not show progress update controls for backend REVIEW tickets', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 32,
            title: '方案评审申请 - 视觉检测项目',
            ticket_type: 'SOLUTION_REVIEW',
            status: 'REVIEW',
            urgency: 'NORMAL',
            customer_name: '苏州电子',
            applicant_name: '吴敏',
            expected_date: '2026-06-22',
            description: '审核方案边界和成本测算',
          },
        ],
        total: 1,
      },
    });

    renderPage('/sales/presales-tasks?type=review&status=reviewing');

    await screen.findByText('方案评审申请 - 视觉检测项目');
    fireEvent.click(screen.getByText('方案评审申请 - 视觉检测项目'));

    expect(screen.queryByRole('button', { name: /更新进度/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /完成工单/ })).toBeInTheDocument();
  });

  it('completes a review ticket with a sales-visible review conclusion', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 33,
            title: '方案评审申请 - 视觉检测项目',
            ticket_type: 'SOLUTION_REVIEW',
            status: 'REVIEW',
            urgency: 'NORMAL',
            customer_name: '苏州电子',
            applicant_name: '吴敏',
            expected_date: '2026-06-22',
            description: '审核方案边界和成本测算',
          },
        ],
        total: 1,
      },
    });
    presaleApi.tickets.complete.mockResolvedValue({ data: { success: true } });

    renderPage('/sales/presales-tasks?type=review&status=reviewing');

    await screen.findByText('方案评审申请 - 视觉检测项目');
    fireEvent.click(screen.getByText('方案评审申请 - 视觉检测项目'));

    fireEvent.change(screen.getByLabelText('实际工时（小时）'), {
      target: { value: '5.5' },
    });
    fireEvent.change(screen.getByLabelText('完成说明 / 评审结论'), {
      target: { value: '方案可行，成本边界清楚，建议进入报价' },
    });
    fireEvent.click(screen.getByRole('button', { name: /完成工单/ }));

    await waitFor(() => {
      expect(presaleApi.tickets.complete).toHaveBeenCalledWith(33, {
        actual_hours: 5.5,
        completion_note: '方案可行，成本边界清楚，建议进入报价',
      });
    });
  });

  it('uses backend progress_percent when rendering in-progress tickets', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 41,
            title: '方案深化',
            ticket_type: 'SOLUTION_DESIGN',
            status: 'IN_PROGRESS',
            urgency: 'NORMAL',
            customer_name: '华东制造',
            applicant_name: '宋魁',
            progress_percent: 65,
            actual_hours: 4,
          },
        ],
        total: 1,
      },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('方案深化')).toBeInTheDocument();
    });

    expect(screen.getByText('65%')).toBeInTheDocument();
  });

  it('shows PM involvement warnings from presale tickets in the unified center', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 71,
            title: '大型线体方案评审',
            ticket_type: 'SOLUTION_REVIEW',
            status: 'REVIEW',
            urgency: 'HIGH',
            customer_name: '华南电子',
            applicant_name: '王伟',
            description: '金额大且交期紧，需要提前拉项目经理评审。',
            expected_date: '2026-06-12',
            pm_involvement_required: true,
            pm_involvement_risk_level: '高',
            pm_involvement_risk_factors: ['金额高', '交期紧'],
            pm_assigned: false,
          },
        ],
        total: 1,
      },
    });

    renderPage('/presales/technical-solutions?tab=reviews&type=review&status=reviewing');

    await screen.findByText('大型线体方案评审');

    expect(screen.getByText('需PM介入')).toBeInTheDocument();
    expect(screen.getByText('高风险')).toBeInTheDocument();
    expect(screen.getByText('金额高、交期紧')).toBeInTheDocument();
    expect(screen.getByText('PM未分配')).toBeInTheDocument();

    fireEvent.click(screen.getByText('大型线体方案评审'));

    expect(screen.getByText('PM提前介入')).toBeInTheDocument();
  });

  it('opens the linked project workspace from a project presale task detail', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 91,
            title: 'FCT售前技术支持',
            ticket_type: 'TECHNICAL_SUPPORT',
            status: 'IN_PROGRESS',
            urgency: 'HIGH',
            customer_name: '华南电子',
            applicant_name: '张销售',
            description: '交接售前方案、成本边界和验收口径',
            lead_id: 2026,
            opportunity_id: 2,
            opportunity_name: '电源测试线商机',
            project_id: 42,
          },
        ],
        total: 1,
      },
    });

    renderPage('/presales/technical-solutions?tab=reviews&type=support&ticket_id=91&opportunity_id=2&project_id=42');

    await screen.findByText('FCT售前技术支持');
    fireEvent.click(screen.getByText('FCT售前技术支持'));
    fireEvent.click(screen.getByRole('button', { name: /打开项目工作区/ }));

    expect(navigateSpy).toHaveBeenCalledWith(
      '/projects/42/workspace?ticket_id=91&lead_id=2026&opportunity_id=2&project_id=42',
    );
  });

  it('opens the linked lead technical assessment from a presale task detail', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 92,
            title: '线索售前可行性评估',
            ticket_type: 'TECHNICAL_SUPPORT',
            status: 'IN_PROGRESS',
            urgency: 'HIGH',
            customer_name: '华东电子',
            applicant_name: '张销售',
            description: '线索阶段评估测试方案和成本边界',
            lead_id: 21,
            assessment_status: 'IN_PROGRESS',
            current_assessment_id: 701,
          },
        ],
        total: 1,
      },
    });

    renderPage('/presales/technical-solutions?tab=reviews&type=support&lead_id=21');

    await screen.findByText('线索售前可行性评估');
    fireEvent.click(screen.getByText('线索售前可行性评估'));
    fireEvent.click(screen.getByRole('button', { name: /打开技术评估/ }));

    expect(navigateSpy).toHaveBeenCalledWith(
      '/sales/assessments/lead/21?assessment_id=701&ticket_id=92',
    );
  });

  it('opens the linked opportunity technical assessment when a converted lead task has both contexts', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 93,
            title: '商机售前技术评估',
            ticket_type: 'TECHNICAL_SUPPORT',
            status: 'IN_PROGRESS',
            urgency: 'HIGH',
            customer_name: '华东电子',
            applicant_name: '张销售',
            description: '线索转商机后评估测试方案和成本边界',
            lead_id: 21,
            opportunity_id: 2,
            opportunity_name: '视觉检测商机',
            project_id: 42,
            assessment_status: 'COMPLETED',
            current_assessment_id: 702,
          },
        ],
        total: 1,
      },
    });

    renderPage(
      '/presales/technical-solutions?tab=reviews&type=support&lead_id=21&opportunity_id=2&ticket_id=93',
    );

    await screen.findByText('商机售前技术评估');
    fireEvent.click(screen.getByText('商机售前技术评估'));
    fireEvent.click(screen.getByRole('button', { name: /打开技术评估/ }));

    expect(navigateSpy).toHaveBeenCalledWith(
      '/sales/assessments/opportunity/2?assessment_id=702&ticket_id=93&lead_id=21&project_id=42',
    );
  });

  it('creates an internal presale task from the task center and refreshes the list', async () => {
    renderPage('/sales/presales-tasks');

    await screen.findByText('技术方案编写');

    fireEvent.click(screen.getByRole('button', { name: /新建任务/ }));

    expect(screen.getByText('新建售前任务')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('任务标题'), {
      target: { value: '客户现场技术交流' },
    });
    fireEvent.change(screen.getByLabelText('任务类型'), {
      target: { value: 'TECHNICAL_EXCHANGE' },
    });
    fireEvent.change(screen.getByLabelText('紧急程度'), {
      target: { value: 'URGENT' },
    });
    fireEvent.change(screen.getByLabelText('客户名称'), {
      target: { value: '华东制造' },
    });
    fireEvent.change(screen.getByLabelText('期望完成日期'), {
      target: { value: '2026-06-20' },
    });
    fireEvent.change(screen.getByLabelText('任务说明'), {
      target: { value: '现场澄清节拍和验收标准' },
    });

    fireEvent.click(screen.getByRole('button', { name: '创建任务' }));

    await waitFor(() => {
      expect(presaleApi.tickets.create).toHaveBeenCalledWith({
        title: '客户现场技术交流',
        ticket_type: 'TECHNICAL_EXCHANGE',
        urgency: 'URGENT',
        customer_name: '华东制造',
        expected_date: '2026-06-20',
        description: '现场澄清节拍和验收标准',
      });
    });

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledTimes(2);
    });
  });

  it('requests backend status filters using current ticket API parameters', async () => {
    renderPage();

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledTimes(1);
    });

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'in_progress' },
    });

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        status: 'ACCEPTED,IN_PROGRESS,PROCESSING',
      });
    });
  });

  it('opens details and accepts the selected ticket id', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('技术方案编写')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('技术方案编写'));
    expect(screen.getByText('任务详情')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /接单处理/ }));

    await waitFor(() => {
      expect(presaleApi.tickets.accept).toHaveBeenCalledWith(11, {});
    });
  });

  it('renders ticket deliverables returned by the backend in the detail panel', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 51,
            title: '方案深化交付',
            ticket_type: 'SOLUTION_DESIGN',
            status: 'IN_PROGRESS',
            urgency: 'NORMAL',
            customer_name: '华南电子',
            applicant_name: '陈敏',
            description: '深化测试方案',
            deliverables: [
              {
                id: 7,
                deliverable_name: '初版技术方案',
                deliverable_type: 'SOLUTION',
                file_path: '/files/solution-v1.pdf',
              },
            ],
          },
        ],
        total: 1,
      },
    });

    renderPage();

    await screen.findByText('方案深化交付');

    fireEvent.click(screen.getByText('方案深化交付'));

    expect(screen.getByText('初版技术方案')).toBeInTheDocument();
  });

  it('submits a deliverable from an in-progress ticket detail panel', async () => {
    presaleApi.tickets.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 61,
            title: '方案输出',
            ticket_type: 'SOLUTION_DESIGN',
            status: 'IN_PROGRESS',
            urgency: 'NORMAL',
            customer_name: '华南电子',
            applicant_name: '陈敏',
            description: '输出技术方案',
          },
        ],
        total: 1,
      },
    });

    renderPage();

    await screen.findByText('方案输出');
    fireEvent.click(screen.getByText('方案输出'));

    fireEvent.change(screen.getByLabelText('交付物名称'), {
      target: { value: '新版技术方案' },
    });
    fireEvent.change(screen.getByLabelText('交付物类型'), {
      target: { value: 'SOLUTION' },
    });
    fireEvent.change(screen.getByLabelText('文件路径或链接'), {
      target: { value: '/files/solution-v2.pdf' },
    });

    fireEvent.click(screen.getByRole('button', { name: /提交交付物/ }));

    await waitFor(() => {
      expect(presaleApi.tickets.createDeliverable).toHaveBeenCalledWith(61, {
        deliverable_name: '新版技术方案',
        deliverable_type: 'SOLUTION',
        file_path: '/files/solution-v2.pdf',
      });
    });
    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText('新版技术方案')).toBeInTheDocument();
  });
});
