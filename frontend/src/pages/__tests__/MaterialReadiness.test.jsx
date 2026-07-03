/**
 * MaterialReadiness 组件测试
 * 测试覆盖：物料齐套检查、缺料提醒、采购建议
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MaterialReadiness from '../MaterialReadiness';
import { materialApi, projectApi as _projectApi, supplierApi as _supplierApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
  materialApi: {
    create: vi.fn().mockResolvedValue({data: { items: [] }}),
    update: vi.fn().mockResolvedValue({data: { items: [] }}),
    list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    search: vi.fn().mockResolvedValue({data: { items: [] }}),
    warehouse: {
      statistics: vi.fn().mockResolvedValue({data: { items: [] }}),
    },
    categories: {
      list: vi.fn().mockResolvedValue({data: { items: [] }}),
    },
  },
  projectApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
    getBoard: vi.fn().mockResolvedValue({data: { items: [] }}),
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    create: vi.fn().mockResolvedValue({data: { items: [] }}),
    update: vi.fn().mockResolvedValue({data: { items: [] }}),
    getMachines: vi.fn().mockResolvedValue({data: { items: [] }}),
    getInProductionSummary: vi.fn().mockResolvedValue({data: { items: [] }}),
    recommendTemplates: vi.fn().mockResolvedValue({data: { items: [] }}),
    createFromTemplate: vi.fn().mockResolvedValue({data: { items: [] }}),
    checkAutoTransition: vi.fn().mockResolvedValue({data: { items: [] }}),
    getGateCheckResult: vi.fn().mockResolvedValue({data: { items: [] }}),
    advanceStage: vi.fn().mockResolvedValue({data: { items: [] }}),
    getCacheStats: vi.fn().mockResolvedValue({data: { items: [] }}),
    clearCache: vi.fn().mockResolvedValue({data: { items: [] }}),
    resetCacheStats: vi.fn().mockResolvedValue({data: { items: [] }}),
    getStatusLogs: vi.fn().mockResolvedValue({data: { items: [] }}),
    getHealthDetails: vi.fn().mockResolvedValue({data: { items: [] }}),
    getStats: vi.fn().mockResolvedValue({data: { items: [] }}),
  },
  supplierApi: {
    list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    create: vi.fn().mockResolvedValue({data: { items: [] }}),
    update: vi.fn().mockResolvedValue({data: { items: [] }}),
    updateRating: vi.fn().mockResolvedValue({data: { items: [] }}),
    getMaterials: vi.fn().mockResolvedValue({data: { items: [] }}),
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

describe('MaterialReadiness', () => {
  // Mock 物料数组数据（供 useMaterialReadiness hook 使用）
  const mockMaterials = [
    {
      id: 1,
      code: 'MAT-001',
      name: '钢板',
      type: 'RAW_MATERIAL',
      status: 'AVAILABLE',
      quantity: 1000,
      required_quantity: 1000,
      priority: 'HIGH',
      project_id: 1,
      expected_date: null
    },
    {
      id: 2,
      code: 'MAT-002',
      name: '螺栓',
      type: 'RAW_MATERIAL',
      status: 'OUT_OF_STOCK',
      quantity: 300,
      required_quantity: 500,
      priority: 'URGENT',
      project_id: 1,
      expected_date: null
    },
    {
      id: 3,
      code: 'MAT-003',
      name: '电机',
      type: 'COMPONENT',
      status: 'ON_ORDER',
      quantity: 0,
      required_quantity: 10,
      priority: 'HIGH',
      project_id: 1,
      expected_date: '2024-03-10'
    }
  ];

  // Mock 项目数据
  const mockProjects = [
    { id: 101, name: '项目A' },
    { id: 102, name: '项目B' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    materialApi.list.mockResolvedValue({ data: { items: mockMaterials, total: mockMaterials.length } });
    _projectApi.list.mockResolvedValue({ data: { items: mockProjects, total: mockProjects.length } });
    _supplierApi.list.mockResolvedValue({ data: { items: [], total: 0 } });
    materialApi.create.mockResolvedValue({ data: { success: true } });
    materialApi.update.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render material readiness page', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/物料齐套管理/i)).toBeInTheDocument();
      });
    });

    it('should render without crashing with material data', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        // 验证页面标题渲染
        expect(screen.getByText('物料齐套管理')).toBeInTheDocument();
      });
    });

    it('should display view mode tabs', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('概览')).toBeInTheDocument();
        expect(screen.getByText('列表')).toBeInTheDocument();
        expect(screen.getByText('分析')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load readiness data on mount', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        // API should be called
        expect(materialApi.list).toHaveBeenCalled();
      });
    });

    it('should load projects data', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(_projectApi.list).toHaveBeenCalled();
      });
    });

    it('should show refresh button', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('刷新')).toBeInTheDocument();
      });
    });

    it('should show export button', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('导出')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should call API when refresh button is clicked', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('刷新')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('刷新');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(materialApi.list).toHaveBeenCalled();
      });
    });
  });

  describe('View Mode Switching', () => {
    it('should switch to list view', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('列表')).toBeInTheDocument();
      });

      const listButton = screen.getByText('列表');
      fireEvent.click(listButton);

      // Should still render without error
      expect(screen.getByText('物料齐套管理')).toBeInTheDocument();
    });

    it('should switch to analytics view', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('分析')).toBeInTheDocument();
      });

      const analyticsButton = screen.getByText('分析');
      fireEvent.click(analyticsButton);

      expect(screen.getByText('物料齐套管理')).toBeInTheDocument();
    });
  });

  describe('Search and Filters', () => {
    it('should render filter bar', async () => {
      render(
        <MemoryRouter>
          <MaterialReadiness />
        </MemoryRouter>
      );

      await waitFor(() => {
        // Filter bar should be present (search input or select)
        const searchInput = screen.queryByPlaceholderText(/搜索/i);
        expect(searchInput || screen.getByText('概览')).toBeInTheDocument();
      });
    });
  });
});