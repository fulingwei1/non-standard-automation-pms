import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  LoadingSpinner,
  LoadingCard,
  LoadingSkeleton,
} from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  describe('Basic Rendering', () => {
    it('renders spinner by default', () => {
      const { container } = render(<LoadingSpinner />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders with text when provided', () => {
      render(<LoadingSpinner text="加载中..." />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });

    it('renders without text by default', () => {
      render(<LoadingSpinner />);
      expect(screen.queryByText(/加载/)).not.toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('renders small size', () => {
      const { container } = render(<LoadingSpinner size="sm" />);
      const svg = container.querySelector('svg');
      expect(svg).toHaveClass('w-4', 'h-4');
    });

    it('renders medium size (default)', () => {
      const { container } = render(<LoadingSpinner size="md" />);
      const svg = container.querySelector('svg');
      expect(svg).toHaveClass('w-8', 'h-8');
    });

    it('renders large size', () => {
      const { container } = render(<LoadingSpinner size="lg" />);
      const svg = container.querySelector('svg');
      expect(svg).toHaveClass('w-12', 'h-12');
    });

    it('renders extra large size', () => {
      const { container } = render(<LoadingSpinner size="xl" />);
      const svg = container.querySelector('svg');
      expect(svg).toHaveClass('w-16', 'h-16');
    });
  });

  describe('Layout Modes', () => {
    it('renders inline spinner by default', () => {
      const { container } = render(<LoadingSpinner />);
      expect(
        container.querySelector('.min-h-screen')
      ).not.toBeInTheDocument();
    });

    it('renders fullScreen spinner', () => {
      const { container } = render(<LoadingSpinner fullScreen={true} />);
      expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
    });

    it('fullScreen has proper background classes', () => {
      const { container } = render(<LoadingSpinner fullScreen={true} />);
      const fullScreenDiv = container.querySelector('.min-h-screen');
      expect(fullScreenDiv).toHaveClass('bg-gradient-to-br');
      expect(fullScreenDiv).toHaveClass('from-slate-950');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <LoadingSpinner className="custom-class" />
      );
      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('applies className with size', () => {
      const { container } = render(
        <LoadingSpinner size="lg" className="my-custom-spinner" />
      );
      expect(
        container.querySelector('.my-custom-spinner')
      ).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default spinner', () => {
      const { container } = render(<LoadingSpinner />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for spinner with text', () => {
      const { container } = render(
        <LoadingSpinner text="正在加载数据..." />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for fullScreen spinner', () => {
      const { container } = render(
        <LoadingSpinner fullScreen={true} text="系统启动中" />
      );
      expect(container).toMatchSnapshot();
    });
  });
});

describe('LoadingCard', () => {
  describe('Basic Rendering', () => {
    it('renders default 3 rows', () => {
      const { container } = render(<LoadingCard />);
      const rows = container.querySelectorAll('.animate-pulse');
      expect(rows).toHaveLength(3);
    });

    it('renders custom number of rows', () => {
      const { container } = render(<LoadingCard rows={5} />);
      const rows = container.querySelectorAll('.animate-pulse');
      expect(rows).toHaveLength(5);
    });

    it('renders single row', () => {
      const { container } = render(<LoadingCard rows={1} />);
      const rows = container.querySelectorAll('.animate-pulse');
      expect(rows).toHaveLength(1);
    });
  });

  describe('Styling', () => {
    it('applies default styling to rows', () => {
      const { container } = render(<LoadingCard />);
      const firstRow = container.querySelector('.animate-pulse');
      expect(firstRow).toHaveClass('bg-slate-800/50');
      expect(firstRow).toHaveClass('rounded-lg');
      expect(firstRow).toHaveClass('h-20');
    });

    it('applies custom className to container', () => {
      const { container } = render(<LoadingCard className="custom-card" />);
      expect(container.querySelector('.custom-card')).toBeInTheDocument();
    });

    it('has proper spacing classes', () => {
      const { container } = render(<LoadingCard />);
      expect(container.querySelector('.space-y-3')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default loading card', () => {
      const { container } = render(<LoadingCard />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom rows', () => {
      const { container } = render(<LoadingCard rows={7} />);
      expect(container).toMatchSnapshot();
    });
  });
});

describe('LoadingSkeleton', () => {
  describe('Basic Rendering', () => {
    it('renders skeleton element', () => {
      const { container } = render(<LoadingSkeleton />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });

    it('has proper default classes', () => {
      const { container } = render(<LoadingSkeleton />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('bg-slate-800/50');
      expect(skeleton).toHaveClass('rounded');
    });
  });

  describe('Size Customization', () => {
    it('renders with default width', () => {
      const { container } = render(<LoadingSkeleton />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('w-full');
    });

    it('renders with custom width', () => {
      const { container } = render(<LoadingSkeleton width="w-1/2" />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('w-1/2');
    });

    it('renders with default height', () => {
      const { container } = render(<LoadingSkeleton />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('h-4');
    });

    it('renders with custom height', () => {
      const { container } = render(<LoadingSkeleton height="h-8" />);
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('h-8');
    });

    it('renders with both custom width and height', () => {
      const { container } = render(
        <LoadingSkeleton width="w-3/4" height="h-12" />
      );
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('w-3/4');
      expect(skeleton).toHaveClass('h-12');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <LoadingSkeleton className="my-skeleton" />
      );
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('my-skeleton');
    });

    it('merges custom className with default classes', () => {
      const { container } = render(
        <LoadingSkeleton className="opacity-50" />
      );
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toHaveClass('opacity-50');
      expect(skeleton).toHaveClass('bg-slate-800/50');
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default skeleton', () => {
      const { container } = render(<LoadingSkeleton />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom dimensions', () => {
      const { container } = render(
        <LoadingSkeleton width="w-32" height="h-16" />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom styling', () => {
      const { container } = render(
        <LoadingSkeleton
          width="w-full"
          height="h-24"
          className="rounded-xl opacity-75"
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
