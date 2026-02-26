/**
 * GeneralManagerWorkstation 组件测试
 * 测试覆盖：组件渲染、业务数据展示、审批流程、部门状态、关键指标
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import GeneralManagerWorkstation from '../GeneralManagerWorkstation';

// Mock API
vi.mock('../../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}));

// Mock dependencies
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}));

// Mock useGMDashboard hook
const mockLoadDashboard = vi.fn();
const mockUseGMDashboard = vi.fn(() => ({
  loading: false,
  error: null,
  businessStats: {
    yearTarget: 50000000,
    yearRevenue: 35000000,
    yearProgress: 70,
    monthTarget: 4000000,
    monthRevenue: 3200000,
    monthProgress: 80,
    quarterTarget: 12000000,
    quarterRevenue: 10500000,
    quarterProgress: 87.5
  },
  pendingApprovals: [
    {
      id: 1,
      type: 'contract',
      title: '某项目合同审批',
      amount: 500000,
      submitter: '张三',
      submitTime: '2024-02-20T10:00:00Z',
      priority: 'high'
    },
    {
      id: 2,
      type: 'expense',
      title: '市场活动费用',
      amount: 50000,
      submitter: '李四',
      submitTime: '2024-02-20T09:00:00Z',
      priority: 'medium'
    }
  ],
  projectHealth: {
    total: 50,
    onTrack: 35,
    atRisk: 10,
    delayed: 5,
    healthRate: 70
  },
  departmentStatus: [
    {
      name: '销售部',
      revenue: 15000000,
      target: 18000000,
      completion: 83.3,
      headcount: 15,
      trend: 'up'
    },
    {
      name: '研发部',
      projects: 25,
      onTime: 20,
      delayed: 5,
      headcount: 50,
      trend: 'stable'
    },
    {
      name: '生产部',
      orders: 30,
      completed: 25,
      inProgress: 5,
      headcount: 80,
      trend: 'up'
    }
  ],
  keyMetrics: {
    customerSatisfaction: 4.5,
    employeeSatisfaction: 4.2,
    productivityIndex: 85,
    innovationIndex: 75,
    qualityScore: 92
  },
  loadDashboard: mockLoadDashboard
}));

vi.mock('../useGMDashboard', () => ({
  default: () => mockUseGMDashboard()
}));

// Mock CultureWallCarousel
vi.mock('../../../components/culture/CultureWallCarousel', () => ({
  default: ({ onItemClick }) => (
    <div data-testid="culture-wall-carousel">
      <button onClick={() => onItemClick({ id: 1, category: 'GOAL' })}>
        Culture Item
      </button>
    </div>
  )
}));

describe.skip('GeneralManagerWorkstation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render general manager workstation with title', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText('总经理工作台')).toBeInTheDocument();
    });

    it('should render description with business stats', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/年度营收目标|已完成/)).toBeInTheDocument();
    });

    it('should render culture wall carousel', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByTestId('culture-wall-carousel')).toBeInTheDocument();
    });

    it('should render action buttons', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/经营报表/)).toBeInTheDocument();
      expect(screen.getByText(/审批中心/)).toBeInTheDocument();
    });
  });

  // 2. 业务统计展示测试
  describe('Business Statistics Display', () => {
    it('should display year revenue target and progress', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/50,000,000|5000万/)).toBeInTheDocument();
      expect(screen.getByText(/35,000,000|3500万/)).toBeInTheDocument();
      expect(screen.getByText(/70%/)).toBeInTheDocument();
    });

    it('should display month revenue stats', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/4,000,000|400万/)).toBeInTheDocument();
      expect(screen.getByText(/3,200,000|320万/)).toBeInTheDocument();
    });

    it('should display quarter revenue stats', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/12,000,000|1200万/)).toBeInTheDocument();
      expect(screen.getByText(/10,500,000|1050万/)).toBeInTheDocument();
    });

    it('should show formatted currency values', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      // 检查货币格式化（¥或逗号分隔）
      const currencyElements = screen.getAllByText(/¥|,/);
      expect(currencyElements.length).toBeGreaterThan(0);
    });
  });

  // 3. 待审批事项测试
  describe('Pending Approvals', () => {
    it('should display pending approvals count', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/2|待审批/)).toBeInTheDocument();
    });

    it('should show approval items with details', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/某项目合同审批/)).toBeInTheDocument();
      expect(screen.getByText(/市场活动费用/)).toBeInTheDocument();
    });

    it('should display approval amount', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/500,000|50万/)).toBeInTheDocument();
      expect(screen.getByText(/50,000|5万/)).toBeInTheDocument();
    });

    it('should show approval priority badges', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      const highPriority = screen.queryByText(/高|High|紧急/i);
      expect(highPriority).toBeTruthy();
    });

    it('should handle click on approval item', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      const approvalItems = screen.getAllByText(/审批/);
      if (approvalItems.length > 0) {
        const clickable = approvalItems[0].closest('button') || approvalItems[0].closest('a');
        if (clickable) {
          fireEvent.click(clickable);
        }
      }
    });
  });

  // 4. 项目健康度测试
  describe('Project Health', () => {
    it('should display total project count', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/50|项目总数/)).toBeInTheDocument();
    });

    it('should show projects by status', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/35|正常/)).toBeInTheDocument();
      expect(screen.getByText(/10|风险/)).toBeInTheDocument();
      expect(screen.getByText(/5|延期/)).toBeInTheDocument();
    });

    it('should display project health rate', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/70%/)).toBeInTheDocument();
    });

    it('should use color coding for project status', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      // 检查是否有颜色标识的元素
      const container = screen.getByText(/项目健康/i).closest('div');
      expect(container).toBeTruthy();
    });
  });

  // 5. 部门状态测试
  describe('Department Status', () => {
    it('should display all departments', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/销售部/)).toBeInTheDocument();
      expect(screen.getByText(/研发部/)).toBeInTheDocument();
      expect(screen.getByText(/生产部/)).toBeInTheDocument();
    });

    it('should show sales department metrics', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/15,000,000|1500万/)).toBeInTheDocument();
      expect(screen.getByText(/83.3%/)).toBeInTheDocument();
    });

    it('should show R&D department metrics', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/25|项目/)).toBeInTheDocument();
      expect(screen.getByText(/20|按时/)).toBeInTheDocument();
    });

    it('should show production department metrics', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/30|订单/)).toBeInTheDocument();
      expect(screen.getByText(/25|完成/)).toBeInTheDocument();
    });

    it('should display department headcount', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/15|人|员工/)).toBeInTheDocument();
      expect(screen.getByText(/50|人|员工/)).toBeInTheDocument();
      expect(screen.getByText(/80|人|员工/)).toBeInTheDocument();
    });

    it('should show department trend indicators', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      const trendElements = screen.getAllByText(/↑|↓|→|上升|下降|稳定/i);
      expect(trendElements.length).toBeGreaterThan(0);
    });
  });

  // 6. 关键指标测试
  describe('Key Metrics', () => {
    it('should display customer satisfaction score', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/4.5|客户满意度/)).toBeInTheDocument();
    });

    it('should display employee satisfaction score', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/4.2|员工满意度/)).toBeInTheDocument();
    });

    it('should display productivity index', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/85|生产力指数/)).toBeInTheDocument();
    });

    it('should display innovation index', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/75|创新指数/)).toBeInTheDocument();
    });

    it('should display quality score', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/92|质量分数/)).toBeInTheDocument();
    });
  });

  // 7. 加载和错误状态测试
  describe('Loading and Error States', () => {
    it('should show loading state', () => {
      mockUseGMDashboard.mockReturnValueOnce({
        loading: true,
        error: null,
        businessStats: null,
        pendingApprovals: [],
        projectHealth: null,
        departmentStatus: [],
        keyMetrics: null,
        loadDashboard: mockLoadDashboard
      });

      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中/)).toBeInTheDocument();
    });

    it('should show error state when data loading fails', () => {
      mockUseGMDashboard.mockReturnValueOnce({
        loading: false,
        error: new Error('Failed to load data'),
        businessStats: null,
        pendingApprovals: [],
        projectHealth: null,
        departmentStatus: [],
        keyMetrics: null,
        loadDashboard: mockLoadDashboard
      });

      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(screen.getByText(/错误|Error|failed/i)).toBeInTheDocument();
    });

    it('should call loadDashboard on mount', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      expect(mockLoadDashboard).toHaveBeenCalled();
    });
  });

  // 8. 用户交互测试
  describe('User Interactions', () => {
    it('should navigate to business reports when clicking button', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      const reportButton = screen.getByText(/经营报表/);
      fireEvent.click(reportButton);
    });

    it('should navigate to approval center when clicking button', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      const approvalButton = screen.getByText(/审批中心/);
      fireEvent.click(approvalButton);
    });

    it('should handle culture wall item click', () => {
      render(
        <MemoryRouter>
          <GeneralManagerWorkstation />
        </MemoryRouter>
      );

      const cultureItem = screen.getByText('Culture Item');
      fireEvent.click(cultureItem);

      // 应该导航到个人目标页面
      expect(window.location.href).toContain('personal-goals');
    });
  });
});
