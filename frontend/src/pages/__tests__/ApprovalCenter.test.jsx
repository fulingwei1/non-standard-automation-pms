/**
 * ApprovalCenter 组件测试
 * 测试覆盖：审批中心主页、四个标签页、数据加载、筛选功能
 */


import { describe, it, expect, vi, beforeEach } from 'vitest';

import { render, screen } from '@testing-library/react';

import { MemoryRouter } from 'react-router-dom';

// Mock all the components used in ApprovalCenter
vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, description, actions }) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      <p>{description}</p>
      {actions && <div data-testid="header-actions">{actions}</div>}
    </div>
  ),
}));

// Mock the UI components
vi.mock('../../components/ui', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    Button: ({ children, variant, onClick, ...props }) => (
      <button 
        data-testid="button"
        data-button-text={typeof children === 'string' ? children : ''}
        data-variant={variant} 
        onClick={onClick} 
        {...props}
      >
        {children}
      </button>
    ),
    Badge: ({ children, ...props }) => (
      <span data-testid="badge" {...props}>{children}</span>
    ),
    Tabs: ({ children, value, onValueChange }) => (
      <div data-testid="tabs" data-value={value}>
        <input 
          type="hidden" 
          value={value} 
          onChange={(e) => onValueChange?.(e.target.value)} 
          data-testid="tabs-input"
        />
        {children}
      </div>
    ),
    TabsContent: ({ children, value }) => (
      <div data-testid="tabs-content" data-value={value}>
        {children}
      </div>
    ),
    TabsList: ({ children }) => (
      <div data-testid="tabs-list">{children}</div>
    ),
    TabsTrigger: ({ children, value, onClick }) => (
      <button 
        data-testid="tabs-trigger" 
        data-value={value} 
        onClick={() => onClick?.()}
      >
        {children}
      </button>
    ),
  };
});

vi.mock('../../components/ui/button', () => ({
  Button: ({ children, variant, onClick, ...props }) => (
    <button
      data-testid="button"
      data-button-text={typeof children === 'string' ? children : ''}
      data-variant={variant}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  ),
}));

vi.mock('../../components/ui/badge', () => ({
  Badge: ({ children, ...props }) => (
    <span data-testid="badge" {...props}>{children}</span>
  ),
}));

vi.mock('../../components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }) => (
    <div data-testid="tabs" data-value={value}>
      <input
        type="hidden"
        value={value}
        onChange={(e) => onValueChange?.(e.target.value)}
        data-testid="tabs-input"
      />
      {children}
    </div>
  ),
  TabsContent: ({ children, value }) => (
    <div data-testid="tabs-content" data-value={value}>
      {children}
    </div>
  ),
  TabsList: ({ children }) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  TabsTrigger: ({ children, value, onClick }) => (
    <button
      data-testid="tabs-trigger"
      data-value={value}
      onClick={() => onClick?.()}
    >
      {children}
    </button>
  ),
}));

vi.mock('../ApprovalCenter/StatCards', () => ({
  default: () => (
    <div data-testid="stat-cards">
      <span>Stat Cards Rendered</span>
    </div>
  ),
}));

vi.mock('../ApprovalCenter/FilterBar', () => ({
  default: ({ searchText, setSearchText }) => (
    <div data-testid="filter-bar">
      <input
        placeholder="Search"
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        data-testid="search-input"
      />
    </div>
  ),
}));

vi.mock('../ApprovalCenter/PendingList', () => ({
  default: () => (
    <div data-testid="pending-list">
      <span>Pending List Rendered</span>
    </div>
  ),
}));

vi.mock('../ApprovalCenter/InitiatedList', () => ({
  default: () => (
    <div data-testid="initiated-list">
      <span>Initiated List Rendered</span>
    </div>
  ),
}));

vi.mock('../ApprovalCenter/CcList', () => ({
  default: () => (
    <div data-testid="cc-list">
      <span>Cc List Rendered</span>
    </div>
  ),
}));

vi.mock('../ApprovalCenter/ProcessedList', () => ({
  default: () => (
    <div data-testid="processed-list">
      <span>Processed List Rendered</span>
    </div>
  ),
}));

vi.mock('../ApprovalCenter/QuickApprovalDialog', () => ({
  default: () => (
    <div data-testid="quick-approval-dialog">
      <span>Quick Approval Dialog Rendered</span>
    </div>
  ),
}));

// Mock the components used in ApprovalCenter
vi.mock('../ApprovalCenter/components', () => ({
  StatCards: () => (
    <div data-testid="stat-cards">
      <span>Stat Cards Rendered</span>
    </div>
  ),
  FilterBar: ({ searchText, setSearchText }) => (
    <div data-testid="filter-bar">
      <input 
        placeholder="Search" 
        value={searchText} 
        onChange={(e) => setSearchText(e.target.value)} 
        data-testid="search-input"
      />
    </div>
  ),
  PendingList: () => (
    <div data-testid="pending-list">
      <span>Pending List Rendered</span>
    </div>
  ),
  InitiatedList: () => (
    <div data-testid="initiated-list">
      <span>Initiated List Rendered</span>
    </div>
  ),
  CcList: () => (
    <div data-testid="cc-list">
      <span>Cc List Rendered</span>
    </div>
  ),
  ProcessedList: () => (
    <div data-testid="processed-list">
      <span>Processed List Rendered</span>
    </div>
  ),
  QuickApprovalDialog: () => (
    <div data-testid="quick-approval-dialog">
      <span>Quick Approval Dialog Rendered</span>
    </div>
  ),
}));

// Mock the hook
vi.mock('../ApprovalCenter/hooks', () => ({
  useApprovalCenter: () => ({
    items: [
      {
        id: 1,
        approvalNo: 'APR-2024-001',
        title: '项目立项审批',
        type: 'project_initiation',
        applicant: '张三',
        status: 'pending',
        currentApprover: '李四',
        submittedAt: '2024-02-15',
        priority: 'high'
      },
      {
        id: 2,
        approvalNo: 'APR-2024-002',
        title: '合同签订审批',
        type: 'contract',
        applicant: '王五',
        status: 'approved',
        currentApprover: null,
        submittedAt: '2024-02-10',
        priority: 'medium'
      }
    ],
    loading: false,
    error: null,
    pagination: {
      page: 1,
      pageSize: 20,
      total: 2,
      pages: 1,
    },
    counts: {
      pending: 1,
      initiated_pending: 1,
      unread_cc: 0,
      urgent: 0,
      total: 2,
    },
    tabBadges: {
      pending: 1,
      initiated: 1,
      cc: 0,
      processed: 0,
    },
    activeTab: 'pending',
    filters: {
      urgency: 'all',
      templateId: null,
      keyword: '',
    },
    switchTab: vi.fn(),
    updateFilters: vi.fn(),
    refresh: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    markCcAsRead: vi.fn(),
  }),
  APPROVAL_TABS: {
    PENDING: 'pending',
    INITIATED: 'initiated',
    CC: 'cc',
    PROCESSED: 'processed',
  }
}));

vi.mock('../ApprovalCenter/hooks/useApprovalCenter', () => ({
  useApprovalCenter: () => ({
    items: [
      {
        id: 1,
        approvalNo: 'APR-2024-001',
        title: '项目立项审批',
        type: 'project_initiation',
        applicant: '张三',
        status: 'pending',
        currentApprover: '李四',
        submittedAt: '2024-02-15',
        priority: 'high'
      },
      {
        id: 2,
        approvalNo: 'APR-2024-002',
        title: '合同签订审批',
        type: 'contract',
        applicant: '王五',
        status: 'approved',
        currentApprover: null,
        submittedAt: '2024-02-10',
        priority: 'medium'
      }
    ],
    loading: false,
    error: null,
    pagination: {
      page: 1,
      pageSize: 20,
      total: 2,
      pages: 1,
    },
    counts: {
      pending: 1,
      initiated_pending: 1,
      unread_cc: 0,
      urgent: 0,
      total: 2,
    },
    tabBadges: {
      pending: 1,
      initiated: 1,
      cc: 0,
      processed: 0,
    },
    activeTab: 'pending',
    filters: {
      urgency: 'all',
      templateId: null,
      keyword: '',
    },
    switchTab: vi.fn(),
    updateFilters: vi.fn(),
    refresh: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    markCcAsRead: vi.fn(),
  }),
  APPROVAL_TABS: {
    PENDING: 'pending',
    INITIATED: 'initiated',
    CC: 'cc',
    PROCESSED: 'processed',
  }
}));

// Mock framer-motion
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

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});


import ApprovalCenter from '../ApprovalCenter';

describe('ApprovalCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the page header with correct title and description', () => {
    render(
      <MemoryRouter>
        <ApprovalCenter />
      </MemoryRouter>
    );

    expect(screen.getByTestId('page-header')).toBeInTheDocument();
    expect(screen.getByText('审批中心')).toBeInTheDocument();
    expect(screen.getByText('统一审批管理平台')).toBeInTheDocument();
  });

  it('should render header action buttons', () => {
    render(
      <MemoryRouter>
        <ApprovalCenter />
      </MemoryRouter>
    );

    expect(screen.getByTestId('header-actions')).toBeInTheDocument();
    
    // Check that refresh button exists
    const buttons = screen.getAllByTestId('button');
    expect(buttons).toHaveLength(1); // Only refresh button
    
    const refreshBtn = buttons[0];
    expect(refreshBtn).toHaveTextContent('刷新');
    expect(refreshBtn.getAttribute('data-variant')).toBe('outline');
  });

  it('should render statistics cards', () => {
    render(
      <MemoryRouter>
        <ApprovalCenter />
      </MemoryRouter>
    );

    expect(screen.getByTestId('stat-cards')).toBeInTheDocument();
    expect(screen.getByText('Stat Cards Rendered')).toBeInTheDocument();
  });

  it('should render tabs with correct default value', () => {
    render(
      <MemoryRouter>
        <ApprovalCenter />
      </MemoryRouter>
    );

    expect(screen.getByTestId('tabs')).toBeInTheDocument();
    expect(screen.getByTestId('tabs-list')).toBeInTheDocument();
    
    const triggers = screen.getAllByTestId('tabs-trigger');
    expect(triggers).toHaveLength(4);
    expect(triggers[0]).toHaveTextContent('待我审批');
    expect(triggers[0].getAttribute('data-value')).toBe('pending');
    expect(triggers[1]).toHaveTextContent('我发起的');
    expect(triggers[1].getAttribute('data-value')).toBe('initiated');
    expect(triggers[2]).toHaveTextContent('抄送我的');
    expect(triggers[2].getAttribute('data-value')).toBe('cc');
    expect(triggers[3]).toHaveTextContent('已处理');
    expect(triggers[3].getAttribute('data-value')).toBe('processed');
  });

  it('should render pending tab content by default', () => {
    render(
      <MemoryRouter>
        <ApprovalCenter />
      </MemoryRouter>
    );

    // Check that at least one tabs-content exists
    const tabContents = screen.getAllByTestId('tabs-content');
    expect(tabContents.length).toBeGreaterThan(0);
    
    // Find the one with pending value
    const pendingTabContent = tabContents.find(content => content.getAttribute('data-value') === 'pending');
    expect(pendingTabContent).toBeTruthy();
    
    expect(screen.getByTestId('pending-list')).toBeInTheDocument();
    expect(screen.getByText('Pending List Rendered')).toBeInTheDocument();
  });
});
