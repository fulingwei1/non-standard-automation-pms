/**
 * useDebounce Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDebounce, useDebouncedCallback } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
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

    // 更新值
    rerender({ value: 'updated', delay: 500 });

    // 在延迟之前值不应该变化
    expect(result.current).toBe('initial');

    // 快进时间
    vi.advanceTimersByTime(500);

    // 现在值应该更新了
    expect(result.current).toBe('updated');
  });

  it('should cancel previous timer when value changes rapidly', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'value1' } }
    );

    rerender({ value: 'value2' });
    vi.advanceTimersByTime(250);

    rerender({ value: 'value3' });
    vi.advanceTimersByTime(250);

    // 此时总共过了 500ms，但因为中途有更新，所以还是初始值
    expect(result.current).toBe('value1');

    // 再过 250ms，总共从最后一次更新过了 500ms
    vi.advanceTimersByTime(250);

    expect(result.current).toBe('value3');
  });

  it('should use custom delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 1000 } }
    );

    rerender({ value: 'updated', delay: 1000 });

    vi.advanceTimersByTime(500);
    expect(result.current).toBe('initial');

    vi.advanceTimersByTime(500);
    expect(result.current).toBe('updated');
  });

  it('should handle numeric values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 0 } }
    );

    rerender({ value: 100 });
    vi.advanceTimersByTime(300);

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
    vi.advanceTimersByTime(300);

    expect(result.current).toEqual(obj2);
  });

  it('should handle empty string', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'text' } }
    );

    rerender({ value: '' });
    vi.advanceTimersByTime(300);

    expect(result.current).toBe('');
  });

  it('should cleanup timeout on unmount', () => {
    const { unmount } = renderHook(() => useDebounce('value', 500));

    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

    unmount();

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });
});

describe('useDebouncedCallback', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should debounce callback execution', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 500));

    result.current('arg1');
    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(500);
    expect(callback).toHaveBeenCalledWith('arg1');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should cancel previous callback when called rapidly', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 500));

    result.current('call1');
    vi.advanceTimersByTime(250);

    result.current('call2');
    vi.advanceTimersByTime(250);

    result.current('call3');
    vi.advanceTimersByTime(500);

    // 只有最后一次调用应该执行
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('call3');
  });

  it('should handle multiple arguments', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    result.current('arg1', 'arg2', 'arg3');
    vi.advanceTimersByTime(300);

    expect(callback).toHaveBeenCalledWith('arg1', 'arg2', 'arg3');
  });

  it('should use custom delay', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 1000));

    result.current('test');

    vi.advanceTimersByTime(500);
    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(500);
    expect(callback).toHaveBeenCalledWith('test');
  });

  it('should cleanup timeout on unmount', () => {
    const callback = vi.fn();
    const { unmount } = renderHook(() => useDebouncedCallback(callback, 500));

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

    result.current('test1');

    // 更改回调
    rerender({ cb: callback2 });

    vi.advanceTimersByTime(300);

    // 应该调用新的回调
    expect(callback1).not.toHaveBeenCalled();
    expect(callback2).toHaveBeenCalledWith('test1');
  });

  it('should not execute if unmounted before delay', () => {
    const callback = vi.fn();
    const { result, unmount } = renderHook(() => 
      useDebouncedCallback(callback, 500)
    );

    result.current('test');
    unmount();

    vi.advanceTimersByTime(500);

    expect(callback).not.toHaveBeenCalled();
  });

  it('should handle no arguments', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    result.current();
    vi.advanceTimersByTime(300);

    expect(callback).toHaveBeenCalledWith();
  });

  it('should execute callback multiple times with sufficient delay', () => {
    const callback = vi.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    result.current('call1');
    vi.advanceTimersByTime(300);

    result.current('call2');
    vi.advanceTimersByTime(300);

    expect(callback).toHaveBeenCalledTimes(2);
    expect(callback).toHaveBeenNthCalledWith(1, 'call1');
    expect(callback).toHaveBeenNthCalledWith(2, 'call2');
  });
});
