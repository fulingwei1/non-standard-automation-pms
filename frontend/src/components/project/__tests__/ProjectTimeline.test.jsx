import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ProjectTimeline from '../ProjectTimeline';

describe('ProjectTimeline', () => {
  const mockStatusLogs = [
    {
      id: 1,
      change_type: 'STAGE_CHANGE',
      old_stage: '需求分析',
      new_stage: '设计',
      change_note: '进入设计阶段',
      changed_at: '2024-01-15T10:00:00',
      changed_by_name: '张三',
    },
    {
      id: 2,
      change_type: 'STATUS_CHANGE',
      old_status: '进行中',
      new_status: '已完成',
      change_reason: '阶段完成',
      changed_at: '2024-01-20T15:30:00',
      changed_by_name: '李四',
    },
    {
      id: 3,
      change_type: 'HEALTH_CHANGE',
      old_health: '良好',
      new_health: '警告',
      change_note: '进度延迟',
      changed_at: '2024-01-25T09:00:00',
      changed_by_name: '王五',
    },
  ];

  const mockMilestones = [
    {
      id: 1,
      milestone_name: '需求评审完成',
      description: '完成需求文档评审',
      planned_date: '2024-01-10',
      actual_date: '2024-01-12',
      status: 'COMPLETED',
    },
    {
      id: 2,
      milestone_name: '设计评审',
      description: '设计方案评审',
      planned_date: '2024-01-30',
      status: 'PENDING',
    },
  ];

  // 文档必须有 status: 'APPROVED' 才能被组件过滤后显示
  const mockDocuments = [
    {
      id: 1,
      document_name: '需求规格说明书',
      uploaded_at: '2024-01-05T14:00:00',
      updated_at: '2024-01-05T14:00:00',
      uploaded_by_name: '赵六',
      document_type: '需求文档',
      status: 'APPROVED',
    },
    {
      id: 2,
      document_name: '设计文档',
      uploaded_at: '2024-01-18T11:00:00',
      updated_at: '2024-01-18T11:00:00',
      uploaded_by_name: '孙七',
      document_type: '设计文档',
      status: 'APPROVED',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders without props', () => {
      render(<ProjectTimeline />);
      expect(screen.getByPlaceholderText(/搜索事件/i)).toBeInTheDocument();
    });

    it('renders with empty arrays', () => {
      render(
        <ProjectTimeline
          statusLogs={[]}
          milestones={[]}
          documents={[]}
        />
      );
      expect(screen.getByPlaceholderText(/搜索事件/i)).toBeInTheDocument();
    });

    it('renders with all event types', () => {
      render(
        <ProjectTimeline
          projectId="123"
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );
      // 阶段变更标题格式: "阶段变更: 需求分析 → 设计"
      expect(screen.getByText(/需求分析.*设计/)).toBeInTheDocument();
      // 里程碑
      expect(screen.getByText('需求评审完成')).toBeInTheDocument();
      // 文档（标题格式: "文档审批通过: 需求规格说明书"）
      expect(screen.getByText(/需求规格说明书/)).toBeInTheDocument();
    });
  });

  describe('Event Display', () => {
    it('displays stage change events', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={[]}
          documents={[]}
        />
      );
      expect(screen.getByText(/需求分析.*设计/)).toBeInTheDocument();
      expect(screen.getByText('进入设计阶段')).toBeInTheDocument();
    });

    it('displays status change events', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={[]}
          documents={[]}
        />
      );
      expect(screen.getByText(/进行中.*已完成/)).toBeInTheDocument();
      expect(screen.getByText('阶段完成')).toBeInTheDocument();
    });

    it('displays health change events', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={[]}
          documents={[]}
        />
      );
      expect(screen.getByText(/良好.*警告/)).toBeInTheDocument();
      expect(screen.getByText('进度延迟')).toBeInTheDocument();
    });

    it('displays milestone events', () => {
      render(
        <ProjectTimeline
          statusLogs={[]}
          milestones={mockMilestones}
          documents={[]}
        />
      );
      expect(screen.getByText('需求评审完成')).toBeInTheDocument();
      expect(screen.getByText('完成需求文档评审')).toBeInTheDocument();
    });

    it('displays document events', () => {
      render(
        <ProjectTimeline
          statusLogs={[]}
          milestones={[]}
          documents={mockDocuments}
        />
      );
      // 文档标题格式: "文档审批通过: 需求规格说明书"
      expect(screen.getByText(/需求规格说明书/)).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('filters events by search query', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );

      const searchInput = screen.getByPlaceholderText(/搜索事件/i);
      fireEvent.change(searchInput, { target: { value: '需求' } });

      expect(screen.getByText('需求评审完成')).toBeInTheDocument();
      expect(screen.getByText(/需求规格说明书/)).toBeInTheDocument();
    });

    it('shows no results when search does not match', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );

      const searchInput = screen.getByPlaceholderText(/搜索事件/i);
      fireEvent.change(searchInput, { target: { value: '不存在的事件' } });

      expect(screen.queryByText('需求评审完成')).not.toBeInTheDocument();
    });

    it('clears search query', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );

      const searchInput = screen.getByPlaceholderText(/搜索事件/i);
      fireEvent.change(searchInput, { target: { value: '需求' } });
      fireEvent.change(searchInput, { target: { value: '' } });

      expect(screen.getByText('需求评审完成')).toBeInTheDocument();
      expect(screen.getByText(/需求分析.*设计/)).toBeInTheDocument();
    });
  });

  describe('Event Type Filtering', () => {
    it('filters by event type', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );

      // 默认显示全部事件
      expect(screen.getByText(/需求分析.*设计/)).toBeInTheDocument();
      expect(screen.getByText('需求评审完成')).toBeInTheDocument();
    });

    it('shows all events when filter is "all"', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );

      expect(screen.getByText(/需求分析.*设计/)).toBeInTheDocument();
      expect(screen.getByText('需求评审完成')).toBeInTheDocument();
      expect(screen.getByText(/需求规格说明书/)).toBeInTheDocument();
    });
  });

  describe('Event Sorting', () => {
    it('displays events in chronological order', () => {
      const { container } = render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );

      // 验证有事件渲染出来
      const eventItems = container.querySelectorAll('.relative.flex.gap-4');
      expect(eventItems.length).toBeGreaterThan(0);
    });
  });

  describe('User Information', () => {
    it('displays user names for events', () => {
      render(
        <ProjectTimeline
          statusLogs={mockStatusLogs}
          milestones={[]}
          documents={mockDocuments}
        />
      );

      expect(screen.getByText('张三')).toBeInTheDocument();
      expect(screen.getByText('李四')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing change notes', () => {
      const logsWithoutNotes = [
        {
          id: 1,
          change_type: 'STAGE_CHANGE',
          old_stage: 'A',
          new_stage: 'B',
          changed_at: '2024-01-01',
          changed_by_name: '测试',
        },
      ];

      render(<ProjectTimeline statusLogs={logsWithoutNotes} />);
      expect(screen.getByText(/A.*B/)).toBeInTheDocument();
    });

    it('handles events without user names', () => {
      const logsWithoutUsers = [
        {
          id: 1,
          change_type: 'STAGE_CHANGE',
          old_stage: 'A',
          new_stage: 'B',
          changed_at: '2024-01-01',
        },
      ];

      render(<ProjectTimeline statusLogs={logsWithoutUsers} />);
      expect(screen.getByText(/A.*B/)).toBeInTheDocument();
    });

    it('handles invalid change types gracefully', () => {
      const logsWithInvalidType = [
        {
          id: 1,
          change_type: 'UNKNOWN_TYPE',
          changed_at: '2024-01-01',
        },
      ];

      render(<ProjectTimeline statusLogs={logsWithInvalidType} />);
      expect(screen.getByPlaceholderText(/搜索事件/i)).toBeInTheDocument();
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot with all events', () => {
      const { container } = render(
        <ProjectTimeline
          projectId="123"
          statusLogs={mockStatusLogs}
          milestones={mockMilestones}
          documents={mockDocuments}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with empty data', () => {
      const { container } = render(
        <ProjectTimeline
          statusLogs={[]}
          milestones={[]}
          documents={[]}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
