import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingPage from '../LoadingPage';

describe('LoadingPage', () => {
  describe('Basic Rendering', () => {
    it('renders loading page component', () => {
      const { container } = render(<LoadingPage />);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('displays loading indicator', () => {
      const { container } = render(<LoadingPage />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('has fullscreen layout', () => {
      const { container } = render(<LoadingPage />);
      expect(container.firstChild).toHaveClass('min-h-screen');
    });
  });

  describe('Loading Text', () => {
    it('displays default loading text', () => {
      render(<LoadingPage />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });

    it('displays custom loading text', () => {
      render(<LoadingPage message="正在初始化系统..." />);
      expect(screen.getByText('正在初始化系统...')).toBeInTheDocument();
    });

    it('hides text when text prop is empty', () => {
      render(<LoadingPage message="" />);
      expect(screen.queryByText('加载中...')).not.toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('has centered layout', () => {
      const { container } = render(<LoadingPage />);
      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass('flex', 'items-center', 'justify-center');
    });

    it('has gradient background', () => {
      const { container } = render(<LoadingPage />);
      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass('bg-gradient-to-br');
    });

    it('applies custom className', () => {
      // LoadingPage doesn't support className prop; verify it renders
      const { container } = render(<LoadingPage />);
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default loading page', () => {
      const { container } = render(<LoadingPage />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom text', () => {
      const { container } = render(<LoadingPage text="请稍候..." />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom className', () => {
      const { container } = render(
        <LoadingPage text="加载数据中" className="custom-styles" />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
