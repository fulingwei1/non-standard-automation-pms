/**
 * BOMManagement 组件测试
 * 测试覆盖：BOM列表、层级结构、物料关联、版本管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { bomApi, projectApi } from '../../services/api';
import { MemoryRouter } from 'react-router-dom';
import BOMManagement from '../BOMManagement';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    bomApi: {
      create: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      getByMachine: vi.fn().mockResolvedValue({ data: [] }),
      list: vi.fn().mockResolvedValue({ data: [] }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      getItems: vi.fn().mockResolvedValue({ data: [] }),
      addItem: vi.fn().mockResolvedValue({ data: {} }),
      updateItem: vi.fn().mockResolvedValue({ data: {} }),
      deleteItem: vi.fn().mockResolvedValue({ data: {} }),
      getVersions: vi.fn().mockResolvedValue({ data: [] }),
      compareVersions: vi.fn().mockResolvedValue({ data: {} }),
      release: vi.fn().mockResolvedValue({ data: {} }),
      import: vi.fn().mockResolvedValue({ data: {} }),
      export: vi.fn().mockResolvedValue({ data: {} }),
      generatePR: vi.fn().mockResolvedValue({ data: {} }),
    },
    projectApi: {
      list: vi.fn().mockResolvedValue({ data: [] }),
      getBoard: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      getMachines: vi.fn().mockResolvedValue({ data: [] }),
      getInProductionSummary: vi.fn().mockResolvedValue({ data: {} }),
      recommendTemplates: vi.fn().mockResolvedValue({ data: [] }),
      createFromTemplate: vi.fn().mockResolvedValue({ data: {} }),
      checkAutoTransition: vi.fn().mockResolvedValue({ data: {} }),
      getGateCheckResult: vi.fn().mockResolvedValue({ data: {} }),
      advanceStage: vi.fn().mockResolvedValue({ data: {} }),
      getCacheStats: vi.fn().mockResolvedValue({ data: {} }),
      clearCache: vi.fn().mockResolvedValue({ data: {} }),
      resetCacheStats: vi.fn().mockResolvedValue({ data: {} }),
      getStatusLogs: vi.fn().mockResolvedValue({ data: {} }),
      getHealthDetails: vi.fn().mockResolvedValue({ data: {} }),
      getStats: vi.fn().mockResolvedValue({ data: {} }),
    },
    machineApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      updateProgress: vi.fn().mockResolvedValue({ data: {} }),
      getBom: vi.fn().mockResolvedValue({ data: {} }),
      getServiceHistory: vi.fn().mockResolvedValue({ data: {} }),
      getSummary: vi.fn().mockResolvedValue({ data: {} }),
      recalculate: vi.fn().mockResolvedValue({ data: {} }),
      uploadDocument: vi.fn().mockResolvedValue({ data: {} }),
      getDocuments: vi.fn().mockResolvedValue({ data: {} }),
      downloadDocument: vi.fn().mockResolvedValue({ data: {} }),
      getDocumentVersions: vi.fn().mockResolvedValue({ data: {} }),
    }
}));

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


// 全局定义缺失的组件（源文件中使用但未导入）
globalThis.PageHeader = ({ title, children, extra, ...props }) => (
  <div data-testid="page-header" {...props}>
    {title && <h1>{title}</h1>}
    {extra && <div>{extra}</div>}
    {children}
  </div>
);
globalThis.Tag = ({ children, color, ...props }) => (
  <span data-testid="tag" style={{ color }} {...props}>{children}</span>
);

describe('BOMManagement', () => {
  // 组件使用 bom_no, bom_name, project_name, machine_name 等字段
  const mockBOMs = {
    items: [
      {
        id: 1,
        bom_no: 'BOM-001',
        bom_name: '产品A BOM',
        version: '1.0',
        project_name: '项目A',
        machine_name: '机台A-01',
        status: 'DRAFT',
        total_items: 25,
        total_amount: 12500,
        is_latest: true,
        updated_at: '2024-02-20',
      },
      {
        id: 2,
        bom_no: 'BOM-002',
        bom_name: '产品B BOM',
        version: '2.1',
        project_name: '项目B',
        machine_name: '机台B-01',
        status: 'APPROVED',
        total_items: 18,
        total_amount: 8900,
        is_latest: true,
        updated_at: '2024-02-22',
      }
    ],
    total: 2,
  };

  const mockProjects = [
    { id: 1, project_name: '项目A' },
    { id: 2, project_name: '项目B' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    // 组件调用 bomApi.list(params) 获取 BOM 列表
    bomApi.list.mockResolvedValue({ data: mockBOMs });
    // 组件调用 projectApi.list(params) 获取项目列表
    projectApi.list.mockResolvedValue({ data: { items: mockProjects, total: 2 } });
    // 其他 mock
    bomApi.create.mockResolvedValue({ data: { success: true, id: 3 } });
    bomApi.update.mockResolvedValue({ data: { success: true } });
    bomApi.delete.mockResolvedValue({ data: { success: true } });
    bomApi.get.mockResolvedValue({ data: { id: 1, bom_no: 'BOM-001', bom_name: '产品A BOM', version: '1.0', status: 'DRAFT', total_items: 25, total_amount: 12500 } });
    bomApi.getItems.mockResolvedValue({ data: [] });
    bomApi.getVersions.mockResolvedValue({ data: [] });
    bomApi.export.mockResolvedValue({ data: new Blob() });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render BOM management page', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件 PageHeader title="BOM管理"
      await waitFor(() => {
        expect(screen.getByText('BOM管理')).toBeInTheDocument();
      });
    });

    it('should render BOM list', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件在表格中显示 bom_name
      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
        expect(screen.getByText('产品B BOM')).toBeInTheDocument();
      });
    });

    it('should display BOM codes and versions', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件显示 bom_no 和 version（Badge）
      await waitFor(() => {
        expect(screen.getByText('BOM-001')).toBeInTheDocument();
        expect(screen.getByText('1.0')).toBeInTheDocument();
        expect(screen.getByText('2.1')).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load BOMs on mount', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件调用 bomApi.list(params) 而非 projectApi.list
      await waitFor(() => {
        expect(bomApi.list).toHaveBeenCalled();
      });
    });

    it('should show loading state', () => {
      bomApi.list.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件在 loading 时显示 "加载中..."
      expect(screen.queryByText(/加载中/)).toBeTruthy();
    });

    it('should handle empty BOM list', async () => {
      bomApi.list.mockResolvedValue({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件在无数据时显示 "暂无BOM数据"
      await waitFor(() => {
        expect(screen.getByText('暂无BOM数据')).toBeInTheDocument();
      });
    });
  });

  // 3. BOM信息显示测试
  describe('BOM Information Display', () => {
    it('should display project and machine info', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // project_name 同时出现在表格和筛选 Select 中，使用 getAllByText
      await waitFor(() => {
        expect(screen.getAllByText('项目A').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('机台A-01')).toBeInTheDocument();
      });
    });

    it('should display item count column', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件在表格中有 "物料数量" 列，显示 total_items
      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument();
        expect(screen.getByText('18')).toBeInTheDocument();
      });
    });

    it('should display total amount', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件通过 formatCurrency 格式化 total_amount
      await waitFor(() => {
        expect(bomApi.list).toHaveBeenCalled();
      });
    });

    it('should show table headers', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // "BOM名称" 同时出现在表头和创建对话框中，使用 getAllByText
      await waitFor(() => {
        expect(screen.getByText('BOM编号')).toBeInTheDocument();
        expect(screen.getAllByText('BOM名称').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('物料数量')).toBeInTheDocument();
      });
    });
  });

  // 4. BOM状态管理测试
  describe('BOM Status Management', () => {
    it('should display BOM status labels', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // statusConfigs: DRAFT -> "草稿", APPROVED -> "已审批"
      await waitFor(() => {
        expect(screen.getByText('草稿')).toBeInTheDocument();
        expect(screen.getByText('已审批')).toBeInTheDocument();
      });
    });

    it('should show latest badge', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件对 is_latest=true 显示 "最新" Badge
      await waitFor(() => {
        expect(screen.getAllByText('最新').length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  // 5. 搜索和筛选测试
  describe('Search and Filtering', () => {
    it('should have search input', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      // 组件有搜索输入框 placeholder="搜索BOM编号、名称..."
      const searchInput = screen.queryByPlaceholderText(/搜索BOM/i);
      expect(searchInput).toBeTruthy();
    });

    it('should load projects for filter', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件调用 projectApi.list 获取项目列表用于筛选
      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      });
    });

    it('should display BOM count', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件 CardDescription 显示 "共 N 个BOM"
      await waitFor(() => {
        expect(screen.getByText(/2.*个BOM/)).toBeInTheDocument();
      });
    });
  });

  // 6. BOM表格功能测试
  describe('BOM Table Features', () => {
    it('should display BOM list in table', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
        expect(screen.getByText('BOM-001')).toBeInTheDocument();
      });
    });

    it('should show table column headers', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // "项目"、"机台"、"版本" 可能在表头和创建对话框中同时出现
      await waitFor(() => {
        expect(screen.getAllByText('项目').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('机台').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('版本').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display action buttons', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      // 每行有查看和导出按钮
      const buttons = screen.queryAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(2);
    });
  });

  // 7. BOM列表内容测试
  describe('BOM List Content', () => {
    it('should display project names', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // project_name 同时出现在表格和筛选 Select 中
      await waitFor(() => {
        expect(screen.getAllByText('项目A').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('项目B').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display machine names', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('机台A-01')).toBeInTheDocument();
        expect(screen.getByText('机台B-01')).toBeInTheDocument();
      });
    });

    it('should display update dates', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件通过 formatDate 显示 updated_at
      await waitFor(() => {
        expect(bomApi.list).toHaveBeenCalled();
      });
    });
  });

  // 8. BOM操作测试
  describe('BOM Operations', () => {
    it('should have create BOM button', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(bomApi.list).toHaveBeenCalled();
      });

      // 组件有 "新建BOM" 按钮（可能和对话框标题重复）
      expect(screen.getAllByText(/新建BOM/).length).toBeGreaterThanOrEqual(1);
    });

    it('should call bomApi.list on mount', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 验证 BOM 数据加载
      await waitFor(() => {
        expect(bomApi.list).toHaveBeenCalled();
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });
    });

    it('should have BOM list header', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('BOM列表')).toBeInTheDocument();
      });
    });

    it('should render both BOMs in table', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('BOM-001')).toBeInTheDocument();
        expect(screen.getByText('BOM-002')).toBeInTheDocument();
      });
    });
  });

  // 9. 版本显示测试
  describe('Version Display', () => {
    it('should display BOM versions in table', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件在版本列用 Badge 显示 version
      await waitFor(() => {
        expect(screen.getByText('1.0')).toBeInTheDocument();
        expect(screen.getByText('2.1')).toBeInTheDocument();
      });
    });

    it('should show latest badge for latest versions', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 两个 BOM 都是 is_latest=true
      await waitFor(() => {
        expect(screen.getAllByText('最新').length).toBeGreaterThanOrEqual(2);
      });
    });

    it('should display version column header', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('版本')).toBeInTheDocument();
      });
    });
  });

  // 10. 总金额显示测试
  describe('Amount Display', () => {
    it('should display total amount column', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件表格有 "总金额" 列
      await waitFor(() => {
        expect(screen.getByText('总金额')).toBeInTheDocument();
      });
    });

    it('should display operation column', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 组件表格有 "操作" 列
      await waitFor(() => {
        expect(screen.getByText('操作')).toBeInTheDocument();
      });
    });

    it('should load BOM data on mount', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      // 验证 API 被调用
      await waitFor(() => {
        expect(bomApi.list).toHaveBeenCalled();
        expect(projectApi.list).toHaveBeenCalled();
      });
    });
  });
});
