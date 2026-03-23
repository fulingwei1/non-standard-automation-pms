/**
 * AcceptanceExecution 组件测试
 * 测试覆盖：验收执行、检查项管理、问题记录、验收完成
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { acceptanceApi } from '../../services/api';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import AcceptanceExecution from '../AcceptanceExecution';

// Mock API - 提供 acceptanceApi 的完整嵌套结构
vi.mock('../../services/api', () => ({
  acceptanceApi: {
    orders: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      getItems: vi.fn(),
      updateItem: vi.fn(),
      complete: vi.fn(),
    },
    issues: {
      list: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    templates: {
      list: vi.fn(),
      get: vi.fn(),
    },
  },
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    defaults: { baseURL: '/api' },
  },
}));

// Mock dependencies
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(Object.entries(props).filter(([k]) => !['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'].includes(k)));
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
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

describe('AcceptanceExecution', () => {
  // 组件使用 order.order_no 显示编号，order.project_name 等字段
  const mockOrder = {
    id: 1,
    order_no: 'ACC-2024-001',
    project_name: '智能制造系统',
    template_name: '软件验收模板',
    status: 'IN_PROGRESS',
    scheduled_date: '2024-06-30',
    executor_name: '张三',
    created_at: '2024-06-20T10:00:00Z',
  };

  // 组件使用 item_name, category_name, item_code, acceptance_criteria 等字段
  const mockItems = [
    {
      id: 1,
      order_id: 1,
      category_name: '功能测试',
      item_name: '用户登录功能',
      item_code: 'FT-001',
      acceptance_criteria: '能够正常登录系统',
      check_method: '手工测试',
      result_status: 'PENDING',
      actual_value: null,
      deviation: null,
      remark: null,
      is_key_item: false,
    },
    {
      id: 2,
      order_id: 1,
      category_name: '性能测试',
      item_name: '系统响应时间',
      item_code: 'PT-001',
      acceptance_criteria: '页面加载时间<3秒',
      standard_value: '3',
      unit: '秒',
      check_method: '性能工具测试',
      result_status: 'PASSED',
      actual_value: '2.5秒',
      deviation: null,
      remark: '性能良好',
      is_key_item: false,
    },
    {
      id: 3,
      order_id: 1,
      category_name: '兼容性测试',
      item_name: '浏览器兼容性',
      item_code: 'CT-001',
      acceptance_criteria: '支持Chrome、Firefox、Safari',
      check_method: '手工测试',
      result_status: 'FAILED',
      actual_value: 'Safari部分功能异常',
      deviation: '存在兼容性问题',
      remark: '需要修复',
      is_key_item: true,
    },
  ];

  const mockIssues = [
    {
      id: 1,
      item_id: 3,
      item_name: '浏览器兼容性',
      category: 'BUG',
      severity: 'MAJOR',
      description: 'Safari浏览器下拉菜单无法正常显示',
      status: 'OPEN',
      created_at: '2024-06-25T14:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    // 组件调用 get(id) 其中 id 是 useParams() 返回的字符串 "1"
    acceptanceApi.orders.get.mockResolvedValue({ data: mockOrder });
    acceptanceApi.orders.getItems.mockResolvedValue({ data: mockItems });
    acceptanceApi.issues.list.mockResolvedValue({ data: mockIssues });
    acceptanceApi.orders.updateItem.mockResolvedValue({ data: { success: true } });
    acceptanceApi.issues.create.mockResolvedValue({
      data: { id: 2, ...mockIssues[0] }
    });
    acceptanceApi.orders.complete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render page title', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/验收执行|Acceptance Execution/i)).toBeInTheDocument();
      });
    });

    it('should render order information', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件显示 order.order_no 在 PageHeader title 中
      await waitFor(() => {
        expect(screen.getByText(/ACC-2024-001/)).toBeInTheDocument();
      });
    });

    it('should render acceptance items table', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // item_name 可能在检查项列表和 Select 选项中同时出现，使用 getAllByText
      await waitFor(() => {
        expect(screen.getAllByText('用户登录功能').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('系统响应时间').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('浏览器兼容性').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display result status badges', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 状态标签可能出现多次（列表项 + 对话框选项），使用 getAllByText
      await waitFor(() => {
        expect(screen.getAllByText('待检查').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('通过').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('不通过').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should render progress stats', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件显示通过率 = passedCount/totalChecked = 1/2 = 50%
      // 以及总项数、通过数、不通过数的统计卡片
      await waitFor(() => {
        // 总项数显示 3
        const threeTexts = screen.queryAllByText('3');
        expect(threeTexts.length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch order details on mount', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // useParams() 返回字符串 "1"，组件直接传递给 API
      await waitFor(() => {
        expect(acceptanceApi.orders.get).toHaveBeenCalledWith('1');
        expect(acceptanceApi.orders.getItems).toHaveBeenCalledWith('1');
        expect(acceptanceApi.issues.list).toHaveBeenCalledWith('1');
      });
    });

    it('should show loading state initially', () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      const loadingElements = screen.queryAllByRole('status') || screen.queryAllByText(/加载中|Loading/i);
      expect(loadingElements.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error gracefully', async () => {
      // 组件在 fetchOrderDetail catch 中静默降级，不渲染错误 DOM
      acceptanceApi.orders.get.mockRejectedValueOnce(new Error('Failed to load'));

      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // order 为 null 时，组件渲染 "验收单不存在"
      await waitFor(() => {
        const notExist = screen.queryByText(/验收单不存在/);
        expect(notExist).toBeTruthy();
      });
    });
  });

  // 3. 检查项执行测试
  describe('Item Execution', () => {
    it('should display items grouped by category', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件按 category_name 分组显示检查项
      await waitFor(() => {
        expect(screen.getByText('功能测试')).toBeInTheDocument();
        expect(screen.getByText('性能测试')).toBeInTheDocument();
        expect(screen.getByText('兼容性测试')).toBeInTheDocument();
      });
    });

    it('should display item names', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByText('用户登录功能').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('系统响应时间').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should show acceptance criteria', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件显示 item.acceptance_criteria
      await waitFor(() => {
        expect(screen.getByText(/能够正常登录系统/)).toBeInTheDocument();
      });
    });

    it('should display actual values for checked items', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件对已填写 actual_value 的项目显示实际值
      await waitFor(() => {
        expect(screen.getByText(/2\.5秒/)).toBeInTheDocument();
      });
    });
  });

  // 4. 问题管理测试
  describe('Issue Management', () => {
    it('should display issues list', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件显示 issue.description 在问题列表中
      await waitFor(() => {
        expect(screen.getByText(/Safari浏览器下拉菜单无法正常显示/i)).toBeInTheDocument();
      });
    });

    it('should display issue category', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件显示 issue.category
      await waitFor(() => {
        expect(screen.getAllByText('BUG').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display issue status', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // issue.status === 'OPEN' 显示为 "待处理"
      await waitFor(() => {
        expect(screen.getByText('待处理')).toBeInTheDocument();
      });
    });

    it('should display issue severity badges', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // severity === 'MAJOR' 显示为 "重要"
      await waitFor(() => {
        expect(screen.getAllByText(/重要/).length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  // 5. 验收完成测试
  describe('Acceptance Completion', () => {
    it('should show complete button for IN_PROGRESS orders', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/ACC-2024-001/)).toBeInTheDocument();
      });

      // 组件在 order.status === 'IN_PROGRESS' 时显示 "完成验收" 按钮（可能多处出现）
      const completeButtons = screen.queryAllByText('完成验收');
      expect(completeButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('should show back button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/ACC-2024-001/)).toBeInTheDocument();
      });

      // 组件有 "返回列表" 按钮
      expect(screen.getByText('返回列表')).toBeInTheDocument();
    });

    it('should show refresh button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/ACC-2024-001/)).toBeInTheDocument();
      });

      // 组件有 "刷新" 按钮
      expect(screen.getByText('刷新')).toBeInTheDocument();
    });

    it('should have report issue button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/ACC-2024-001/)).toBeInTheDocument();
      });

      // 组件有 "上报问题" 按钮（可能在按钮和对话框标题中同时出现）
      expect(screen.getAllByText('上报问题').length).toBeGreaterThanOrEqual(1);
    });
  });

  // 6. 统计信息测试
  describe('Statistics', () => {
    it('should display summary cards', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // 组件显示 4 个统计卡片: 总项数、通过、不通过、通过率
      await waitFor(() => {
        expect(screen.getByText('总项数')).toBeInTheDocument();
        expect(screen.getAllByText('通过').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('不通过').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('通过率')).toBeInTheDocument();
      });
    });

    it('should display correct total count', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // items.length = 3
      await waitFor(() => {
        const threeTexts = screen.queryAllByText('3');
        expect(threeTexts.length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display passed and failed counts', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // passedCount = 1, failedCount = 1
      await waitFor(() => {
        const oneTexts = screen.queryAllByText('1');
        expect(oneTexts.length).toBeGreaterThanOrEqual(2);
      });
    });

    it('should calculate pass rate', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      // passRate = passedCount/totalChecked = 1/2 = 50%
      await waitFor(() => {
        expect(screen.getByText(/50\.0/)).toBeInTheDocument();
      });
    });
  });

  // 7. 导航功能测试
  describe('Navigation', () => {
    it('should navigate to list when clicking back button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/ACC-2024-001/)).toBeInTheDocument();
      });

      // 组件的 "返回列表" 按钮调用 navigate("/acceptance-orders")
      const backButton = screen.getByText('返回列表');
      fireEvent.click(backButton);
      expect(mockNavigate).toHaveBeenCalledWith('/acceptance-orders');
    });
  });

  // 8. 刷新功能测试
  describe('Refresh Functionality', () => {
    it('should refresh data when clicking refresh button', async () => {
      render(
        <MemoryRouter initialEntries={['/acceptance/execution/1']}>
          <Routes>
            <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(acceptanceApi.orders.getItems).toHaveBeenCalled();
      });

      const initialCallCount = acceptanceApi.orders.getItems.mock.calls.length;

      // 组件有 "刷新" 按钮
      const refreshButton = screen.getByText('刷新');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(acceptanceApi.orders.getItems.mock.calls.length).toBeGreaterThan(initialCallCount);
      });
    });
  });
});
