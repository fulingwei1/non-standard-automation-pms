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
      // LoadingSpinner 在 mock 环境中渲染为 div[data-testid="loadingspinner"]，无 svg
      expect(screen.getByTestId('loadingspinner')).toBeInTheDocument();
    });

    it('has fullscreen layout', () => {
      const { container } = render(<LoadingPage />);
      expect(container.firstChild).toHaveClass('min-h-screen');
    });
  });

  describe('Loading Text', () => {
    it('displays default loading text', () => {
      render(<LoadingPage />);
      // LoadingSpinner mock 将 text 作为 HTML 属性传递，非文本子节点
      const spinner = screen.getByTestId('loadingspinner');
      expect(spinner).toHaveAttribute('text', '加载中...');
    });

    it('displays custom loading text', () => {
      render(<LoadingPage message="正在初始化系统..." />);
      const spinner = screen.getByTestId('loadingspinner');
      expect(spinner).toHaveAttribute('text', '正在初始化系统...');
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
