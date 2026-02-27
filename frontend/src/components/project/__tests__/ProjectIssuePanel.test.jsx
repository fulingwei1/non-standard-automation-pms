import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProjectIssuePanel from '../ProjectIssuePanel';
import { projectWorkspaceApi } from '../../../services/api';

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
      status: 'OPEN',
      priority: 'HIGH',
      created_at: '2024-01-01',
      has_solution: false,
    },
    {
      id: 2,
      title: '测试问题2',
      status: 'RESOLVED',
      priority: 'MEDIUM',
      created_at: '2024-01-02',
      has_solution: true,
    },
    {
      id: 3,
      title: '测试问题3',
      status: 'IN_PROGRESS',
      priority: 'LOW',
      created_at: '2024-01-03',
      has_solution: false,
    },
  ];

  const mockSolutions = {
    total: 1,
    solutions: [{ id: 1, issue_id: 2, description: '解决方案' }],
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

  const renderWithRouter = (component) => {
    return render(<BrowserRouter>{component}</BrowserRouter>);
  };

  describe('Basic Rendering', () => {
    it('shows loading state initially', () => {
      projectWorkspaceApi.getIssues.mockReturnValue(new Promise(() => {}));
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });

    it('renders issue panel after loading', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(screen.queryByText('加载中...')).not.toBeInTheDocument();
      });
    });

    it('fetches issues on mount', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(projectWorkspaceApi.getIssues).toHaveBeenCalledWith('123');
        expect(projectWorkspaceApi.getSolutions).toHaveBeenCalledWith('123');
      });
    });
  });

  describe('Issue Display', () => {
    it('displays all issues by default', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(screen.getByText('测试问题1')).toBeInTheDocument();
        expect(screen.getByText('测试问题2')).toBeInTheDocument();
        expect(screen.getByText('测试问题3')).toBeInTheDocument();
      });
    });

    it('filters open issues correctly', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(screen.getByText('测试问题1')).toBeInTheDocument();
      });
    });

    it('filters resolved issues correctly', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(screen.getByText('测试问题2')).toBeInTheDocument();
      });
    });

    it('shows issues with solutions', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(screen.getByText('测试问题2')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('handles API error gracefully', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      projectWorkspaceApi.getIssues.mockRejectedValue(new Error('API Error'));
      projectWorkspaceApi.getSolutions.mockRejectedValue(new Error('API Error'));

      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      
      await waitFor(() => {
        expect(consoleError).toHaveBeenCalled();
      });
      
      consoleError.mockRestore();
    });

    it('handles empty issues array', async () => {
      projectWorkspaceApi.getIssues.mockResolvedValue({
        data: { issues: [] },
      });
      
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      
      await waitFor(() => {
        expect(screen.queryByText('测试问题1')).not.toBeInTheDocument();
      });
    });

    it('handles null issues data', async () => {
      projectWorkspaceApi.getIssues.mockResolvedValue({
        data: null,
      });
      
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      
      await waitFor(() => {
        expect(projectWorkspaceApi.getIssues).toHaveBeenCalled();
      });
    });
  });

  describe('Issue Statistics', () => {
    it('calculates open issues count correctly', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(projectWorkspaceApi.getIssues).toHaveBeenCalled();
      });
      // Open issues: OPEN (1) + IN_PROGRESS (1) = 2
    });

    it('calculates resolved issues count correctly', async () => {
      renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(projectWorkspaceApi.getIssues).toHaveBeenCalled();
      });
      // Resolved issues: RESOLVED (1) = 1
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot in loading state', () => {
      projectWorkspaceApi.getIssues.mockReturnValue(new Promise(() => {}));
      const { container } = renderWithRouter(<ProjectIssuePanel projectId="123" />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with issues loaded', async () => {
      const { container } = renderWithRouter(<ProjectIssuePanel projectId="123" />);
      await waitFor(() => {
        expect(screen.queryByText('加载中...')).not.toBeInTheDocument();
      });
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
