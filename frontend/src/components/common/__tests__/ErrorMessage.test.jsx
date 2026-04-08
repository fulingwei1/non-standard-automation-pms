import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorMessage, EmptyState } from '../ErrorMessage';
import { Database } from 'lucide-react';

describe('ErrorMessage', () => {
  it('renders friendly fallback for a generic error', () => {
    render(<ErrorMessage error={new Error('测试错误')} />);

    expect(screen.getByText('操作失败')).toBeInTheDocument();
    expect(screen.getByText('请求未能成功完成。')).toBeInTheDocument();
    expect(screen.getByText('请稍后重试，如果问题持续请联系管理员。')).toBeInTheDocument();
  });

  it('renders custom title when provided', () => {
    render(<ErrorMessage error={new Error('测试错误')} title="自定义错误标题" />);

    expect(screen.getByText('自定义错误标题')).toBeInTheDocument();
  });

  it('renders friendly API error message from response detail', () => {
    render(
      <ErrorMessage
        error={{
          response: {
            data: {
              detail: 'API错误信息',
            },
          },
        }}
      />
    );

    expect(screen.getByText('操作失败')).toBeInTheDocument();
    expect(screen.getByText('请求未能成功完成。')).toBeInTheDocument();
  });

  it('renders unknown error copy when error is null', () => {
    render(<ErrorMessage error={null} />);

    expect(screen.getByText('操作失败')).toBeInTheDocument();
    expect(screen.getByText('发生了未知错误。')).toBeInTheDocument();
    expect(screen.getByText('请稍后重试，如果问题持续请联系管理员。')).toBeInTheDocument();
  });

  it('shows details when showDetails is true', () => {
    const error = {
      response: {
        data: { detail: '错误', code: 500 },
      },
    };

    render(<ErrorMessage error={error} showDetails />);

    expect(screen.getByText('详细信息')).toBeInTheDocument();
    expect(screen.getByText(/"detail": "错误"/)).toBeInTheDocument();
    expect(screen.getByText(/"code": 500/)).toBeInTheDocument();
  });

  it('does not show details block by default', () => {
    render(
      <ErrorMessage
        error={{ response: { data: { detail: '错误', code: 500 } } }}
      />
    );

    expect(screen.queryByText('详细信息')).not.toBeInTheDocument();
  });

  it('shows retry button only when onRetry is provided', () => {
    const onRetry = vi.fn();
    render(<ErrorMessage error={new Error('错误')} onRetry={onRetry} />);

    fireEvent.click(screen.getByText('重试'));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', () => {
    const { container } = render(
      <ErrorMessage error={new Error('错误')} className="custom-error" />
    );

    expect(container.querySelector('.custom-error')).toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('renders default empty state', () => {
    render(<EmptyState />);

    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('renders custom title and description', () => {
    render(<EmptyState title="没有找到项目" description="请创建第一个项目" />);

    expect(screen.getByText('没有找到项目')).toBeInTheDocument();
    expect(screen.getByText('请创建第一个项目')).toBeInTheDocument();
  });

  it('renders custom icon', () => {
    const { container } = render(<EmptyState icon={Database} />);

    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('renders action node when provided', () => {
    render(<EmptyState action={<button>创建新项目</button>} />);

    expect(screen.getByText('创建新项目')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<EmptyState className="custom-empty" />);

    expect(container.querySelector('.custom-empty')).toBeInTheDocument();
  });
});
