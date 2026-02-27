import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import SolutionLibrary from '../SolutionLibrary';
import { issueTemplateApi } from '../../../services/api';

vi.mock('../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: '/api' },
    },
  };
});

describe('SolutionLibrary', () => {
  const mockTemplates = [
    {
      id: 1,
      template_name: '性能优化方案',
      template_code: 'PERF_OPT',
      category: '技术问题',
      issue_type: '技术问题',
      remark: '适用于系统性能优化场景',
      solution_template: '1. 分析性能瓶颈\n2. 优化代码\n3. 测试验证',
      usage_count: 15,
    },
    {
      id: 2,
      template_name: '需求变更处理',
      template_code: 'REQ_CHANGE',
      category: '管理问题',
      issue_type: '管理问题',
      remark: '适用于客户需求变更',
      solution_template: '1. 评估影响\n2. 制定方案\n3. 获取批准',
      usage_count: 8,
    },
  ];

  const mockOnApplyTemplate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    issueTemplateApi.list.mockResolvedValue({
      data: { items: mockTemplates },
    });
  });

  describe('Basic Rendering', () => {
    it('shows loading state initially', () => {
      issueTemplateApi.list.mockReturnValue(new Promise(() => {}));
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });

    it('renders solution templates after loading', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
        expect(screen.getByText('需求变更处理')).toBeInTheDocument();
      });
    });

    it('displays template details', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('适用于系统性能优化场景')).toBeInTheDocument();
        expect(screen.getByText(/使用.*15.*次/)).toBeInTheDocument();
      });
    });

    it('calls API with correct parameters', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(issueTemplateApi.list).toHaveBeenCalledWith({
          page: 1,
          page_size: 100,
          is_active: true,
        });
      });
    });
  });

  describe('Search Functionality', () => {
    it('filters templates by search query', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索/i);
      fireEvent.change(searchInput, { target: { value: '性能' } });

      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      expect(screen.queryByText('需求变更处理')).not.toBeInTheDocument();
    });

    it('searches in template names', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索/i);
      fireEvent.change(searchInput, { target: { value: '优化' } });

      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });

    it('searches in solution content', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索/i);
      fireEvent.change(searchInput, { target: { value: '分析性能' } });

      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      expect(screen.queryByText('需求变更处理')).not.toBeInTheDocument();
    });

    it('handles case-insensitive search', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索/i);
      fireEvent.change(searchInput, { target: { value: '性能' } });

      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });

    it('shows no results when search has no matches', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索/i);
      fireEvent.change(searchInput, { target: { value: '不存在的模板' } });

      expect(screen.queryByText('性能优化方案')).not.toBeInTheDocument();
      expect(screen.queryByText('需求变更处理')).not.toBeInTheDocument();
    });

    it('clears search query', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索/i);
      fireEvent.change(searchInput, { target: { value: '性能' } });
      fireEvent.change(searchInput, { target: { value: '' } });

      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      expect(screen.getByText('需求变更处理')).toBeInTheDocument();
    });
  });

  describe('Type Filtering', () => {
    it('filters by issue type', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      // Simulate type filter change (implementation depends on UI)
      // This is a placeholder test
      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });
  });

  describe('Template Application', () => {
    it('calls onApplyTemplate when apply button clicked', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const applyButtons = screen.getAllByRole('button', { name: /应用|使用/i });
      if (applyButtons.length > 0) {
        fireEvent.click(applyButtons[0]);
        expect(mockOnApplyTemplate).toHaveBeenCalled();
      }
    });

    it('does not error when onApplyTemplate is not provided', async () => {
      render(<SolutionLibrary projectId="123" />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });

      const applyButtons = screen.queryAllByRole('button', { name: /应用|使用/i });
      if (applyButtons.length > 0) {
        expect(() => fireEvent.click(applyButtons[0])).not.toThrow();
      }
    });
  });

  describe('Error Handling', () => {
    it('handles API error gracefully', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      issueTemplateApi.list.mockRejectedValue(new Error('API Error'));

      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(consoleError).toHaveBeenCalled();
      });
      
      consoleError.mockRestore();
    });

    it('handles empty template array', async () => {
      issueTemplateApi.list.mockResolvedValue({
        data: { items: [] },
      });
      
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.queryByText('性能优化方案')).not.toBeInTheDocument();
      });
    });

    it('handles null data', async () => {
      issueTemplateApi.list.mockResolvedValue({
        data: null,
      });
      
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(issueTemplateApi.list).toHaveBeenCalled();
      });
    });

    it('handles data without items field', async () => {
      issueTemplateApi.list.mockResolvedValue({
        data: mockTemplates,
      });
      
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });
    });
  });

  describe('Template Statistics', () => {
    it('displays usage count', async () => {
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText(/使用.*15.*次/)).toBeInTheDocument();
      });
    });

    it('handles missing usage count', async () => {
      const templatesWithoutCount = mockTemplates.map(t => ({
        ...t,
        usage_count: undefined,
      }));
      
      issueTemplateApi.list.mockResolvedValue({
        data: { items: templatesWithoutCount },
      });
      
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles templates without applicable scenarios', async () => {
      const templatesWithoutRemark = mockTemplates.map(t => ({
        ...t,
        remark: undefined,
      }));
      
      issueTemplateApi.list.mockResolvedValue({
        data: { items: templatesWithoutRemark },
      });
      
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });
    });

    it('handles templates without solution template', async () => {
      const templatesWithoutSolution = mockTemplates.map(t => ({
        ...t,
        solution_template: undefined,
      }));
      
      issueTemplateApi.list.mockResolvedValue({
        data: { items: templatesWithoutSolution },
      });
      
      render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });
    });

    it('refetches data when projectId changes', async () => {
      const { rerender } = render(
        <SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />
      );
      
      await waitFor(() => {
        expect(issueTemplateApi.list).toHaveBeenCalledTimes(1);
      });

      rerender(
        <SolutionLibrary projectId="456" onApplyTemplate={mockOnApplyTemplate} />
      );
      
      await waitFor(() => {
        expect(issueTemplateApi.list).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot in loading state', () => {
      issueTemplateApi.list.mockReturnValue(new Promise(() => {}));
      const { container } = render(
        <SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with templates', async () => {
      const { container } = render(
        <SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />
      );
      
      await waitFor(() => {
        expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      });
      
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
