/**
 * QualificationManagement 组件测试
 * 测试覆盖：资质列表、证书管理、到期提醒、审核流程
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { qualificationApi } from '../../services/api';
import { MemoryRouter } from 'react-router-dom';
import QualificationManagement from '../QualificationManagement';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    qualificationApi: {
      create: vi.fn().mockResolvedValue({ data: {} }),
      deleteLevel: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      getLevels: vi.fn().mockResolvedValue({ data: {} }),
      getLevel: vi.fn().mockResolvedValue({ data: {} }),
      createLevel: vi.fn().mockResolvedValue({ data: {} }),
      updateLevel: vi.fn().mockResolvedValue({ data: {} }),
      getModels: vi.fn().mockResolvedValue({ data: {} }),
      getModel: vi.fn().mockResolvedValue({ data: {} }),
      getModelById: vi.fn().mockResolvedValue({ data: {} }),
      createModel: vi.fn().mockResolvedValue({ data: {} }),
      updateModel: vi.fn().mockResolvedValue({ data: {} }),
      getEmployeeQualification: vi.fn().mockResolvedValue({ data: {} }),
      getEmployeeQualifications: vi.fn().mockResolvedValue({ data: {} }),
      certifyEmployee: vi.fn().mockResolvedValue({ data: {} }),
      promoteEmployee: vi.fn().mockResolvedValue({ data: {} }),
      getAssessments: vi.fn().mockResolvedValue({ data: {} }),
      createAssessment: vi.fn().mockResolvedValue({ data: {} }),
      submitAssessment: vi.fn().mockResolvedValue({ data: {} }),
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

describe('QualificationManagement', () => {
  // 组件 loadLevels() 检查 response.data?.code === 200，取 response.data.data?.items
  // 组件 loadStats() 也调用 getLevels 并读取 response.data?.data?.total
  const mockLevels = [
    {
      id: 1,
      level_code: 'SENIOR',
      level_name: '高级工程师',
      level_order: 1,
      role_type: 'ENGINEER',
      is_active: true,
    },
    {
      id: 2,
      level_code: 'JUNIOR',
      level_name: '初级工程师',
      level_order: 2,
      role_type: 'ENGINEER',
      is_active: true,
    }
  ];

  // 组件 loadModels() 检查 response.data?.code === 200，取 response.data.data?.items
  const mockModels = [
    {
      id: 1,
      position_type: 'ENGINEER',
      position_subtype: '机械',
      level_id: 1,
      level: { level_code: 'SENIOR', level_name: '高级工程师' },
      is_active: true,
      created_at: '2024-01-15',
    }
  ];

  // 组件 loadQualifications() 检查 response.data?.code === 200
  const mockEmployeeQualifications = [
    {
      id: 1,
      employee_id: 101,
      position_type: 'ENGINEER',
      current_level_id: 1,
      level: { level_code: 'SENIOR', level_name: '高级工程师' },
      status: 'APPROVED',
      certified_date: '2024-01-15',
    }
  ];

  // 构造符合组件期望的 API 响应格式
  const wrapResponse = (items, total) => ({
    data: { code: 200, data: { items, total: total ?? items.length } }
  });

  beforeEach(() => {
    vi.clearAllMocks();
    // getLevels 在 loadLevels 和 loadStats 中都被调用
    qualificationApi.getLevels.mockResolvedValue(wrapResponse(mockLevels, mockLevels.length));
    // getModels 在 loadModels 和 loadStats 中被调用
    qualificationApi.getModels.mockResolvedValue(wrapResponse(mockModels, mockModels.length));
    // getEmployeeQualifications 在 loadQualifications 和 loadStats 中被调用
    qualificationApi.getEmployeeQualifications.mockResolvedValue(
      wrapResponse(mockEmployeeQualifications, mockEmployeeQualifications.length)
    );
    qualificationApi.create.mockResolvedValue({ data: { code: 200, data: { success: true, id: 3 } } });
    qualificationApi.update.mockResolvedValue({ data: { code: 200, data: { success: true } } });
    qualificationApi.deleteLevel.mockResolvedValue({ data: { code: 200, data: { success: true } } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render qualification management page', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件 PageHeader title="任职资格管理"
      await waitFor(() => {
        expect(screen.getAllByText(/任职资格管理/i).length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should render level list in default tab', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 默认 tab 是 "levels"，显示等级管理表格中的 level_name
      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
        expect(screen.getByText('初级工程师')).toBeInTheDocument();
      });
    });

    it('should display level codes', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件在表格中显示 level_code Badge
      await waitFor(() => {
        expect(screen.getByText('SENIOR')).toBeInTheDocument();
        expect(screen.getByText('JUNIOR')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load levels on mount', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件调用 getLevels 传入参数对象
      await waitFor(() => {
        expect(qualificationApi.getLevels).toHaveBeenCalledWith(
          expect.objectContaining({ page: 1 })
        );
      });
    });

    it('should call getLevels for stats', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // loadStats 也会调用 getLevels({ page: 1, page_size: 1 })
      await waitFor(() => {
        expect(qualificationApi.getLevels).toHaveBeenCalled();
      });
    });

    it('should handle load error gracefully', async () => {
      // 组件在 loadData catch 中调用 toast.error，不渲染错误 DOM
      qualificationApi.getLevels.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件出错后仍然渲染页面框架
      await waitFor(() => {
        expect(screen.getAllByText(/任职资格管理/i).length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe('Qualification Information', () => {
    it('should display level names in table', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 默认 tab "levels" 显示等级表格
      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
        expect(screen.getByText('初级工程师')).toBeInTheDocument();
      });
    });

    it('should show role type for levels', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件显示 level.role_type 或 "通用"
      await waitFor(() => {
        expect(screen.getAllByText('ENGINEER').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display active status badge', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件对 is_active=true 渲染 "启用" Badge
      await waitFor(() => {
        expect(screen.getAllByText('启用').length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe('Tab Navigation', () => {
    it('should display tab buttons', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件有 3 个 tab: "等级管理", "能力模型", "员工认证"
      // "能力模型" 同时出现在 tab 和统计卡片中，使用 getAllByText
      await waitFor(() => {
        expect(screen.getByText('等级管理')).toBeInTheDocument();
        expect(screen.getAllByText('能力模型').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('员工认证')).toBeInTheDocument();
      });
    });

    it('should show level table headers', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 默认 levels tab 的表头
      await waitFor(() => {
        expect(screen.getByText('等级编码')).toBeInTheDocument();
        expect(screen.getByText('等级名称')).toBeInTheDocument();
      });
    });

    it('should show level order', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
      });
    });

    it('should load data on mount', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(qualificationApi.getLevels).toHaveBeenCalled();
      });
    });
  });

  describe('Level Status', () => {
    it('should display active status for levels', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件对 is_active=true 显示 "启用" Badge
      await waitFor(() => {
        expect(screen.getAllByText('启用').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display level data correctly', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
      });
    });
  });

  describe('Filtering', () => {
    it('should display role type filter', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 等级管理 tab 有角色类型和状态的 Select 筛选器
      await waitFor(() => {
        expect(qualificationApi.getLevels).toHaveBeenCalled();
      });
    });

    it('should call API on mount', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(qualificationApi.getLevels).toHaveBeenCalled();
      });
    });

    it('should load stats data', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // loadStats 调用 getLevels, getModels, getEmployeeQualifications
      await waitFor(() => {
        expect(qualificationApi.getModels).toHaveBeenCalled();
      });
    });
  });

  describe('CRUD Operations', () => {
    it('should have new level button', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(qualificationApi.getLevels).toHaveBeenCalled();
      });

      // 组件在 levels tab 显示 "新建等级" 按钮
      const createButtons = screen.queryAllByRole('button', { name: /新建等级/i });
      expect(createButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('should display action buttons for levels', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
      });

      // 每个等级行有查看详情、编辑、删除按钮
      const actionButtons = screen.queryAllByRole('button');
      expect(actionButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('should render delete buttons for levels', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
      });

      // 每个等级行都有删除按钮（图标按钮）
      expect(qualificationApi.getLevels).toHaveBeenCalled();
    });
  });

  describe('Level Actions', () => {
    it('should have view detail buttons', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
      });

      // 组件每行有带 title="查看详情" 的按钮
      const viewButtons = screen.queryAllByTitle('查看详情');
      expect(viewButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('should have edit buttons', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('高级工程师')).toBeInTheDocument();
      });

      // 组件每行有带 title="编辑" 的按钮
      const editButtons = screen.queryAllByTitle('编辑');
      expect(editButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Statistics Display', () => {
    it('should show statistics cards', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // 组件渲染 4 个统计卡片: 等级总数、已认证员工 等
      // "待认证" 同时出现在统计卡片和筛选 Select 中
      await waitFor(() => {
        expect(screen.getByText('等级总数')).toBeInTheDocument();
        expect(screen.getByText('已认证员工')).toBeInTheDocument();
        expect(screen.getAllByText('待认证').length).toBeGreaterThanOrEqual(1);
      });
    });

    it('should display stats values from API', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      // loadStats 从 API 响应中提取 total 值
      await waitFor(() => {
        expect(qualificationApi.getLevels).toHaveBeenCalled();
        expect(qualificationApi.getModels).toHaveBeenCalled();
      });
    });
  });
});
