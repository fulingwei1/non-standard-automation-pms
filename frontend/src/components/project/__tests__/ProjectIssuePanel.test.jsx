import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProjectIssuePanel from '../ProjectIssuePanel';
import { projectWorkspaceApi } from '../../../services/api';

vi.mock('../../../services/api', () => ({
  projectWorkspaceApi: {
    getIssues: vi.fn(),
    getSolutions: vi.fn(),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ProjectIssuePanel', () => {
  const mockIssues = [
    {
      id: 1,
      title: '测试问题1',
      issue_no: 'ISS-001',
      status: 'OPEN',
      priority: 'HIGH',
      severity: 'CRITICAL',
      assignee_name: '张三',
      report_date: '2024-01-01',
      has_solution: false,
    },
    {
      id: 2,
      title: '测试问题2',
      issue_no: 'ISS-002',
      status: 'RESOLVED',
      priority: 'MEDIUM',
      severity: 'MAJOR',
      assignee_name: '李四',
      report_date: '2024-01-02',
      has_solution: true,
    },
    {
      id: 3,
      title: '测试问题3',
      issue_no: 'ISS-003',
      status: 'IN_PROGRESS',
      priority: 'LOW',
      severity: 'MINOR',
      assignee_name: '王五',
      report_date: '2024-01-03',
      has_solution: false,
    },
  ];

  const mockSolutions = {
    statistics: {
      resolved_issues: 1,
      issues_with_solution: 1,
      solution_coverage: 33.3,
    },
    solutions: [
      {
        issue_id: 2,
        title: '测试问题2解决方案',
        issue_type: '缺陷',
        category: '技术问题',
        resolved_at: '2024-01-05',
        resolved_by: '李四',
        solution: '已提供解决方案',
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    projectWorkspaceApi.getIssues.mockResolvedValue({
      data: { issues: mockIssues },
    });
    projectWorkspaceApi.getSolutions.mockResolvedValue({
      data: mockSolutions,
    });
  });

  const renderWithRouter = (component) => render(<BrowserRouter>{component}</BrowserRouter>);

  it('shows loading state initially', () => {
    projectWorkspaceApi.getIssues.mockReturnValue(new Promise(() => {}));
    projectWorkspaceApi.getSolutions.mockReturnValue(new Promise(() => {}));

    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('fetches issue data on mount and renders statistics', async () => {
    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(projectWorkspaceApi.getIssues).toHaveBeenCalledTimes(1);
      expect(projectWorkspaceApi.getSolutions).toHaveBeenCalledTimes(1);
      expect(projectWorkspaceApi.getIssues).toHaveBeenCalledWith('123');
      expect(projectWorkspaceApi.getSolutions).toHaveBeenCalledWith('123');
    });

    expect(screen.getByText('问题总数')).toBeInTheDocument();
    expect(screen.getByText('解决率')).toBeInTheDocument();
    expect(screen.getAllByText('33.3%').length).toBeGreaterThan(0);
  });

  it('displays all issues by default', async () => {
    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText('测试问题1')).toBeInTheDocument();
      expect(screen.getByText('测试问题2')).toBeInTheDocument();
      expect(screen.getByText('测试问题3')).toBeInTheDocument();
      expect(screen.getByText('ISS-001')).toBeInTheDocument();
    });
  });

  it('shows technical review issue source, deadline and verification context', async () => {
    projectWorkspaceApi.getIssues.mockResolvedValue({
      data: {
        issues: [
          {
            id: 9,
            title: '技术评审问题：定位夹具方案复核',
            issue_no: 'IS-TR-001',
            category: 'TECHNICAL',
            issue_type: 'TECHNICAL_REVIEW',
            description: 'PDR评审发现定位夹具校核资料不完整',
            status: 'CLOSED',
            priority: 'HIGH',
            severity: 'MAJOR',
            assignee_name: '王工',
            report_date: '2026-06-21T10:00:00',
            due_date: '2026-06-25',
            impact_scope: '技术评审 RV-PDR-001',
            is_blocking: true,
            verified_result: 'VERIFIED',
            verified_at: '2026-06-22T15:30:00',
            has_solution: true,
          },
        ],
      },
    });

    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    expect(await screen.findByText('技术评审问题：定位夹具方案复核')).toBeInTheDocument();
    expect(screen.getByText('技术评审')).toBeInTheDocument();
    expect(screen.getByText('PDR评审发现定位夹具校核资料不完整')).toBeInTheDocument();
    expect(screen.getByText('截止 2026-06-25')).toBeInTheDocument();
    expect(screen.getByText('阻塞')).toBeInTheDocument();
    expect(screen.getByText('验证通过')).toBeInTheDocument();
  });

  it('filters open issues correctly', async () => {
    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText('测试问题1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('待处理', { selector: 'button' }));

    expect(screen.getByText('测试问题1')).toBeInTheDocument();
    expect(screen.getByText('测试问题3')).toBeInTheDocument();
    expect(screen.queryByText('测试问题2')).not.toBeInTheDocument();
  });

  it('filters resolved issues correctly', async () => {
    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText('测试问题2')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('已解决', { selector: 'button' }));

    expect(screen.getByText('测试问题2')).toBeInTheDocument();
    expect(screen.queryByText('测试问题1')).not.toBeInTheDocument();
    expect(screen.queryByText('测试问题3')).not.toBeInTheDocument();
  });

  it('shows issues with solutions tab correctly', async () => {
    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText('测试问题2')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('有解决方案', { selector: 'button' }));

    expect(screen.getByText('测试问题2')).toBeInTheDocument();
    expect(screen.getAllByText('已解决').length).toBeGreaterThan(0);
    expect(screen.queryByText('测试问题1')).not.toBeInTheDocument();
  });

  it('navigates to issue detail when clicking an issue card', async () => {
    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText('测试问题1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('测试问题1'));
    expect(mockNavigate).toHaveBeenCalledWith('/issues/1');
  });

  it('renders solution library summary when solutions exist', async () => {
    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText('解决方案库')).toBeInTheDocument();
      expect(screen.getByText('测试问题2解决方案')).toBeInTheDocument();
      expect(screen.getByText('缺陷')).toBeInTheDocument();
      expect(screen.getByText('技术问题')).toBeInTheDocument();
      expect(screen.getByText('已提供解决方案')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    projectWorkspaceApi.getIssues.mockRejectedValue(new Error('API Error'));
    projectWorkspaceApi.getSolutions.mockRejectedValue(new Error('API Error'));

    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalled();
      expect(screen.getByText('问题总数')).toBeInTheDocument();
      expect(screen.getAllByText('0').length).toBeGreaterThan(0);
      expect(screen.getByText('暂无问题')).toBeInTheDocument();
    });

    consoleError.mockRestore();
  });

  it('handles empty issues array', async () => {
    projectWorkspaceApi.getIssues.mockResolvedValue({
      data: { issues: [] },
    });

    renderWithRouter(<ProjectIssuePanel projectId="123" />);

    await waitFor(() => {
      expect(screen.getByText('暂无问题')).toBeInTheDocument();
    });
  });
});
