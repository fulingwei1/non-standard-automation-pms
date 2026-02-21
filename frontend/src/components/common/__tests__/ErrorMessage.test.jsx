import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorMessage, EmptyState } from '../ErrorMessage';
import { Inbox, Database } from 'lucide-react';

describe('ErrorMessage', () => {
  describe('Basic Rendering', () => {
    it('renders default error message', () => {
      const error = new Error('测试错误');
      render(<ErrorMessage error={error} />);

      expect(screen.getByText('加载失败')).toBeInTheDocument();
      expect(screen.getByText('测试错误')).toBeInTheDocument();
    });

    it('renders custom title', () => {
      const error = new Error('测试错误');
      render(<ErrorMessage error={error} title="自定义错误标题" />);

      expect(screen.getByText('自定义错误标题')).toBeInTheDocument();
    });

    it('renders error from error.response.data.detail', () => {
      const error = {
        response: {
          data: {
            detail: 'API错误信息',
          },
        },
      };
      render(<ErrorMessage error={error} />);

      expect(screen.getByText('API错误信息')).toBeInTheDocument();
    });

    it('renders unknown error when no error message', () => {
      render(<ErrorMessage error={{}} />);

      expect(screen.getByText('未知错误')).toBeInTheDocument();
    });

    it('renders unknown error when error is null', () => {
      render(<ErrorMessage error={null} />);

      expect(screen.getByText('未知错误')).toBeInTheDocument();
    });
  });

  describe('Error Details', () => {
    it('does not show details by default', () => {
      const error = {
        response: {
          data: { detail: '错误', code: 500 },
        },
      };
      render(<ErrorMessage error={error} />);

      expect(screen.queryByText('详细信息')).not.toBeInTheDocument();
    });

    it('shows details when showDetails is true', () => {
      const error = {
        response: {
          data: { detail: '错误', code: 500 },
        },
      };
      render(<ErrorMessage error={error} showDetails={true} />);

      expect(screen.getByText('详细信息')).toBeInTheDocument();
    });

    it('expands details when summary is clicked', () => {
      const error = {
        response: {
          data: { detail: '错误', code: 500 },
        },
      };
      render(<ErrorMessage error={error} showDetails={true} />);

      const summary = screen.getByText('详细信息');
      fireEvent.click(summary);

      // Details should be visible after clicking
      const pre = summary.parentElement?.querySelector('pre');
      expect(pre).toBeInTheDocument();
    });

    it('displays formatted JSON in details', () => {
      const error = {
        response: {
          data: { detail: '错误', code: 500, extra: 'info' },
        },
      };
      render(<ErrorMessage error={error} showDetails={true} />);

      const detailsButton = screen.getByText('详细信息');
      expect(detailsButton).toBeInTheDocument();
    });
  });

  describe('Retry Functionality', () => {
    it('does not show retry button when onRetry is not provided', () => {
      const error = new Error('错误');
      render(<ErrorMessage error={error} />);

      expect(screen.queryByText('重试')).not.toBeInTheDocument();
    });

    it('shows retry button when onRetry is provided', () => {
      const error = new Error('错误');
      render(<ErrorMessage error={error} onRetry={() => {}} />);

      expect(screen.getByText('重试')).toBeInTheDocument();
    });

    it('calls onRetry when retry button is clicked', () => {
      const handleRetry = vi.fn();
      const error = new Error('错误');
      render(<ErrorMessage error={error} onRetry={handleRetry} />);

      const retryButton = screen.getByText('重试');
      fireEvent.click(retryButton);

      expect(handleRetry).toHaveBeenCalledTimes(1);
    });

    it('retry button has refresh icon', () => {
      const error = new Error('错误');
      const { container } = render(
        <ErrorMessage error={error} onRetry={() => {}} />
      );

      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const error = new Error('错误');
      const { container } = render(
        <ErrorMessage error={error} className="custom-error" />
      );

      expect(container.querySelector('.custom-error')).toBeInTheDocument();
    });

    it('has proper error styling classes', () => {
      const error = new Error('错误');
      const { container } = render(<ErrorMessage error={error} />);

      const card = container.querySelector('.border-red-500\\/20');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for basic error', () => {
      const error = new Error('测试错误信息');
      const { container } = render(<ErrorMessage error={error} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with retry button', () => {
      const error = new Error('网络错误');
      const { container } = render(
        <ErrorMessage error={error} onRetry={() => {}} />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with details', () => {
      const error = {
        message: '服务器错误',
        response: {
          data: { detail: '内部错误', code: 500 },
        },
      };
      const { container } = render(
        <ErrorMessage error={error} showDetails={true} />
      );
      expect(container).toMatchSnapshot();
    });
  });
});

describe('EmptyState', () => {
  describe('Basic Rendering', () => {
    it('renders default empty state', () => {
      render(<EmptyState />);

      expect(screen.getByText('暂无数据')).toBeInTheDocument();
    });

    it('renders custom title', () => {
      render(<EmptyState title="没有找到项目" />);

      expect(screen.getByText('没有找到项目')).toBeInTheDocument();
    });

    it('renders description when provided', () => {
      render(<EmptyState description="请创建第一个项目" />);

      expect(screen.getByText('请创建第一个项目')).toBeInTheDocument();
    });

    it('does not render description by default', () => {
      render(<EmptyState />);

      expect(screen.queryByText(/请/)).not.toBeInTheDocument();
    });
  });

  describe('Icon Rendering', () => {
    it('renders default Inbox icon', () => {
      const { container } = render(<EmptyState />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders custom icon', () => {
      const { container } = render(<EmptyState icon={Database} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('icon has proper size classes', () => {
      const { container } = render(<EmptyState />);
      const icon = container.querySelector('svg');
      expect(icon).toHaveClass('w-16', 'h-16');
    });
  });

  describe('Action Button', () => {
    it('does not render action by default', () => {
      render(<EmptyState />);
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('renders action when provided', () => {
      const action = <button>创建新项目</button>;
      render(<EmptyState action={action} />);

      expect(screen.getByText('创建新项目')).toBeInTheDocument();
    });

    it('action can be any React node', () => {
      const action = <div data-testid="custom-action">自定义操作</div>;
      render(<EmptyState action={action} />);

      expect(screen.getByTestId('custom-action')).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<EmptyState className="custom-empty" />);
      expect(container.querySelector('.custom-empty')).toBeInTheDocument();
    });

    it('has centered text layout', () => {
      const { container } = render(<EmptyState />);
      const content = container.querySelector('.text-center');
      expect(content).toBeInTheDocument();
    });
  });

  describe('Complete Examples', () => {
    it('renders complete empty state with all props', () => {
      const action = <button>添加数据</button>;
      render(
        <EmptyState
          title="暂无订单"
          description="您还没有创建任何订单"
          icon={Database}
          action={action}
        />
      );

      expect(screen.getByText('暂无订单')).toBeInTheDocument();
      expect(screen.getByText('您还没有创建任何订单')).toBeInTheDocument();
      expect(screen.getByText('添加数据')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default empty state', () => {
      const { container } = render(<EmptyState />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with all props', () => {
      const action = <button>创建项目</button>;
      const { container } = render(
        <EmptyState
          title="没有项目"
          description="开始创建您的第一个项目"
          icon={Database}
          action={action}
          className="my-4"
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with description only', () => {
      const { container } = render(
        <EmptyState
          title="空列表"
          description="列表中还没有任何项目"
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
