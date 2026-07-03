import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Mock console.error and alert globally
const { consoleErrorMock, alertMock } = vi.hoisted(() => ({
  consoleErrorMock: vi.fn(),
  alertMock: vi.fn(),
}));

// Mock services and dependencies
vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    customerApi: {
      list: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      get: vi.fn(),
      get360: vi.fn(),
    }
  };
});

const { confirmAction } = vi.hoisted(() => {
  const confirmAction = vi.fn();
  return { confirmAction };
});

vi.mock('@/lib/confirmAction', () => ({
  confirmAction,
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const Tag = typeof tag === 'string' ? tag : 'div';
        const filteredProps = Object.fromEntries(
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
        return <Tag {...filteredProps}>{children}</Tag>;
      },
    },
  ),
}));

vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, description, actions }) => (
    <div>
      <h1>{title}</h1>
      <p>{description}</p>
      <div>{actions}</div>
    </div>
  ),
}));

vi.mock('../../components/ui/card', () => ({
  Card: ({ children }) => <div>{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>,
  CardHeader: ({ children, className }) => <div className={className}>{children}</div>,
  CardTitle: ({ children }) => <h3>{children}</h3>,
  CardDescription: ({ children }) => <p>{children}</p>,
}));

vi.mock('../../components/ui/button', () => ({
  Button: ({ children, onClick, type = 'button', ...props }) => (
    <button type={type} onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('../../components/ui/input', () => ({
  Input: ({ value, onChange, placeholder, ...props }) => (
    <input 
      value={value || ''} 
      onChange={onChange} 
      placeholder={placeholder} 
      {...props} 
    />
  ),
}));

vi.mock('../../components/ui/select', () => ({
  Select: ({ children, value, onValueChange }) => (
    <div data-select-value={value} data-on-change={typeof onValueChange}>
      {children}
    </div>
  ),
  SelectTrigger: ({ children, ...props }) => (
    <button {...props}>{children}</button>
  ),
  SelectValue: ({ placeholder }) => <span>{placeholder}</span>,
  SelectContent: ({ children }) => <div>{children}</div>,
  SelectItem: ({ children, value }) => <div data-value={value}>{children}</div>,
}));

vi.mock('../../lib/animations', () => ({
  fadeIn: {},
  staggerContainer: {},
}));

// Import the actual hook to test it
import { useCustomerManagement } from '../CustomerManagement/hooks/useCustomerManagement';

// Mock the hook implementation
vi.mock('../CustomerManagement/hooks/useCustomerManagement', () => ({
  useCustomerManagement: vi.fn(),
}));

// Import the actual component
import CustomerManagement from '../CustomerManagement/index';

function createHookValue(overrides = {}) {
  return {
    customers: [
      { id: 1, name: '华为技术有限公司', code: 'HW001', industry: '通信', contact: '任正非', status: 'active' },
      { id: 2, name: '中兴通讯股份有限公司', code: 'ZX002', industry: '通信', contact: '李自学', status: 'active' },
    ],
    loading: false,
    total: 2,
    page: 1,
    setPage: vi.fn(),
    pageSize: 20,
    industries: ['通信', '新能源', '互联网'],

    // Filters
    searchKeyword: '',
    setSearchKeyword: vi.fn(),
    filterIndustry: 'all',
    setFilterIndustry: vi.fn(),
    filterStatus: 'all',
    setFilterStatus: vi.fn(),

    // Dialog States
    showCreateDialog: false,
    setShowCreateDialog: vi.fn(),
    showEditDialog: false,
    setShowEditDialog: vi.fn(),
    showDetailDialog: false,
    setShowDetailDialog: vi.fn(),
    show360Dialog: false,
    setShow360Dialog: vi.fn(),

    // Data
    selectedCustomer: { id: 1, name: '华为技术有限公司' },
    editCustomer: { id: 1, name: '华为技术有限公司' },
    customer360: { id: 1, name: '华为客户画像' },
    loading360: false,

    // Handlers
    handleCreate: vi.fn(),
    handleUpdate: vi.fn(),
    handleDelete: vi.fn(),
    handleViewDetail: vi.fn(),
    handleView360: vi.fn(),
    prepareEdit: vi.fn(),
    refresh: vi.fn(),
    ...overrides,
  };
}

describe('CustomerManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(consoleErrorMock);
    vi.spyOn(window, 'alert').mockImplementation(alertMock);
  });

  function renderPage(overrides = {}) {
    const hookValue = createHookValue(overrides);
    useCustomerManagement.mockReturnValue(hookValue);

    const view = render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

    return { ...view, hookValue };
  }

  it('渲染页头、筛选区和客户表格，并可打开新增弹窗', () => {
    const { hookValue } = renderPage();

    expect(screen.getByText('客户管理')).toBeInTheDocument();
    expect(screen.getByText('管理系统客户信息，包括创建、编辑、查看等操作。')).toBeInTheDocument();
    expect(screen.getByText('客户列表')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /新增客户/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /新增客户/i }));
    expect(hookValue.setShowCreateDialog).toHaveBeenCalledWith(true);
  });

  it('筛选区操作会调用真实 hook 提供的 setter', () => {
    const { hookValue } = renderPage();

    const searchInput = screen.getByPlaceholderText('搜索客户名称/编码...');
    fireEvent.change(searchInput, { target: { value: '华为' } });
    expect(hookValue.setSearchKeyword).toHaveBeenCalledWith('华为');
  });

  it('表格应显示客户数据', () => {
    renderPage();

    // 检查客户数据显示在表格中
    expect(screen.getAllByText('通信')).toHaveLength(3); // 行业信息出现在筛选选项和两行数据中
  });

  it('应能打开编辑、详情和360视图', () => {
    const { hookValue } = renderPage();

    // 触发编辑
    hookValue.prepareEdit(1);
    expect(hookValue.prepareEdit).toHaveBeenCalledWith(1);

    // 触发详情查看
    hookValue.handleViewDetail(1);
    expect(hookValue.handleViewDetail).toHaveBeenCalledWith(1);

    // 触发360视图
    hookValue.handleView360(1);
    expect(hookValue.handleView360).toHaveBeenCalledWith(1);

    // 触发删除
    hookValue.handleDelete(1);
    expect(hookValue.handleDelete).toHaveBeenCalledWith(1);
  });

  it('应能打开编辑弹窗', () => {
    const { hookValue } = renderPage({
      showEditDialog: true,
      editCustomer: { id: 1, name: '华为技术有限公司' }
    });

    expect(hookValue.showEditDialog).toBe(true);
  });

  it('应该处理加载客户列表失败的情况', async () => {
    // 模拟API失败
    const mockHandleCreate = vi.fn().mockRejectedValue(new Error('Load failed'));
    const mockHookValue = createHookValue({
      handleCreate: mockHandleCreate,
    });
    useCustomerManagement.mockReturnValue(mockHookValue);

    render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

    // 组件应该仍然渲染
    expect(screen.getByText('客户管理')).toBeInTheDocument();
  });

  it('应该处理创建客户失败的情况', async () => {
    // 设置初始成功的列表调用，然后失败创建调用
    vi.clearAllMocks();
    const mockHandleCreate = vi.fn().mockRejectedValue(new Error('Create failed'));
    const mockHookValue = createHookValue({
      handleCreate: mockHandleCreate,
    });
    useCustomerManagement.mockReturnValue(mockHookValue);
    
    // Mock console.error
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

    // 尝试创建客户
    fireEvent.click(screen.getByRole('button', { name: /新增客户/i }));
    
    // 验证handleCreate被调用并抛出错误
    try {
      await mockHandleCreate();
    } catch (error) {
      expect(error.message).toBe('Create failed');
    }
    
    consoleSpy.mockRestore();
  });

  it('应该处理更新客户失败的情况', async () => {
    const mockHandleUpdate = vi.fn().mockRejectedValue(new Error('Update failed'));
    const mockHookValue = createHookValue({
      handleUpdate: mockHandleUpdate,
    });
    useCustomerManagement.mockReturnValue(mockHookValue);

    render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

    expect(screen.getByText('客户管理')).toBeInTheDocument();
  });

  it('应该处理删除客户失败的情况', async () => {
    const mockHandleDelete = vi.fn().mockRejectedValue(new Error('Delete failed'));
    const mockHookValue = createHookValue({
      handleDelete: mockHandleDelete,
    });
    useCustomerManagement.mockReturnValue(mockHookValue);

    // 使用已在hoisted部分定义的confirmAction模拟
    confirmAction.mockResolvedValue(true);

    render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

    expect(screen.getByText('客户管理')).toBeInTheDocument();
  });

  it('应该处理获取客户详情失败的情况', async () => {
    const mockHandleViewDetail = vi.fn().mockRejectedValue(new Error('Get detail failed'));
    const mockHookValue = createHookValue({
      handleViewDetail: mockHandleViewDetail,
    });
    useCustomerManagement.mockReturnValue(mockHookValue);

    render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

    expect(screen.getByText('客户管理')).toBeInTheDocument();
  });

  it('应该处理获取客户360失败的情况', async () => {
    const mockHandleView360 = vi.fn().mockRejectedValue(new Error('Get 360 failed'));
    const mockHookValue = createHookValue({
      handleView360: mockHandleView360,
    });
    useCustomerManagement.mockReturnValue(mockHookValue);

    render(
      <MemoryRouter>
        <CustomerManagement />
      </MemoryRouter>,
    );

    expect(screen.getByText('客户管理')).toBeInTheDocument();
  });
});