import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import SolutionLibrary from '../SolutionLibrary';
import { issueTemplateApi } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  issueTemplateApi: {
    list: vi.fn(),
  },
}));

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

  it('shows loading state initially', () => {
    issueTemplateApi.list.mockReturnValue(new Promise(() => {}));

    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('loads templates on mount with expected params', async () => {
    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(issueTemplateApi.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
        is_active: true,
      });
    });
  });

  it('renders mapped template data', async () => {
    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(screen.getByText('解决方案模板库')).toBeInTheDocument();
      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
      expect(screen.getByText('需求变更处理')).toBeInTheDocument();
      expect(screen.getByText('适用于系统性能优化场景')).toBeInTheDocument();
      expect(screen.getByText('使用 15 次')).toBeInTheDocument();
      expect(screen.getByText(/分析性能瓶颈/)).toBeInTheDocument();
    });
  });

  it('filters templates by search query in template name', async () => {
    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('搜索解决方案模板...'), {
      target: { value: '性能' },
    });

    expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    expect(screen.queryByText('需求变更处理')).not.toBeInTheDocument();
  });

  it('filters templates by search query in solution content', async () => {
    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('搜索解决方案模板...'), {
      target: { value: '评估影响' },
    });

    expect(screen.getByText('需求变更处理')).toBeInTheDocument();
    expect(screen.queryByText('性能优化方案')).not.toBeInTheDocument();
  });

  it('shows no matched templates when search misses', async () => {
    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('搜索解决方案模板...'), {
      target: { value: '不存在的模板' },
    });

    expect(screen.getByText('没有找到匹配的模板')).toBeInTheDocument();
  });

  it('applies template with mapped payload', async () => {
    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole('button', { name: /应用模板/i })[0]);

    expect(mockOnApplyTemplate).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 1,
        template_name: '性能优化方案',
        applicable_scenarios: '适用于系统性能优化场景',
        solution: '1. 分析性能瓶颈\n2. 优化代码\n3. 测试验证',
      })
    );
  });

  it('renders empty state when template list is empty', async () => {
    issueTemplateApi.list.mockResolvedValue({
      data: { items: [] },
    });

    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(screen.getByText('暂无解决方案模板')).toBeInTheDocument();
    });
  });

  it('handles null/array-like API payload safely', async () => {
    issueTemplateApi.list.mockResolvedValueOnce({ data: null });
    const { rerender } = render(
      <SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />
    );

    await waitFor(() => {
      expect(screen.getByText('暂无解决方案模板')).toBeInTheDocument();
    });

    issueTemplateApi.list.mockResolvedValueOnce({ data: mockTemplates });
    rerender(<SolutionLibrary projectId="456" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(screen.getByText('性能优化方案')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    issueTemplateApi.list.mockRejectedValue(new Error('API Error'));

    render(<SolutionLibrary projectId="123" onApplyTemplate={mockOnApplyTemplate} />);

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalled();
      expect(screen.getByText('暂无解决方案模板')).toBeInTheDocument();
    });

    consoleError.mockRestore();
  });
});
