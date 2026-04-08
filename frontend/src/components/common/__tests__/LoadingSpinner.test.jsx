import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  LoadingSpinner,
  LoadingCard,
  LoadingSkeleton,
} from '../LoadingSpinner';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, animate, transition, ...props }) => <div {...props}>{children}</div>,
  },
}));

describe('LoadingSpinner', () => {
  it('renders spinner by default', () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('renders with text when provided', () => {
    render(<LoadingSpinner text="加载中..." />);
    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('renders small size on wrapper', () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    expect(container.querySelector('.w-4.h-4')).toBeInTheDocument();
  });

  it('renders medium size on wrapper', () => {
    const { container } = render(<LoadingSpinner size="md" />);
    expect(container.querySelector('.w-6.h-6')).toBeInTheDocument();
  });

  it('renders large size on wrapper', () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    expect(container.querySelector('.w-8.h-8')).toBeInTheDocument();
  });

  it('renders extra large size on wrapper', () => {
    const { container } = render(<LoadingSpinner size="xl" />);
    expect(container.querySelector('.w-12.h-12')).toBeInTheDocument();
  });

  it('renders fullScreen spinner when requested', () => {
    const { container } = render(<LoadingSpinner fullScreen text="系统启动中" />);
    expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
    expect(screen.getByText('系统启动中')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="custom-class" />);
    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });
});

describe('LoadingCard', () => {
  it('renders loading card structure', () => {
    const { container } = render(<LoadingCard />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    expect(container.querySelector('.space-y-4')).toBeInTheDocument();
  });

  it('renders custom message', () => {
    render(<LoadingCard message="加载中" />);
    expect(screen.getByText('加载中')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<LoadingCard className="custom-card" />);
    expect(container.querySelector('.custom-card')).toBeInTheDocument();
  });
});

describe('LoadingSkeleton', () => {
  it('renders skeleton element', () => {
    const { container } = render(<LoadingSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('uses default width and height classes', () => {
    const { container } = render(<LoadingSkeleton />);
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toHaveClass('w-full');
    expect(skeleton).toHaveClass('h-4');
  });

  it('accepts custom width, height, and className', () => {
    const { container } = render(
      <LoadingSkeleton width="w-1/2" height="h-8" className="my-skeleton" />
    );
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toHaveClass('w-1/2');
    expect(skeleton).toHaveClass('h-8');
    expect(skeleton).toHaveClass('my-skeleton');
  });
});
