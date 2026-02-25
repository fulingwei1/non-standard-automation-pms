/**
 * useDebounce Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDebounce, useDebouncedCallback } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize with the initial value', () => {
    const { result } = renderHook(() => useDebounce('initial', 500));
    expect(result.current).toBe('initial');
  });

  it('should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 500 } }
    );

    expect(result.current).toBe('initial');

    rerender({ value: 'updated', delay: 500 });
    expect(result.current).toBe('initial');

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current).toBe('updated');
  });

  it('should cancel previous timer when value changes rapidly', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'value1' } }
    );

    rerender({ value: 'value2' });
    act(() => { vi.advanceTimersByTime(250); });

    rerender({ value: 'value3' });
    act(() => { vi.advanceTimersByTime(250); });

    // Not yet 500ms from last change
    expect(result.current).toBe('value1');

    act(() => { vi.advanceTimersByTime(250); });

    expect(result.current).toBe('value3');
  });

  it('should use custom delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 1000 } }
    );

    rerender({ value: 'updated', delay: 1000 });

    act(() => { vi.advanceTimersByTime(500); });
    expect(result.current).toBe('initial');

    act(() => { vi.advanceTimersByTime(500); });
    expect(result.current).toBe('updated');
  });

  it('should handle numeric values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 0 } }
    );

    rerender({ value: 100 });
    act(() => { vi.advanceTimersByTime(300); });

    expect(result.current).toBe(100);
  });

  it('should handle object values', () => {
    const obj1 = { id: 1, name: 'Test' };
    const obj2 = { id: 2, name: 'Updated' };

    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: obj1 } }
    );

    rerender({ value: obj2 });
    act(() => { vi.advanceTimersByTime(300); });

    expect(result.current).toEqual(obj2);
  });

  it('should handle empty string', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'text' } }
    );

    rerender({ value: '' });
    act(() => { vi.advanceTimersByTime(300); });

    expect(result.current).toBe('');
  });

  it('should cleanup timeout on unmount', () => {
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');
    const { unmount } = renderHook(() => useDebounce('value', 500));

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });
});

describe('useDebouncedCallback', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should debounce callback execution', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 500));

    act(() => { result.current('arg1'); });
    expect(callback).not.toHaveBeenCalled();

    act(() => { vi.advanceTimersByTime(500); });
    expect(callback).toHaveBeenCalledWith('arg1');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should cancel previous callback when called rapidly', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 500));

    act(() => { result.current('call1'); });
    act(() => { vi.advanceTimersByTime(250); });

    act(() => { result.current('call2'); });
    act(() => { vi.advanceTimersByTime(250); });

    act(() => { result.current('call3'); });
    act(() => { vi.advanceTimersByTime(500); });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('call3');
  });

  it('should handle multiple arguments', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => { result.current('arg1', 'arg2', 'arg3'); });
    act(() => { vi.advanceTimersByTime(300); });

    expect(callback).toHaveBeenCalledWith('arg1', 'arg2', 'arg3');
  });

  it('should use custom delay', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 1000));

    act(() => { result.current('test'); });

    act(() => { vi.advanceTimersByTime(500); });
    expect(callback).not.toHaveBeenCalled();

    act(() => { vi.advanceTimersByTime(500); });
    expect(callback).toHaveBeenCalledWith('test');
  });

  it('should cleanup timeout on unmount', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => useDebouncedCallback(callback, 500));

    act(() => { result.current('test'); });

    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');
    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it('should handle callback changes', () => {
    const callback1 = vi.fn();
    const callback2 = vi.fn();

    const { result, rerender } = renderHook(
      ({ cb }) => useDebouncedCallback(cb, 300),
      { initialProps: { cb: callback1 } }
    );

    act(() => { result.current('test1'); });

    // Change callback - this creates a new debounced function
    rerender({ cb: callback2 });

    // The old timer is still running with old callback closure
    act(() => { vi.advanceTimersByTime(300); });

    // The old callback was captured in the closure, so callback1 gets called
    // This is expected behavior - the timer was set before rerender
    expect(callback1).toHaveBeenCalledWith('test1');
  });

  it('should not execute if unmounted before delay', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => 
      useDebouncedCallback(callback, 500)
    );

    act(() => { result.current('test'); });
    unmount();

    act(() => { vi.advanceTimersByTime(500); });

    expect(callback).not.toHaveBeenCalled();
  });

  it('should handle no arguments', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => { result.current(); });
    act(() => { vi.advanceTimersByTime(300); });

    expect(callback).toHaveBeenCalledWith();
  });

  it('should execute callback multiple times with sufficient delay', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    act(() => { result.current('call1'); });
    act(() => { vi.advanceTimersByTime(300); });

    act(() => { result.current('call2'); });
    act(() => { vi.advanceTimersByTime(300); });

    expect(callback).toHaveBeenCalledTimes(2);
    expect(callback).toHaveBeenNthCalledWith(1, 'call1');
    expect(callback).toHaveBeenNthCalledWith(2, 'call2');
  });
});
