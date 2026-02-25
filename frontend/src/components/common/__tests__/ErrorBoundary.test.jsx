import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '../ErrorBoundary';

describe('ErrorBoundary', () => {
  // Suppress console.error for error boundary tests
  let consoleError;

  beforeEach(() => {
    consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleError.mockRestore();
  });

  const ThrowError = ({ shouldThrow = false, errorMessage = 'Test error' }) => {
    if (shouldThrow) {
      throw new Error(errorMessage);
    }
    return <div data-testid="child-component">Child Component</div>;
  };

  describe('Basic Rendering', () => {
    it('renders children when no error', () => {
      render(
        <ErrorBoundary>
          <div data-testid="test-child">Test Child</div>
        </ErrorBoundary>
      );
      expect(screen.getByTestId('test-child')).toBeInTheDocument();
    });

    it('renders multiple children', () => {
      render(
        <ErrorBoundary>
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
        </ErrorBoundary>
      );
      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('catches errors from children', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      expect(screen.getByText('出现错误')).toBeInTheDocument();
    });

    it('displays error message', () => {
      const errorMessage = '自定义错误消息';
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} errorMessage={errorMessage} />
        </ErrorBoundary>
      );
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('displays default error message when error has no message', () => {
      const ThrowNoMessage = () => {
        throw { error: 'no message' };
      };
      render(
        <ErrorBoundary>
          <ThrowNoMessage />
        </ErrorBoundary>
      );
      expect(screen.getByText('应用程序遇到了意外错误')).toBeInTheDocument();
    });

    it('logs error to console', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      expect(consoleError).toHaveBeenCalled();
    });
  });

  describe('Error UI', () => {
    it('displays error icon', () => {
      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('displays retry button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      expect(screen.getByText('重试')).toBeInTheDocument();
    });

    it('displays home button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      expect(screen.getByText('返回首页')).toBeInTheDocument();
    });

    it('displays error details in dev mode', () => {
      const originalEnv = import.meta.env.DEV;
      import.meta.env.DEV = true;

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText(/错误详情/)).toBeInTheDocument();

      import.meta.env.DEV = originalEnv;
    });
  });

  describe('Reset Functionality', () => {
    it('resets error state on retry click', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('出现错误')).toBeInTheDocument();

      const retryButton = screen.getByText('重试');
      fireEvent.click(retryButton);

      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.queryByText('出现错误')).not.toBeInTheDocument();
    });

    it('calls onReset callback when provided', () => {
      const mockOnReset = vi.fn();
      render(
        <ErrorBoundary onReset={mockOnReset}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const retryButton = screen.getByText('重试');
      fireEvent.click(retryButton);

      expect(mockOnReset).toHaveBeenCalled();
    });

    it('does not error when onReset is not provided', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const retryButton = screen.getByText('重试');
      expect(() => fireEvent.click(retryButton)).not.toThrow();
    });
  });

  describe('Home Button', () => {
    it('redirects to home on button click', () => {
      const originalLocation = window.location;
      delete window.location;
      window.location = { href: '' };

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      const homeButton = screen.getByText('返回首页');
      fireEvent.click(homeButton);

      expect(window.location.href).toBe('/');

      window.location = originalLocation;
    });
  });

  describe('Custom Fallback', () => {
    it('renders custom fallback when provided', () => {
      const customFallback = <div data-testid="custom-fallback">Custom Error</div>;
      
      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
      expect(screen.queryByText('出现错误')).not.toBeInTheDocument();
    });

    it('prefers custom fallback over default UI', () => {
      const customFallback = <div data-testid="custom">Custom</div>;
      
      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('custom')).toBeInTheDocument();
      expect(screen.queryByText('重试')).not.toBeInTheDocument();
    });
  });

  describe('Component Lifecycle', () => {
    it('maintains error state across re-renders', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('出现错误')).toBeInTheDocument();

      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      expect(screen.getByText('出现错误')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles nested error boundaries', () => {
      render(
        <ErrorBoundary>
          <ErrorBoundary>
            <ThrowError shouldThrow={true} />
          </ErrorBoundary>
        </ErrorBoundary>
      );
      expect(screen.getByText('出现错误')).toBeInTheDocument();
    });

    it('handles errors with undefined message', () => {
      const ThrowUndefined = () => {
        const err = new Error();
        err.message = undefined;
        throw err;
      };

      render(
        <ErrorBoundary>
          <ThrowUndefined />
        </ErrorBoundary>
      );

      expect(screen.getByText('应用程序遇到了意外错误')).toBeInTheDocument();
    });

    it('handles non-Error objects thrown', () => {
      const ThrowString = () => {
        throw 'String error';
      };

      render(
        <ErrorBoundary>
          <ThrowString />
        </ErrorBoundary>
      );

      expect(screen.getByText('应用程序遇到了意外错误')).toBeInTheDocument();
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot with normal children', () => {
      const { container } = render(
        <ErrorBoundary>
          <div>Normal content</div>
        </ErrorBoundary>
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with error state', () => {
      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} errorMessage="Snapshot error" />
        </ErrorBoundary>
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with custom fallback', () => {
      const customFallback = <div>Custom Fallback</div>;
      const { container } = render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
