import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PermissionManagement from '../PermissionManagement';

const { mockUsePermissionData } = vi.hoisted(() => ({
  mockUsePermissionData: vi.fn(),
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
}));

vi.mock('../PermissionManagement/usePermissionData', () => ({
  usePermissionData: mockUsePermissionData,
}));

vi.mock('../PermissionManagement/StatsCards', () => ({
  StatsCards: ({ stats }) => (
    <div data-testid="stats-cards">
      权限总数:{stats.total}|模块数量:{stats.modules}|启用权限:{stats.active}
    </div>
  ),
}));

vi.mock('../PermissionManagement/UsageStats', () => ({
  UsageStats: ({ permissionUsageStats, unusedCount }) => (
    <div data-testid="usage-stats">
      常用:{permissionUsageStats.mostUsed.length}|未分配:{unusedCount}
    </div>
  ),
}));

vi.mock('../PermissionManagement/SearchFilter', () => ({
  SearchFilter: ({
    searchKeyword,
    setSearchKeyword,
    filterModule,
    setFilterModule,
    modules,
  }) => (
    <div data-testid="search-filter">
      <input
        aria-label="搜索权限"
        value={searchKeyword}
        onChange={(e) => setSearchKeyword(e.target.value)}
      />
      <select
        aria-label="模块筛选"
        value={filterModule}
        onChange={(e) => setFilterModule(e.target.value)}
      >
        <option value="all">所有模块</option>
        {modules.map((module) => (
          <option key={module} value={module}>{module}</option>
        ))}
      </select>
    </div>
  ),
}));

vi.mock('../PermissionManagement/DemoAccountBanner', () => ({
  DemoAccountBanner: () => <div data-testid="demo-banner">演示账号限制</div>,
}));

vi.mock('../PermissionManagement/PermissionList', () => ({
  PermissionList: ({ loading, isDemoAccount, filteredPermissions, toggleModule, handleViewDetail }) => (
    <div data-testid="permission-list">
      <div>loading:{loading ? 'yes' : 'no'}</div>
      <div>demo:{isDemoAccount ? 'yes' : 'no'}</div>
      {Object.entries(filteredPermissions).map(([module, perms]) => (
        <div key={module}>
          <button onClick={() => toggleModule(module)}>{module}</button>
          {perms.map((perm) => (
            <button key={perm.id} onClick={() => handleViewDetail(perm)}>
              {perm.permission_code}
            </button>
          ))}
        </div>
      ))}
    </div>
  ),
}));

vi.mock('../PermissionManagement/PermissionDetailDialog', () => ({
  PermissionDetailDialog: ({ open, selectedPermission, onOpenChange }) => (
    <div data-testid="permission-detail-dialog">
      {open ? selectedPermission?.permission_code || 'open' : 'closed'}
      <button onClick={() => onOpenChange(false)}>close-dialog</button>
    </div>
  ),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <PermissionManagement />
    </MemoryRouter>,
  );
}

describe('PermissionManagement', () => {
  const baseHookValue = {
    loading: false,
    searchKeyword: '',
    setSearchKeyword: vi.fn(),
    filterModule: 'all',
    setFilterModule: vi.fn(),
    expandedModules: { user: true },
    selectedPermission: null,
    showDetailDialog: false,
    setShowDetailDialog: vi.fn(),
    permissionRoles: [],
    permissionUsageStats: {
      mostUsed: [{ permission_code: 'user:create', roleCount: 2 }],
      unused: [{ permission_code: 'project:delete' }],
    },
    isDemoAccount: false,
    modules: ['user', 'project'],
    filteredPermissions: {
      user: [
        { id: 1, permission_code: 'user:create' },
        { id: 2, permission_code: 'user:delete' },
      ],
    },
    stats: {
      total: 2,
      modules: 2,
      active: 2,
      unused: 1,
    },
    toggleModule: vi.fn(),
    handleViewDetail: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePermissionData.mockReturnValue(baseHookValue);
  });

  it('renders the real page skeleton from hook state', () => {
    renderPage();

    expect(screen.getByText('权限管理')).toBeInTheDocument();
    expect(screen.getByText('查看和管理系统中的所有权限配置')).toBeInTheDocument();
    expect(screen.getByTestId('stats-cards')).toHaveTextContent('权限总数:2|模块数量:2|启用权限:2');
    expect(screen.getByTestId('usage-stats')).toHaveTextContent('常用:1|未分配:1');
    expect(screen.getByText('user:create')).toBeInTheDocument();
    expect(screen.getByText('user:delete')).toBeInTheDocument();
  });

  it('wires search, module filtering, and detail actions back to the hook', () => {
    const setSearchKeyword = vi.fn();
    const setFilterModule = vi.fn();
    const toggleModule = vi.fn();
    const handleViewDetail = vi.fn();

    mockUsePermissionData.mockReturnValue({
      ...baseHookValue,
      setSearchKeyword,
      setFilterModule,
      toggleModule,
      handleViewDetail,
    });

    renderPage();

    fireEvent.change(screen.getByLabelText('搜索权限'), {
      target: { value: 'create' },
    });
    expect(setSearchKeyword).toHaveBeenCalledWith('create');

    fireEvent.change(screen.getByLabelText('模块筛选'), {
      target: { value: 'project' },
    });
    expect(setFilterModule).toHaveBeenCalledWith('project');

    fireEvent.click(screen.getByRole('button', { name: 'user' }));
    expect(toggleModule).toHaveBeenCalledWith('user');

    fireEvent.click(screen.getByRole('button', { name: 'user:create' }));
    expect(handleViewDetail).toHaveBeenCalledWith(
      expect.objectContaining({ id: 1, permission_code: 'user:create' }),
    );
  });

  it('renders demo account and detail dialog states from the real page', () => {
    mockUsePermissionData.mockReturnValue({
      ...baseHookValue,
      isDemoAccount: true,
      showDetailDialog: true,
      selectedPermission: { id: 1, permission_code: 'user:create' },
    });

    renderPage();

    expect(screen.getByTestId('demo-banner')).toBeInTheDocument();
    expect(screen.getByTestId('permission-list')).toHaveTextContent('demo:yes');
    expect(screen.getByTestId('permission-detail-dialog')).toHaveTextContent('user:create');
  });
});
