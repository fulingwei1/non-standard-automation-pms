import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import ContractManagement from '../ContractManagement';
import * as contractService from '../../services/contractService';
import { paymentPlanApi, pmoApi, receivableApi } from '../../services/api';

const mockNavigate = vi.hoisted(() => vi.fn());

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../services/contractService', () => ({
  getContracts: vi.fn(),
  deleteContract: vi.fn(),
  signContract: vi.fn(),
  createProjectFromContract: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  paymentPlanApi: {
    list: vi.fn(),
  },
  pmoApi: {
    initiations: {
      list: vi.fn(),
      create: vi.fn(),
    },
  },
  receivableApi: {
    getSummary: vi.fn(),
  },
}));

vi.mock('../../hooks/usePermission', () => ({
  usePermission: () => ({
    hasPermission: () => false,
    isLoading: false,
  }),
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(
        Object.entries(props).filter(
          ([k]) =>
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
            ].includes(k)
        )
      );
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    },
  }),
  AnimatePresence: ({ children }) => children,
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useInView: () => true,
}));

describe('ContractManagement', () => {
  const mockContracts = [
    {
      id: 1,
      contract_code: 'CON-2024-001',
      contract_name: '智能制造系统合同',
      customer_name: '某大型制造企业',
      contract_type: 'sales',
      status: 'executing',
      total_amount: '1000000',
      created_at: '2024-01-10T10:00:00',
    },
    {
      id: 2,
      contract_code: 'CON-2024-002',
      contract_name: 'ERP升级合同',
      customer_name: '某科技公司',
      contract_type: 'service',
      status: 'draft',
      total_amount: '800000',
      created_at: '2024-02-10T10:00:00',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    contractService.getContracts.mockResolvedValue({
      items: mockContracts,
      total: mockContracts.length,
    });
    contractService.deleteContract.mockResolvedValue({ success: true });
    contractService.signContract.mockResolvedValue({
      code: 200,
      message: '合同签订成功',
      data: { contract_id: 2 },
    });
    contractService.createProjectFromContract.mockResolvedValue({
      code: 200,
      message: '项目创建成功',
      data: { project_id: 9 },
    });
    pmoApi.initiations.create.mockResolvedValue({
      data: {
        id: 12,
        status: 'DRAFT',
      },
    });
    pmoApi.initiations.list.mockResolvedValue({
      data: {
        items: [],
      },
    });
    paymentPlanApi.list.mockResolvedValue({
      data: {
        items: [],
        total: 0,
      },
    });
    receivableApi.getSummary.mockResolvedValue({
      data: {
        data: {
          invoice_count: 0,
          unpaid_amount: 0,
          overdue_count: 0,
          overdue_amount: 0,
          collection_rate: 0,
        },
      },
    });
  });

  it('renders page title and loads contracts via contractService', async () => {
    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    expect(screen.getByText('合同管理')).toBeInTheDocument();

    await waitFor(() => {
      expect(contractService.getContracts).toHaveBeenCalled();
    });
  });

  it('opens the contract list by default for the sales contract center', async () => {
    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/合同列表 \(2\)/)).toBeInTheDocument();
      expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
      expect(screen.getByText('ERP升级合同')).toBeInTheDocument();
    });
  });

  it('shows overview stats based on loaded data', async () => {
    render(
      <MemoryRouter initialEntries={['/sales/contracts?tab=overview']}>
        <ContractManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('合同总数')).toBeInTheDocument();
      expect(screen.getByText('合同总价值')).toBeInTheDocument();
      expect(screen.getByText('待签署')).toBeInTheDocument();
      expect(screen.getByText('完成率')).toBeInTheDocument();
    });
  });

  it('filters contracts by search text on current implementation', async () => {
    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    const searchInput = await screen.findByPlaceholderText('搜索合同标题、客户名称...');
    fireEvent.change(searchInput, { target: { value: 'ERP' } });

    expect(searchInput).toHaveValue('ERP');
    expect(contractService.getContracts).toHaveBeenCalled();
  });

  it('shows error message when loading fails', async () => {
    contractService.getContracts.mockRejectedValueOnce(new Error('boom'));

    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('合同管理')).toBeInTheDocument();
    });
  });

  it('starts PMO initiation from a signed contract instead of directly creating a project', async () => {
    const user = userEvent.setup();
    contractService.getContracts.mockResolvedValue({
      items: [
        {
          id: 3,
          contract_code: 'CON-2026-003',
          contract_name: '非标测试设备合同',
          customer_name: '金凯博客户',
          contract_type: 'sales',
          status: 'SIGNED',
          total_amount: '600000',
          signing_date: '2026-06-06',
          delivery_deadline: '2026-09-30',
          requirement_summary: 'FCT测试设备，扫码追溯，节拍8秒',
        },
      ],
      total: 1,
    });

    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/合同列表 \(1\)/)).toBeInTheDocument();
    });
    const contractsTab = Array.from(document.querySelectorAll('[role="tab"]')).find((tab) =>
      tab.textContent.includes('合同列表')
    );
    await user.click(contractsTab);
    const initiationButton = await screen.findByRole('button', { name: '发起立项' });
    await user.click(initiationButton);

    await waitFor(() => {
      expect(pmoApi.initiations.create).not.toHaveBeenCalled();
      expect(contractService.createProjectFromContract).not.toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith(
        expect.stringContaining('/pmo/initiations?handoff=contract'),
      );
      const target = mockNavigate.mock.calls.at(-1)[0];
      expect(target).toContain('contract_no=CON-2026-003');
      expect(decodeURIComponent(target)).toContain('requirement_summary=FCT测试设备，扫码追溯，节拍8秒');
      expect(target).toContain('required_end_date=2026-09-30');
    });
  });

  it('shows project, payment plan, invoice, and receivable status in contract list', async () => {
    const user = userEvent.setup();
    contractService.getContracts.mockResolvedValue({
      items: [
        {
          id: 3,
          contract_code: 'CON-2026-003',
          contract_name: '已立项设备合同',
          customer_name: '金凯博客户',
          contract_type: 'sales',
          status: 'EXECUTING',
          total_amount: '600000',
          project_id: 9,
          project_code: 'PJ202606001',
        },
        {
          id: 4,
          contract_code: 'CON-2026-004',
          contract_name: '待立项设备合同',
          customer_name: '新客户',
          contract_type: 'sales',
          status: 'SIGNED',
          total_amount: '300000',
        },
      ],
      total: 2,
    });
    paymentPlanApi.list.mockImplementation(({ contract_id }) =>
      Promise.resolve({
        data: {
          items: contract_id === 3 ? [{ id: 1 }, { id: 2 }] : [],
          total: contract_id === 3 ? 2 : 0,
        },
      })
    );
    receivableApi.getSummary.mockImplementation(({ contract_id }) =>
      Promise.resolve({
        data: {
          data: contract_id === 3
            ? {
                invoice_count: 3,
                unpaid_amount: 80000,
                overdue_count: 1,
                overdue_amount: 20000,
                collection_rate: 86.7,
              }
            : {
                invoice_count: 0,
                unpaid_amount: 0,
                overdue_count: 0,
                overdue_amount: 0,
                collection_rate: 0,
              },
        },
      })
    );

    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/合同列表 \(2\)/)).toBeInTheDocument();
    });
    const contractsTab = Array.from(document.querySelectorAll('[role="tab"]')).find((tab) =>
      tab.textContent.includes('合同列表')
    );
    expect(contractsTab).toBeTruthy();
    await user.click(contractsTab);

    await waitFor(() => {
      expect(receivableApi.getSummary).toHaveBeenCalledWith({ contract_id: 3 });
      expect(paymentPlanApi.list).toHaveBeenCalledWith({ contract_id: 3, page_size: 100 });
    });

    expect(await screen.findByText('已立项')).toBeInTheDocument();
    expect(screen.getByText('项目 PJ202606001')).toBeInTheDocument();
    expect(screen.getByText('待立项')).toBeInTheDocument();
    expect(screen.getByText('收款计划 2期')).toBeInTheDocument();
    expect(screen.getByText('已开票 3张')).toBeInTheDocument();
    expect(screen.getByText('待收 ¥80,000')).toBeInTheDocument();
    expect(screen.getByText('逾期 1笔')).toBeInTheDocument();
  });

  it('signs a draft contract through the real API without auto creating a project', async () => {
    const user = userEvent.setup();
    contractService.getContracts.mockResolvedValue({
      items: [
        {
          id: 2,
          contract_code: 'CON-2026-002',
          contract_name: '待签署设备合同',
          customer_name: '新客户',
          contract_type: 'sales',
          status: 'draft',
          total_amount: '300000',
        },
      ],
      total: 1,
    });

    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/合同列表 \(1\)/)).toBeInTheDocument();
    });
    const contractsTab = Array.from(document.querySelectorAll('[role="tab"]')).find((tab) =>
      tab.textContent.includes('合同列表')
    );
    expect(contractsTab).toBeTruthy();
    await user.click(contractsTab);

    const signButton = await screen.findByRole('button', { name: '签署' });
    await user.click(signButton);
    const confirmSignButton = await screen.findByRole('button', { name: '确认签署' });
    await user.click(confirmSignButton);

    await waitFor(() => {
      expect(contractService.signContract).toHaveBeenCalledWith(
        2,
        expect.objectContaining({
          auto_create_project: false,
          signed_date: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
        }),
      );
      expect(contractService.createProjectFromContract).not.toHaveBeenCalled();
      expect(pmoApi.initiations.create).not.toHaveBeenCalled();
    });
  });

  it('opens existing initiation from contract list instead of creating duplicate initiation', async () => {
    const user = userEvent.setup();
    contractService.getContracts.mockResolvedValue({
      items: [
        {
          id: 101,
          contract_code: 'ECMQ2N2LX1',
          contract_name: 'ECMQ2N2LX1',
          customer_name: 'E2E立项客户-MQ2N2LX1',
          contract_type: 'sales',
          status: 'SIGNED',
          total_amount: '188000',
          project_id: null,
        },
      ],
      total: 1,
    });
    pmoApi.initiations.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 5,
            contract_no: 'ECMQ2N2LX1',
            status: 'DRAFT',
          },
          {
            id: 4,
            contract_no: 'ECMQ2N2LX1',
            status: 'SUBMITTED',
          },
        ],
      },
    });

    render(
      <MemoryRouter>
        <ContractManagement />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/合同列表 \(1\)/)).toBeInTheDocument();
    });
    const contractsTab = Array.from(document.querySelectorAll('[role="tab"]')).find((tab) =>
      tab.textContent.includes('合同列表')
    );
    expect(contractsTab).toBeTruthy();
    await user.click(contractsTab);

    const initiationButton = await screen.findByRole('button', { name: '发起立项' });
    await user.click(initiationButton);

    await waitFor(() => {
      expect(pmoApi.initiations.list).toHaveBeenCalledWith(
        expect.objectContaining({ contract_no: 'ECMQ2N2LX1' }),
      );
      expect(pmoApi.initiations.create).not.toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/pmo/initiations/4');
    });
  });
});
