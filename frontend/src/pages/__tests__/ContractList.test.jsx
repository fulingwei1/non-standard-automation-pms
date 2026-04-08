import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ContractList from '../ContractList';

const {
  mockUseContractList,
  consoleErrorMock,
  alertMock,
} = vi.hoisted(() => ({
  mockUseContractList: vi.fn(),
  consoleErrorMock: vi.fn(),
  alertMock: vi.fn(),
}));

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

vi.mock('../../services/api', () => ({
  contractApi: {
    list: vi.fn(),
  },
}));

vi.mock('../ContractList/hooks', () => ({
  useContractList: mockUseContractList,
}));

vi.mock('../ContractList/ContractStatsRow', () => ({
  default: ({ stats }) => (
    <div data-testid="contract-stats">
      总数:{stats.total}|进行中:{stats.active}|已完成:{stats.completed}
    </div>
  ),
}));

vi.mock('../ContractList/ContractFilters', () => ({
  default: ({ searchTerm, onSearchChange, selectedStatus, onStatusChange, resultCount }) => (
    <div data-testid="contract-filters">
      <input
        aria-label="搜索合同"
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
      />
      <select
        aria-label="合同状态"
        value={selectedStatus}
        onChange={(e) => onStatusChange(e.target.value)}
      >
        <option value="all">全部状态</option>
        <option value="active">进行中</option>
      </select>
      <span>结果:{resultCount}</span>
    </div>
  ),
}));

vi.mock('../ContractList/ContractTable', () => ({
  default: ({ contracts, onContractClick, onCreateClick }) => (
    <div data-testid="contract-table">
      {contracts.map((contract) => (
        <button
          key={contract.id}
          onClick={() => onContractClick(contract)}
        >
          {contract.name}
        </button>
      ))}
      <button onClick={onCreateClick}>table-create</button>
    </div>
  ),
}));

vi.mock('../ContractList/ContractDetailPanel', () => ({
  default: ({ contract, onClose }) => (
    <div data-testid="contract-detail-panel">
      <span>{contract.name}</span>
      <button onClick={onClose}>close-detail</button>
    </div>
  ),
}));

vi.mock('../ContractList/CreateContractDialog', () => ({
  default: ({ open, onOpenChange }) => (
    <div data-testid="create-contract-dialog">
      {open ? 'open' : 'closed'}
      <button onClick={() => onOpenChange(false)}>close-create</button>
    </div>
  ),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ContractList />
    </MemoryRouter>,
  );
}

describe('ContractList', () => {
  const baseHookValue = {
    loading: false,
    error: null,
    filteredContracts: [
      { id: 'HT-001', name: '智能制造系统合同' },
      { id: 'HT-002', name: 'ERP升级合同' },
    ],
    stats: {
      total: 2,
      active: 1,
      completed: 1,
      totalValue: 300000,
      paidValue: 100000,
      pendingValue: 200000,
    },
    searchTerm: '',
    setSearchTerm: vi.fn(),
    selectedStatus: 'all',
    setSelectedStatus: vi.fn(),
    selectedContract: null,
    setSelectedContract: vi.fn(),
    showCreateDialog: false,
    setShowCreateDialog: vi.fn(),
    handleContractClick: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseContractList.mockReturnValue(baseHookValue);
  });

  it('renders page skeleton from the real page and hook state', () => {
    renderPage();

    expect(screen.getByText('合同管理')).toBeInTheDocument();
    expect(screen.getByText('管理销售合同和付款条款')).toBeInTheDocument();
    expect(screen.getByTestId('contract-stats')).toHaveTextContent('总数:2|进行中:1|已完成:1');
    expect(screen.getByText('智能制造系统合同')).toBeInTheDocument();
    expect(screen.getByText('ERP升级合同')).toBeInTheDocument();
    expect(screen.getByText('结果:2')).toBeInTheDocument();
  });

  it('wires search, status, and create actions back to the hook', () => {
    const setSearchTerm = vi.fn();
    const setSelectedStatus = vi.fn();
    const setShowCreateDialog = vi.fn();
    const handleContractClick = vi.fn();

    mockUseContractList.mockReturnValue({
      ...baseHookValue,
      setSearchTerm,
      setSelectedStatus,
      setShowCreateDialog,
      handleContractClick,
    });

    renderPage();

    fireEvent.change(screen.getByLabelText('搜索合同'), {
      target: { value: '智能' },
    });
    expect(setSearchTerm).toHaveBeenCalledWith('智能');

    fireEvent.change(screen.getByLabelText('合同状态'), {
      target: { value: 'active' },
    });
    expect(setSelectedStatus).toHaveBeenCalledWith('active');

    fireEvent.click(screen.getByRole('button', { name: '新建合同' }));
    expect(setShowCreateDialog).toHaveBeenCalledWith(true);

    fireEvent.click(screen.getByRole('button', { name: '智能制造系统合同' }));
    expect(handleContractClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'HT-001', name: '智能制造系统合同' }),
    );
  });

  it('renders loading, error, detail panel and dialog states from current implementation', () => {
    const { rerender } = render(
      <MemoryRouter>
        <ContractList />
      </MemoryRouter>,
    );

    mockUseContractList.mockReturnValue({
      ...baseHookValue,
      loading: true,
      filteredContracts: [],
    });
    rerender(
      <MemoryRouter>
        <ContractList />
      </MemoryRouter>,
    );
    expect(screen.getByText('加载中...')).toBeInTheDocument();

    mockUseContractList.mockReturnValue({
      ...baseHookValue,
      error: '加载合同数据失败，请稍后重试',
      filteredContracts: [],
    });
    rerender(
      <MemoryRouter>
        <ContractList />
      </MemoryRouter>,
    );
    expect(screen.getByText('加载失败')).toBeInTheDocument();
    expect(screen.getByText('加载合同数据失败，请稍后重试')).toBeInTheDocument();

    mockUseContractList.mockReturnValue({
      ...baseHookValue,
      selectedContract: { id: 'HT-001', name: '智能制造系统合同' },
      showCreateDialog: true,
    });
    rerender(
      <MemoryRouter>
        <ContractList />
      </MemoryRouter>,
    );
    expect(screen.getByTestId('contract-detail-panel')).toHaveTextContent('智能制造系统合同');
    expect(screen.getByTestId('create-contract-dialog')).toHaveTextContent('open');
  });

  it('应该处理加载合同列表API失败的情况', () => {
    vi.spyOn(console, 'error').mockImplementation(consoleErrorMock);
    
    mockUseContractList.mockReturnValue({
      ...baseHookValue,
      loading: false,
      error: '加载合同数据失败，请稍后重试',
      filteredContracts: [],
    });

    render(
      <MemoryRouter>
        <ContractList />
      </MemoryRouter>,
    );

    expect(screen.getByText('加载失败')).toBeInTheDocument();
    expect(screen.getByText('加载合同数据失败，请稍后重试')).toBeInTheDocument();
  });
});