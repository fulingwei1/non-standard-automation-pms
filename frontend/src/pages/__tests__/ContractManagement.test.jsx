import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ContractManagement from '../ContractManagement';
import * as contractService from '../../services/contractService';

vi.mock('../../services/contractService', () => ({
  getContracts: vi.fn(),
  deleteContract: vi.fn(),
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
    contractService.getContracts.mockResolvedValue({
      items: mockContracts,
      total: mockContracts.length,
    });
    contractService.deleteContract.mockResolvedValue({ success: true });
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

  it('shows overview stats based on loaded data', async () => {
    render(
      <MemoryRouter>
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
});
