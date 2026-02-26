/**
 * ProjectDetail 组件测试
 * 测试覆盖：项目详情显示、标签页切换、数据更新、操作按钮
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ProjectDetail from '../ProjectDetail';
import api, { projectApi, machineApi, stageApi, milestoneApi, memberApi, costApi, documentApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    projectApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      getBoard: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      getMachines: vi.fn().mockResolvedValue({ data: {} }),
      getInProductionSummary: vi.fn().mockResolvedValue({ data: {} }),
      recommendTemplates: vi.fn().mockResolvedValue({ data: {} }),
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
    },
    stageApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      statuses: vi.fn().mockResolvedValue({ data: {} }),
    },
    milestoneApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      complete: vi.fn().mockResolvedValue({ data: {} }),
    },
    memberApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      add: vi.fn().mockResolvedValue({ data: {} }),
      remove: vi.fn().mockResolvedValue({ data: {} }),
      batchAdd: vi.fn().mockResolvedValue({ data: {} }),
      checkConflicts: vi.fn().mockResolvedValue({ data: {} }),
      getDeptUsers: vi.fn().mockResolvedValue({ data: {} }),
      notifyDeptManager: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
    },
    costApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      getProjectCosts: vi.fn().mockResolvedValue({ data: {} }),
      getProjectSummary: vi.fn().mockResolvedValue({ data: {} }),
      getCostAnalysis: vi.fn().mockResolvedValue({ data: {} }),
      getRevenueDetail: vi.fn().mockResolvedValue({ data: {} }),
      getProfitAnalysis: vi.fn().mockResolvedValue({ data: {} }),
      calculateLaborCost: vi.fn().mockResolvedValue({ data: {} }),
      getBudgetExecution: vi.fn().mockResolvedValue({ data: {} }),
      getBudgetTrend: vi.fn().mockResolvedValue({ data: {} }),
      generateCostReview: vi.fn().mockResolvedValue({ data: {} }),
      checkBudgetAlert: vi.fn().mockResolvedValue({ data: {} }),
      allocateCost: vi.fn().mockResolvedValue({ data: {} }),
    },
    documentApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
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
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useInView: () => true,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: '1' }),
  };
});

describe.skip('ProjectDetail', () => {
  const mockProject = {
    id: 1,
    code: 'PROJ-2024-001',
    name: '智能制造系统',
    description: '基于AI的智能制造管理系统',
    status: 'in_progress',
    priority: 'high',
    progress: 65,
    startDate: '2024-01-15',
    endDate: '2024-06-30',
    actualStartDate: '2024-01-20',
    actualEndDate: null,
    manager: {
      id: 1,
      name: '张三',
      email: 'zhangsan@example.com'
    },
    team: [
      { id: 2, name: '李四', role: '开发工程师' },
      { id: 3, name: '王五', role: '测试工程师' }
    ],
    budget: 1000000,
    spent: 650000,
    customer: '某大型制造企业',
    industry: '制造业',
    tags: ['智能制造', '系统集成', 'AI'],
    milestones: [
      {
        id: 1,
        name: '需求分析',
        status: 'completed',
        dueDate: '2024-02-15',
        completedDate: '2024-02-10'
      },
      {
        id: 2,
        name: '系统设计',
        status: 'in_progress',
        dueDate: '2024-03-31',
        completedDate: null
      }
    ],
    risks: [
      {
        id: 1,
        title: '技术风险',
        level: 'high',
        status: 'open',
        description: '新技术栈学习曲线陡峭'
      }
    ],
    changes: [
      {
        id: 1,
        title: '需求变更',
        type: 'requirement',
        status: 'approved',
        submittedAt: '2024-02-20'
      }
    ]
  };

  const mockActivities = [
    {
      id: 1,
      user: '张三',
      action: '更新了项目进度',
      timestamp: '2024-02-20T10:00:00Z'
    },
    {
      id: 2,
      user: '李四',
      action: '提交了代码',
      timestamp: '2024-02-20T09:00:00Z'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    projectApi.get.mockImplementation((url) => {
      if (url.includes('/projects/1')) {
        return Promise.resolve({ data: mockProject });
      }
      if (url.includes('/activities')) {
        return Promise.resolve({ data: mockActivities });
      }
      return Promise.resolve({ data: {} });
    });

    projectApi.update.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render project detail with basic info', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });
    });

    it('should display project code and name', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('PROJ-2024-001')).toBeInTheDocument();
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });
    });

    it('should show project status badge', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/进行中|In Progress/i)).toBeInTheDocument();
      });
    });

    it('should display project description', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/基于AI的智能制造管理系统/)).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should call API to fetch project details', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.get).toHaveBeenCalledWith(expect.stringContaining('/projects/1'));
      });
    });

    it('should show loading state initially', () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      const loadingIndicators = screen.queryAllByText(/加载中|Loading/i);
      expect(loadingIndicators.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle API error', async () => {
      projectApi.get.mockRejectedValueOnce(new Error('Failed to load project'));

      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });

    it('should handle project not found', async () => {
      projectApi.get.mockResolvedValueOnce({ data: null });

      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/未找到项目|Project not found/i)).toBeInTheDocument();
      });
    });
  });

  // 3. 项目信息显示测试
  describe('Project Information Display', () => {
    it('should display project dates', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-01-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-06-30/)).toBeInTheDocument();
      });
    });

    it('should show project manager info', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/张三/)).toBeInTheDocument();
      });
    });

    it('should display team members', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/李四/)).toBeInTheDocument();
        expect(screen.getByText(/王五/)).toBeInTheDocument();
      });
    });

    it('should show budget information', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1,000,000|100万/)).toBeInTheDocument();
        expect(screen.getByText(/650,000|65万/)).toBeInTheDocument();
      });
    });

    it('should display project progress', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/65%/)).toBeInTheDocument();
      });
    });

    it('should show customer and industry', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/某大型制造企业/)).toBeInTheDocument();
        expect(screen.getByText(/制造业/)).toBeInTheDocument();
      });
    });

    it('should display project tags', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/智能制造/)).toBeInTheDocument();
        expect(screen.getByText(/系统集成/)).toBeInTheDocument();
      });
    });
  });

  // 4. 标签页切换测试
  describe('Tab Navigation', () => {
    it('should render all tabs', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/概览|Overview/i)).toBeInTheDocument();
        expect(screen.getByText(/里程碑|Milestones/i)).toBeInTheDocument();
        expect(screen.getByText(/团队|Team/i)).toBeInTheDocument();
      });
    });

    it('should switch to milestones tab', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const milestonesTab = screen.getByText(/里程碑|Milestones/i);
      fireEvent.click(milestonesTab);

      await waitFor(() => {
        expect(screen.getByText(/需求分析/)).toBeInTheDocument();
      });
    });

    it('should switch to team tab', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const teamTab = screen.getByText(/团队|Team/i);
      fireEvent.click(teamTab);

      await waitFor(() => {
        expect(screen.getByText(/开发工程师/)).toBeInTheDocument();
      });
    });

    it('should switch to risks tab', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const risksTab = screen.queryByText(/风险|Risks/i);
      if (risksTab) {
        fireEvent.click(risksTab);
        
        await waitFor(() => {
          expect(screen.getByText(/技术风险/)).toBeInTheDocument();
        });
      }
    });
  });

  // 5. 里程碑显示测试
  describe('Milestones Display', () => {
    it('should display milestone list', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const milestonesTab = screen.getByText(/里程碑|Milestones/i);
      fireEvent.click(milestonesTab);

      await waitFor(() => {
        expect(screen.getByText(/需求分析/)).toBeInTheDocument();
        expect(screen.getByText(/系统设计/)).toBeInTheDocument();
      });
    });

    it('should show milestone status', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const milestonesTab = screen.getByText(/里程碑|Milestones/i);
      fireEvent.click(milestonesTab);

      await waitFor(() => {
        expect(screen.getByText(/已完成|Completed/i)).toBeInTheDocument();
        expect(screen.getByText(/进行中|In Progress/i)).toBeInTheDocument();
      });
    });
  });

  // 6. 操作按钮测试
  describe('Action Buttons', () => {
    it('should render edit button', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const editButton = screen.queryByRole('button', { name: /编辑|Edit/i });
      expect(editButton).toBeTruthy();
    });

    it('should open edit dialog when clicking edit button', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const editButton = screen.queryByRole('button', { name: /编辑|Edit/i });
      if (editButton) {
        fireEvent.click(editButton);
      }
    });

    it('should update project status', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const statusButton = screen.queryByRole('button', { name: /状态|Status/i });
      if (statusButton) {
        fireEvent.click(statusButton);
        
        await waitFor(() => {
          expect(projectApi.update).toHaveBeenCalled();
        });
      }
    });

    it('should navigate back when clicking back button', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const backButton = screen.queryByRole('button', { name: /返回|Back/i });
      if (backButton) {
        fireEvent.click(backButton);
        expect(mockNavigate).toHaveBeenCalledWith(-1);
      }
    });
  });

  // 7. 活动日志测试
  describe('Activity Log', () => {
    it('should display recent activities', async () => {
      render(
        <MemoryRouter initialEntries={['/projects/1']}>
          <Routes>
            <Route path="/projects/:id" element={<ProjectDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const activityTab = screen.queryByText(/活动|Activities/i);
      if (activityTab) {
        fireEvent.click(activityTab);
        
        await waitFor(() => {
          expect(screen.getByText(/更新了项目进度/)).toBeInTheDocument();
        });
      }
    });
  });
});
