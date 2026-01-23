/**
 * useForm Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useForm } from '../useForm';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const initialValues = { name: 'Test', code: 'TEST001' };
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues,
        onSubmit: mockOnSubmit,
      }),
      { wrapper: createWrapper() }
    );

    expect(result.current.values).toEqual(initialValues);
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});
    expect(result.current.isSubmitting).toBe(false);
  });

  it('should handle field change', () => {
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: '', code: '' },
        onSubmit: mockOnSubmit,
      }),
      { wrapper: createWrapper() }
    );

    act(() => {
      result.current.handleChange('name', 'New Name');
    });

    expect(result.current.values.name).toBe('New Name');
    expect(result.current.touched.name).toBe(true);
  });

  it('should clear error on field change', () => {
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: '', code: '' },
        onSubmit: mockOnSubmit,
      }),
      { wrapper: createWrapper() }
    );

    act(() => {
      result.current.setFieldError('name', 'Required');
    });

    expect(result.current.errors.name).toBe('Required');

    act(() => {
      result.current.handleChange('name', 'New Name');
    });

    expect(result.current.errors.name).toBeUndefined();
  });

  it('should validate form before submit', async () => {
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });
    const mockValidate = vi.fn().mockReturnValue({ name: 'Required' });

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: '', code: '' },
        onSubmit: mockOnSubmit,
        validate: mockValidate,
      }),
      { wrapper: createWrapper() }
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(mockValidate).toHaveBeenCalled();
    expect(result.current.errors.name).toBe('Required');
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('should submit form when valid', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockOnSubmit = vi.fn().mockResolvedValue(mockData);
    const mockOnSuccess = vi.fn();

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: 'Test', code: 'TEST001' },
        onSubmit: mockOnSubmit,
        onSuccess: mockOnSuccess,
      }),
      { wrapper: createWrapper() }
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    }, { timeout: 3000 });

    // 验证提交被调用，参数可能顺序不同
    expect(mockOnSubmit).toHaveBeenCalled();
    const submitCall = mockOnSubmit.mock.calls[0][0];
    expect(submitCall.name).toBe('Test');
    expect(submitCall.code).toBe('TEST001');
    
    // 验证成功回调被调用
    expect(mockOnSuccess).toHaveBeenCalled();
    const successCall = mockOnSuccess.mock.calls[0];
    expect(successCall[0]).toEqual(mockData);
    expect(successCall[1].name).toBe('Test');
    expect(successCall[1].code).toBe('TEST001');
  });

  it('should handle submit error', async () => {
    const mockError = new Error('Submit failed');
    const mockOnSubmit = vi.fn().mockRejectedValue(mockError);
    const mockOnError = vi.fn();

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: 'Test', code: 'TEST001' },
        onSubmit: mockOnSubmit,
        onError: mockOnError,
      }),
      { wrapper: createWrapper() }
    );

    await act(async () => {
      try {
        await result.current.handleSubmit();
      } catch (e) {
        // 错误会被mutation捕获，这里不需要处理
      }
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    }, { timeout: 3000 });

    expect(mockOnError).toHaveBeenCalledWith(mockError, expect.objectContaining({ name: 'Test', code: 'TEST001' }));
  });

  it('should reset form', () => {
    const initialValues = { name: 'Test', code: 'TEST001' };
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues,
        onSubmit: mockOnSubmit,
      }),
      { wrapper: createWrapper() }
    );

    act(() => {
      result.current.handleChange('name', 'Changed');
      result.current.setFieldError('code', 'Error');
    });

    expect(result.current.values.name).toBe('Changed');
    expect(result.current.errors.code).toBe('Error');

    act(() => {
      result.current.reset();
    });

    expect(result.current.values).toEqual(initialValues);
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});
  });

  it('should not reset on success when resetOnSuccess is false', async () => {
    const initialValues = { name: 'Test', code: 'TEST001' };
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues,
        onSubmit: mockOnSubmit,
        resetOnSuccess: false,
      }),
      { wrapper: createWrapper() }
    );

    act(() => {
      result.current.handleChange('name', 'Changed');
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.values.name).toBe('Changed'); // 不应该重置
  });

  it('should set field value', () => {
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: '', code: '' },
        onSubmit: mockOnSubmit,
      }),
      { wrapper: createWrapper() }
    );

    act(() => {
      result.current.setFieldValue('name', 'New Value');
    });

    expect(result.current.values.name).toBe('New Value');
    expect(result.current.touched.name).toBe(true);
  });

  it('should check if field is touched', () => {
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: '', code: '' },
        onSubmit: mockOnSubmit,
      }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isFieldTouched('name')).toBe(false);

    act(() => {
      result.current.handleChange('name', 'Test');
    });

    expect(result.current.isFieldTouched('name')).toBe(true);
  });

  it('should get field error', () => {
    const mockOnSubmit = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useForm({
        initialValues: { name: '', code: '' },
        onSubmit: mockOnSubmit,
      }),
      { wrapper: createWrapper() }
    );

    act(() => {
      result.current.setFieldError('name', 'Required');
    });

    expect(result.current.getFieldError('name')).toBe('Required');
    expect(result.current.getFieldError('code')).toBeUndefined();
  });
});
