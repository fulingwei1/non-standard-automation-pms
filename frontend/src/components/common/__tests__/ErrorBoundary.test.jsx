import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '../ErrorBoundary';

function ThrowError({ message = 'Test error' }) {
  throw new Error(message);
}

function ThrowNull() {
  throw null;
}

describe('ErrorBoundary', () => {
  let consoleError;

  beforeEach(() => {
    consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleError.mockRestore();
  });

  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div data-testid="child">正常内容</div>
      </ErrorBoundary>
    );

    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('renders default fallback UI when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError message="boom" />
      </ErrorBoundary>
    );

    expect(screen.getByText('页面出了点问题')).toBeInTheDocument();
    expect(screen.getByText('重试')).toBeInTheDocument();
    expect(screen.getByText('返回首页')).toBeInTheDocument();
    expect(consoleError).toHaveBeenCalled();
  });

  it('calls onReset when retry button is clicked', () => {
    const onReset = vi.fn();

    render(
      <ErrorBoundary onReset={onReset}>
        <ThrowError />
      </ErrorBoundary>
    );

    fireEvent.click(screen.getByText('重试'));

    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it('does not throw when retry button is clicked without onReset', () => {
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(() => fireEvent.click(screen.getByText('重试'))).not.toThrow();
  });

  it('navigates home when clicking return-home button', () => {
    const originalLocation = window.location;
    delete window.location;
    window.location = { href: '' };

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    fireEvent.click(screen.getByText('返回首页'));
    expect(window.location.href).toBe('/');

    window.location = originalLocation;
  });

  it('renders custom fallback function instead of default UI', () => {
    const fallback = vi.fn((error, reset) => (
      <button onClick={reset} data-testid="custom-fallback">
        自定义错误：{error?.message || 'unknown'}
      </button>
    ));

    render(
      <ErrorBoundary fallback={fallback}>
        <ThrowNull />
      </ErrorBoundary>
    );

    expect(fallback).toHaveBeenCalledWith(null, expect.any(Function));
    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.getByText('自定义错误：unknown')).toBeInTheDocument();
    expect(screen.queryByText('页面出了点问题')).not.toBeInTheDocument();
  });
});
