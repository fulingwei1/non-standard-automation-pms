/**
 * useToast Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast } from '../useToast';

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with empty toasts', () => {
    const { result } = renderHook(() => useToast());

    expect(result.current.toasts).toEqual([]);
    expect(typeof result.current.toast).toBe('function');
  });

  it('should add toast with default variant', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        title: 'Test Title',
        description: 'Test Description'
      });
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0]).toMatchObject({
      title: 'Test Title',
      description: 'Test Description',
      variant: 'default'
    });
    expect(result.current.toasts[0].id).toBeDefined();
  });

  it('should add toast with custom variant', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        title: 'Error',
        description: 'Something went wrong',
        variant: 'destructive'
      });
    });

    expect(result.current.toasts[0].variant).toBe('destructive');
  });

  it('should log to console for default variant', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        title: 'Info',
        description: 'Info message'
      });
    });

    expect(console.log).toHaveBeenCalledWith('Info: Info message');
  });

  it('should show alert for destructive variant', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        title: 'Error',
        description: 'Error message',
        variant: 'destructive'
      });
    });

    expect(window.alert).toHaveBeenCalledWith('Error: Error message');
  });

  it('should auto-remove toast after 3 seconds', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        title: 'Auto Remove',
        description: 'This will be removed'
      });
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.toasts).toHaveLength(0);
  });

  it('should handle multiple toasts', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({ title: 'Toast 1', description: 'First' });
      result.current.toast({ title: 'Toast 2', description: 'Second' });
      result.current.toast({ title: 'Toast 3', description: 'Third' });
    });

    expect(result.current.toasts).toHaveLength(3);
  });

  it('should remove toasts independently', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({ title: 'Toast 1', description: 'First' });
    });

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    act(() => {
      result.current.toast({ title: 'Toast 2', description: 'Second' });
    });

    // 再过 2 秒，第一个 toast 应该被移除
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].title).toBe('Toast 2');
  });

  it('should generate unique IDs for each toast', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({ title: 'Toast 1', description: 'First' });
    });

    // 快进一小段时间
    act(() => {
      vi.advanceTimersByTime(1);
    });

    act(() => {
      result.current.toast({ title: 'Toast 2', description: 'Second' });
    });

    const ids = result.current.toasts.map(t => t.id);
    expect(ids[0]).not.toBe(ids[1]);
    
    vi.useRealTimers();
  });

  it('should handle toast without description', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({
        title: 'Only Title'
      });
    });

    expect(result.current.toasts[0]).toMatchObject({
      title: 'Only Title',
      description: undefined,
      variant: 'default'
    });
  });

  it('should clear all toasts after timeout', () => {
    const { result } = renderHook(() => useToast());

    act(() => {
      result.current.toast({ title: 'Toast 1', description: 'First' });
      result.current.toast({ title: 'Toast 2', description: 'Second' });
      result.current.toast({ title: 'Toast 3', description: 'Third' });
    });

    expect(result.current.toasts).toHaveLength(3);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.toasts).toHaveLength(0);
  });

  it('should maintain toast function reference', () => {
    const { result, rerender } = renderHook(() => useToast());

    const firstToast = result.current.toast;
    rerender();

    expect(result.current.toast).toBe(firstToast);
  });
});
