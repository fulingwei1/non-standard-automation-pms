/**
 * useApi Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useApi, useApiMutation } from '../useApi';

describe('useApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => useApi(mockApiFunction));

    expect(result.current.data).toBe(null);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(typeof result.current.execute).toBe('function');
    expect(typeof result.current.setData).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  it('should initialize with custom initial data', () => {
    const mockApiFunction = vi.fn();
    const initialData = { id: 1, name: 'Test' };
    const { result } = renderHook(() => 
      useApi(mockApiFunction, { initialData })
    );

    expect(result.current.data).toEqual(initialData);
  });

  it('should execute api call immediately when immediate is true', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });
    
    const { result } = renderHook(() => 
      useApi(mockApiFunction, { immediate: true })
    );

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(mockApiFunction).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBe(null);
  });

  it('should not execute immediately when immediate is false', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => 
      useApi(mockApiFunction, { immediate: false })
    );

    expect(mockApiFunction).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it('should execute api call manually', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    expect(result.current.loading).toBe(false);

    const promise = result.current.execute();

    expect(result.current.loading).toBe(true);

    const response = await promise;

    expect(response.success).toBe(true);
    expect(response.data).toEqual(mockData);
    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
  });

  it('should handle api call with arguments', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    await result.current.execute(1, 'param2');

    expect(mockApiFunction).toHaveBeenCalledWith(1, 'param2');
  });

  it('should handle api error', async () => {
    const mockError = new Error('API Error');
    mockError.response = { data: { detail: 'API Error Message' } };
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    const response = await result.current.execute();

    expect(response.success).toBe(false);
    expect(response.error).toBe('API Error Message');
    expect(result.current.error).toBe('API Error Message');
    expect(result.current.loading).toBe(false);
  });

  it('should handle error without response data', async () => {
    const mockApiFunction = vi.fn().mockRejectedValue(new Error('Network Error'));
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    await result.current.execute();

    expect(result.current.error).toBe('Network Error');
  });

  it('should call onSuccess callback', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });
    const onSuccess = vi.fn();
    
    const { result } = renderHook(() => 
      useApi(mockApiFunction, { onSuccess })
    );

    await result.current.execute();

    expect(onSuccess).toHaveBeenCalledWith(mockData);
  });

  it('should call onError callback', async () => {
    const mockError = new Error('API Error');
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    const onError = vi.fn();
    
    const { result } = renderHook(() => 
      useApi(mockApiFunction, { onError })
    );

    await result.current.execute();

    expect(onError).toHaveBeenCalledWith(mockError);
  });

  it('should reset data and error', () => {
    const mockApiFunction = vi.fn();
    const initialData = { id: 1 };
    const { result } = renderHook(() => 
      useApi(mockApiFunction, { initialData })
    );

    result.current.setData({ id: 2 });
    expect(result.current.data).toEqual({ id: 2 });

    result.current.reset();

    expect(result.current.data).toEqual(initialData);
    expect(result.current.error).toBe(null);
  });

  it('should update data using setData', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => useApi(mockApiFunction));

    const newData = { id: 1, name: 'Updated' };
    result.current.setData(newData);

    expect(result.current.data).toEqual(newData);
  });
});

describe('useApiMutation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => useApiMutation(mockApiFunction));

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(typeof result.current.mutate).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  it('should execute mutation successfully', async () => {
    const mockData = { id: 1, name: 'Created' };
    const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });
    
    const { result } = renderHook(() => useApiMutation(mockApiFunction));

    const response = await result.current.mutate({ name: 'Created' });

    expect(response.success).toBe(true);
    expect(response.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
  });

  it('should handle mutation error', async () => {
    const mockError = new Error('Mutation Error');
    mockError.response = { data: { detail: 'Mutation Failed' } };
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    
    const { result } = renderHook(() => useApiMutation(mockApiFunction));

    const response = await result.current.mutate({ name: 'Test' });

    expect(response.success).toBe(false);
    expect(response.error).toBe('Mutation Failed');
    expect(result.current.error).toBe('Mutation Failed');
  });

  it('should call onSuccess callback', async () => {
    const mockData = { id: 1, name: 'Created' };
    const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });
    const onSuccess = vi.fn();
    
    const { result } = renderHook(() => 
      useApiMutation(mockApiFunction, { onSuccess })
    );

    await result.current.mutate({ name: 'Created' });

    expect(onSuccess).toHaveBeenCalledWith(mockData);
  });

  it('should call onError callback', async () => {
    const mockError = new Error('Mutation Error');
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    const onError = vi.fn();
    
    const { result } = renderHook(() => 
      useApiMutation(mockApiFunction, { onError })
    );

    await result.current.mutate({ name: 'Test' });

    expect(onError).toHaveBeenCalledWith(mockError);
  });

  it('should reset error state', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => useApiMutation(mockApiFunction));

    // 手动设置错误（通过内部状态）
    result.current.mutate = async () => {
      throw new Error('Test Error');
    };

    result.current.reset();

    expect(result.current.error).toBe(null);
  });

  it('should handle multiple arguments', async () => {
    const mockData = { id: 1 };
    const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });
    
    const { result } = renderHook(() => useApiMutation(mockApiFunction));

    await result.current.mutate('arg1', 'arg2', 'arg3');

    expect(mockApiFunction).toHaveBeenCalledWith('arg1', 'arg2', 'arg3');
  });

  it('should set loading state during mutation', async () => {
    let resolvePromise;
    const promise = new Promise(resolve => {
      resolvePromise = resolve;
    });
    const mockApiFunction = vi.fn(() => promise);
    
    const { result } = renderHook(() => useApiMutation(mockApiFunction));

    const mutationPromise = result.current.mutate({ name: 'Test' });
    
    expect(result.current.loading).toBe(true);

    resolvePromise({ data: { id: 1 } });
    await mutationPromise;

    expect(result.current.loading).toBe(false);
  });
});
