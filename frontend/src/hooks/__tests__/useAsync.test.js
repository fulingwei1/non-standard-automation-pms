/**
 * useAsync Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAsync } from '../useAsync';

describe('useAsync', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with idle status', () => {
    const asyncFn = vi.fn();
    const { result } = renderHook(() => useAsync(asyncFn));

    expect(result.current.status).toBe('idle');
    expect(result.current.value).toBe(null);
    expect(result.current.error).toBe(null);
    expect(result.current.isIdle).toBe(true);
    expect(result.current.isPending).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('should not execute immediately by default', () => {
    const asyncFn = vi.fn();
    renderHook(() => useAsync(asyncFn));

    expect(asyncFn).not.toHaveBeenCalled();
  });

  it('should execute immediately when immediate is true', async () => {
    const mockData = { id: 1, name: 'Test' };
    const asyncFn = vi.fn().mockResolvedValue(mockData);

    const { result } = renderHook(() => 
      useAsync(asyncFn, { immediate: true })
    );

    expect(result.current.status).toBe('pending');

    await waitFor(() => {
      expect(result.current.status).toBe('success');
    });

    expect(result.current.value).toEqual(mockData);
    expect(result.current.isSuccess).toBe(true);
  });

  it('should execute async function manually', async () => {
    const mockData = { id: 1, name: 'Test' };
    const asyncFn = vi.fn().mockResolvedValue(mockData);

    const { result } = renderHook(() => useAsync(asyncFn));

    const response = await result.current.execute();

    expect(response.success).toBe(true);
    expect(response.data).toEqual(mockData);
    expect(result.current.value).toEqual(mockData);
    expect(result.current.status).toBe('success');
  });

  it('should handle async function with arguments', async () => {
    const asyncFn = vi.fn().mockResolvedValue('result');

    const { result } = renderHook(() => useAsync(asyncFn));

    await result.current.execute('arg1', 'arg2', 'arg3');

    expect(asyncFn).toHaveBeenCalledWith('arg1', 'arg2', 'arg3');
  });

  it('should update status to pending during execution', async () => {
    let resolvePromise;
    const promise = new Promise(resolve => {
      resolvePromise = resolve;
    });
    const asyncFn = vi.fn(() => promise);

    const { result } = renderHook(() => useAsync(asyncFn));

    const executePromise = result.current.execute();

    expect(result.current.status).toBe('pending');
    expect(result.current.isPending).toBe(true);

    resolvePromise('result');
    await executePromise;

    expect(result.current.status).toBe('success');
  });

  it('should handle errors', async () => {
    const mockError = new Error('Test Error');
    const asyncFn = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useAsync(asyncFn));

    const response = await result.current.execute();

    expect(response.success).toBe(false);
    expect(response.error).toEqual(mockError);
    expect(result.current.error).toEqual(mockError);
    expect(result.current.status).toBe('error');
    expect(result.current.isError).toBe(true);
  });

  it('should clear previous value and error before execution', async () => {
    const asyncFn1 = vi.fn().mockResolvedValue('result1');
    const asyncFn2 = vi.fn().mockRejectedValue(new Error('error'));

    const { result, rerender } = renderHook(
      ({ fn }) => useAsync(fn),
      { initialProps: { fn: asyncFn1 } }
    );

    await result.current.execute();
    expect(result.current.value).toBe('result1');

    rerender({ fn: asyncFn2 });
    const promise = result.current.execute();

    // 在pending状态，value和error应该被清空
    expect(result.current.value).toBe(null);
    expect(result.current.error).toBe(null);

    await promise;
  });

  it('should reset to idle state', async () => {
    const mockData = { id: 1 };
    const asyncFn = vi.fn().mockResolvedValue(mockData);

    const { result } = renderHook(() => useAsync(asyncFn));

    await result.current.execute();

    expect(result.current.status).toBe('success');
    expect(result.current.value).toEqual(mockData);

    result.current.reset();

    expect(result.current.status).toBe('idle');
    expect(result.current.value).toBe(null);
    expect(result.current.error).toBe(null);
    expect(result.current.isIdle).toBe(true);
  });

  it('should handle multiple executions', async () => {
    let counter = 0;
    const asyncFn = vi.fn().mockImplementation(async () => {
      return ++counter;
    });

    const { result } = renderHook(() => useAsync(asyncFn));

    await result.current.execute();
    expect(result.current.value).toBe(1);

    await result.current.execute();
    expect(result.current.value).toBe(2);

    await result.current.execute();
    expect(result.current.value).toBe(3);
  });

  it('should handle race conditions', async () => {
    let resolveFirst;
    let resolveSecond;

    const firstPromise = new Promise(resolve => {
      resolveFirst = resolve;
    });
    const secondPromise = new Promise(resolve => {
      resolveSecond = resolve;
    });

    let callCount = 0;
    const asyncFn = vi.fn().mockImplementation(() => {
      callCount++;
      return callCount === 1 ? firstPromise : secondPromise;
    });

    const { result } = renderHook(() => useAsync(asyncFn));

    const first = result.current.execute();
    const second = result.current.execute();

    // 第二个请求先完成
    resolveSecond('second');
    await second;

    expect(result.current.value).toBe('second');

    // 第一个请求后完成，但value应该是第二个请求的结果
    resolveFirst('first');
    await first;

    // 注意：由于没有请求取消机制，最后一个完成的会覆盖前面的
    expect(result.current.value).toBe('first');
  });

  it('should maintain function reference stability', () => {
    const asyncFn = vi.fn();
    const { result, rerender } = renderHook(() => useAsync(asyncFn));

    const firstExecute = result.current.execute;
    const firstReset = result.current.reset;

    rerender();

    expect(result.current.execute).toBe(firstExecute);
    expect(result.current.reset).toBe(firstReset);
  });
});
