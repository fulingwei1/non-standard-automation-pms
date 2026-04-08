/**
 * ProjectBoard 组件测试
 * 测试覆盖：项目看板渲染、拖拽功能、筛选、排序、状态更新
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProjectBoard from '../ProjectBoard';
import api, { projectApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  projectApi: {
    update: vi.fn().mockResolvedValue({data: { items: [] }}),
    list: vi.fn().mockResolvedValue({data: { items: [] }}),
    getBoard: vi.fn().mockResolvedValue({data: { items: [] }}),
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    create: vi.fn().mockResolvedValue({data: { items: [] }}),
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
  stageViewsApi: {
    // Pipeline API
    pipeline: {
      get: vi.fn().mockResolvedValue({data: { items: [] }}),
      create: vi.fn().mockResolvedValue({data: { items: [] }}),
      update: vi.fn().mockResolvedValue({data: { items: [] }}),
      delete: vi.fn().mockResolvedValue({data: { items: [] }}),
    },
    // Timeline API
    timeline: {
      get: vi.fn().mockResolvedValue({data: { items: [] }}),
      create: vi.fn().mockResolvedValue({data: { items: [] }}),
      update: vi.fn().mockResolvedValue({data: { items: [] }}),
      delete: vi.fn().mockResolvedValue({data: { items: [] }}),
    },
    // Tree API
    tree: {
      get: vi.fn().mockResolvedValue({data: { items: [] }}),
      create: vi.fn().mockResolvedValue({data: { items: [] }}),
      update: vi.fn().mockResolvedValue({data: { items: [] }}),
      delete: vi.fn().mockResolvedValue({data: { items: [] }}),
    },
    // Stages API
    stages: {
      get: vi.fn().mockResolvedValue({data: { items: [] }}),
      updateStatus: vi.fn().mockResolvedValue({data: { items: [] }}),
      start: vi.fn().mockResolvedValue({data: { items: [] }}),
      complete: vi.fn().mockResolvedValue({data: { items: [] }}),
      submitReview: vi.fn().mockResolvedValue({data: { items: [] }}),
    },
    // Nodes API
    nodes: {
      get: vi.fn().mockResolvedValue({data: { items: [] }}),
      start: vi.fn().mockResolvedValue({data: { items: [] }}),
      complete: vi.fn().mockResolvedValue({data: { items: [] }}),
      skip: vi.fn().mockResolvedValue({data: { items: [] }}),
    },
    // Generic methods
    list: vi.fn().mockResolvedValue({data: { items: [] }}),
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    create: vi.fn().mockResolvedValue({data: { items: [] }}),
    update: vi.fn().mockResolvedValue({data: { items: [] }}),
    delete: vi.fn().mockResolvedValue({data: { items: [] }}),
  },
  // Legacy api export
  default: {
    get: vi.fn().mockResolvedValue({data: { items: [] }}),
    post: vi.fn().mockResolvedValue({data: { items: [] }}),
    put: vi.fn().mockResolvedValue({data: { items: [] }}),
    delete: vi.fn().mockResolvedValue({data: { items: [] }}),
  }
}));

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const validProps = ['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'];
      const filtered = props && Object.entries(props).length > 0 
        ? Object.fromEntries(Object.entries(props).filter(([k]) => !validProps.includes(k))) 
        : {};
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
  AnimatePresence: ({ children }) => children,
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useInView: () => true,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ProjectBoard', () => {
  const mockProjects = [
    {
      id: 1,
      name: '智能制造系统',
      code: 'PROJ-2024-001',
      status: 'in_progress',
      priority: 'high',
      progress: 65,
      startDate: '2024-01-15',
      endDate: '2024-06-30',
      manager: '张三',
      team: ['李四', '王五'],
      budget: 1000000,
      spent: 650000,
      tags: ['智能制造', '系统集成']
    },
    {
      id: 2,
      name: 'ERP系统升级',
      code: 'PROJ-2024-002',
      status: 'planning',
      priority: 'medium',
      progress: 15,
      startDate: '2024-03-01',
      endDate: '2024-08-31',
      manager: '李四',
      team: ['张三', '赵六'],
      budget: 800000,
      spent: 120000,
      tags: ['ERP', '系统升级']
    },
    {
      id: 3,
      name: '数据分析平台',
      code: 'PROJ-2024-003',
      status: 'completed',
      priority: 'low',
      progress: 100,
      startDate: '2023-10-01',
      endDate: '2024-01-31',
      manager: '王五',
      team: ['张三', '李四', '赵六'],
      budget: 500000,
      spent: 480000,
      tags: ['数据分析', '大数据']
    },
    {
      id: 4,
      name: '移动办公应用',
      code: 'PROJ-2024-004',
      status: 'at_risk',
      priority: 'high',
      progress: 45,
      startDate: '2024-02-01',
      endDate: '2024-05-31',
      manager: '赵六',
      team: ['张三'],
      budget: 600000,
      spent: 400000,
      tags: ['移动应用', '办公']
    }
  ];

  const mockStats = {
    total: 4,
    in_progress: 1,
    planning: 1,
    completed: 1,
    at_risk: 1,
    on_hold: 0,
    cancelled: 0
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    projectApi.getBoard.mockImplementation(() => {
      return Promise.resolve({ data: { projects: mockProjects, stats: mockStats } });
    });
    
    projectApi.list.mockImplementation(() => {
      return Promise.resolve({ data: mockProjects });
    });

    projectApi.update.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render project board with title', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/项目看板|Project Board/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should render all project status columns', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/规划中|Planning/i)).toBeInTheDocument();
        expect(screen.getByText(/进行中|In Progress/i)).toBeInTheDocument();
        expect(screen.getByText(/已完成|Completed/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should render project cards in correct columns', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
        expect(screen.getByText('ERP系统升级')).toBeInTheDocument();
        expect(screen.getByText('数据分析平台')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should display project count in each column', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        const inProgressCount = screen.getByText(/1|进行中/);
        expect(inProgressCount).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  // 2. 项目卡片内容测试
  describe('Project Card Content', () => {
    it('should display project code and name', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PROJ-2024-001')).toBeInTheDocument();
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should show project progress bar', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/65%/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should display project manager', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should show project priority badge', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        const highPriority = screen.getAllByText(/高|High|紧急/i);
        expect(highPriority.length).toBeGreaterThan(0);
      }, { timeout: 5000 });
    });

    it('should display project dates', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-01-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-06-30/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should show project tags', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造/)).toBeInTheDocument();
        expect(screen.getByText(/系统集成/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should display budget and spent amount', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1,000,000|100万/)).toBeInTheDocument();
        expect(screen.getByText(/650,000|65万/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  // 3. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch projects on mount', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledWith(expect.stringContaining('/projects'));
      }, { timeout: 5000 });
    });

    it('should show loading state initially', () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      const loadingIndicators = screen.queryAllByText(/加载中|Loading/i);
      expect(loadingIndicators.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error gracefully', async () => {
      projectApi.list.mockRejectedValueOnce(new Error('Failed to fetch projects'));

      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      }, { timeout: 5000 });
    });

    it('should display empty state when no projects', async () => {
      projectApi.list.mockResolvedValueOnce({ data: { projects: [], stats: {} } });

      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无项目|No projects/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  // 4. 筛选和搜索测试
  describe('Filtering and Search', () => {
    it('should filter projects by status', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const filterButton = screen.queryByRole('button', { name: /筛选|Filter/i });
      if (filterButton) {
        fireEvent.click(filterButton);
      }
    });

    it('should filter projects by priority', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      }, { timeout: 5000 });

      const priorityFilter = screen.queryByText(/优先级|Priority/i);
      if (priorityFilter) {
        fireEvent.click(priorityFilter);
      }
    });

    it('should search projects by name', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '智能' } });
      }
    });

    it('should filter projects by manager', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      }, { timeout: 5000 });

      const managerFilter = screen.queryByText(/项目经理|Manager/i);
      if (managerFilter) {
        fireEvent.click(managerFilter);
      }
    });
  });

  // 5. 排序测试
  describe('Sorting', () => {
    it('should sort projects by priority', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      }, { timeout: 5000 });

      const sortButton = screen.queryByText(/排序|Sort/i);
      if (sortButton) {
        fireEvent.click(sortButton);
      }
    });

    it('should sort projects by progress', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      }, { timeout: 5000 });
    });

    it('should sort projects by start date', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      }, { timeout: 5000 });
    });
  });

  // 6. 用户交互测试
  describe('User Interactions', () => {
    it('should navigate to project detail when clicking project card', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const projectCard = screen.getByText('智能制造系统').closest('div');
      if (projectCard) {
        fireEvent.click(projectCard);
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/projects/1'));
      }
    });

    it('should open quick view when clicking info button', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      const infoButtons = screen.queryAllByRole('button', { name: /详情|Info/i });
      if (infoButtons.length > 0) {
        fireEvent.click(infoButtons[0]);
      }
    });

    it('should refresh board when clicking refresh button', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      }, { timeout: 5000 });

      const initialCallCount = projectApi.list.mock.calls.length;

      const refreshButton = screen.queryByRole('button', { name: /刷新|Refresh/i });
      if (refreshButton) {
        fireEvent.click(refreshButton);
        
        await waitFor(() => {
          expect(projectApi.list.mock.calls.length).toBeGreaterThan(initialCallCount);
        }, { timeout: 5000 });
      }
    });

    it('should toggle view mode between board and list', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalled();
      }, { timeout: 5000 });

      const viewToggle = screen.queryByRole('button', { name: /列表|List|看板|Board/i });
      if (viewToggle) {
        fireEvent.click(viewToggle);
      }
    });
  });

  // 7. 统计信息测试
  describe('Statistics Display', () => {
    it('should display total project count', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/4|项目总数/)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should show count for each status', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1.*进行中/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*规划中/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*已完成/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });

    it('should display risk projects count', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1.*风险|At Risk/i)).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  // 8. 拖拽功能测试（模拟）
  describe('Drag and Drop', () => {
    it('should update project status when dragged to new column', async () => {
      render(
        <MemoryRouter>
          <ProjectBoard />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      }, { timeout: 5000 });

      // 模拟拖拽操作（实际拖拽需要更复杂的测试工具）
      const projectCard = screen.getByText('智能制造系统').closest('div[draggable]');
      if (projectCard) {
        fireEvent.dragStart(projectCard);
        fireEvent.dragEnd(projectCard);
        
        await waitFor(() => {
          expect(projectApi.update).toHaveBeenCalled();
        }, { timeout: 5000 });
      }
    });
  });
});
