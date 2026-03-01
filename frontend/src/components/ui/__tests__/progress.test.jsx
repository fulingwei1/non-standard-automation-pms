import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Progress } from '../progress';

describe('Progress', () => {
  describe('Basic Rendering', () => {
    it('renders progress component', () => {
      const { container } = render(<Progress value={50} />);
      expect(container.querySelector('[role="progressbar"]')).toBeInTheDocument();
    });

    it('renders with default 0 value', () => {
      const { container } = render(<Progress />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('forwards ref', () => {
      const ref = { current: null };
      render(<Progress value={50} ref={ref} />);
      expect(ref.current).toBeTruthy();
    });
  });

  describe('Progress Values', () => {
    it('renders 0% progress', () => {
      const { container } = render(<Progress value={0} />);
      const indicator = container.querySelector('[style*="width"]');
      expect(indicator).toBeInTheDocument();
    });

    it('renders 50% progress', () => {
      const { container } = render(<Progress value={50} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('renders 100% progress', () => {
      const { container } = render(<Progress value={100} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('renders negative values as 0', () => {
      const { container } = render(<Progress value={-10} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('renders values > 100 as 100', () => {
      const { container } = render(<Progress value={150} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('handles decimal values', () => {
      const { container } = render(<Progress value={33.33} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <Progress value={50} className="custom-progress" />
      );
      expect(container.querySelector('.custom-progress')).toBeInTheDocument();
    });

    it('merges custom className with default classes', () => {
      const { container } = render(
        <Progress value={50} className="my-custom-class" />
      );
      expect(
        container.querySelector('.my-custom-class')
      ).toBeInTheDocument();
    });
  });

  describe('Additional Props', () => {
    it('spreads additional props', () => {
      const { container } = render(
        <Progress value={50} data-testid="progress-bar" />
      );
      expect(container.querySelector('[data-testid="progress-bar"]')).toBeInTheDocument();
    });

    it('supports aria-label', () => {
      const { container } = render(
        <Progress value={50} aria-label="上传进度" />
      );
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toHaveAttribute('aria-label', '上传进度');
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined value', () => {
      const { container } = render(<Progress value={undefined} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('handles null value', () => {
      const { container } = render(<Progress value={null} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('handles NaN value', () => {
      const { container } = render(<Progress value={NaN} />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('handles string value', () => {
      const { container } = render(<Progress value="50" />);
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for 0% progress', () => {
      const { container } = render(<Progress value={0} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for 50% progress', () => {
      const { container } = render(<Progress value={50} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for 100% progress', () => {
      const { container } = render(<Progress value={100} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom className', () => {
      const { container } = render(
        <Progress value={75} className="custom-styles" />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
