/**
 * useForm Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useForm } from '../useForm';

describe('useForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with initial values', () => {
    const initialValues = { name: 'John', email: 'john@test.com' };
    const { result } = renderHook(() => useForm(initialValues));

    expect(result.current.values).toEqual(initialValues);
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});
    expect(result.current.submitting).toBe(false);
  });

  it('should set field value', () => {
    const { result } = renderHook(() => useForm({ name: '' }));

    act(() => {
      result.current.setValue('name', 'Jane');
    });

    expect(result.current.values.name).toBe('Jane');
  });

  it('should clear error when field value changes', () => {
    const validate = (values) => {
      const errors = {};
      if (!values.name) errors.name = 'Required';
      return errors;
    };

    const { result } = renderHook(() => 
      useForm({ name: '' }, { validate })
    );

    // First trigger validation to set errors
    act(() => {
      result.current.validateForm();
    });

    expect(result.current.errors.name).toBe('Required');

    // Setting value should clear error for that field
    act(() => {
      result.current.setValue('name', 'Jane');
    });

    expect(result.current.errors.name).toBeUndefined();
  });

  it('should handle change event', () => {
    const { result } = renderHook(() => useForm({ name: '' }));

    act(() => {
      result.current.handleChange({ target: { name: 'name', value: 'Jane' } });
    });

    expect(result.current.values.name).toBe('Jane');
  });

  it('should mark field as touched on blur', () => {
    const { result } = renderHook(() => useForm({ name: '' }));

    act(() => {
      result.current.handleBlur({ target: { name: 'name' } });
    });

    expect(result.current.touched.name).toBe(true);
  });

  it('should validate form with validate function', () => {
    const validate = vi.fn((values) => {
      const errors = {};
      if (!values.name) errors.name = 'Name is required';
      return errors;
    });

    const { result } = renderHook(() => 
      useForm({ name: '' }, { validate })
    );

    act(() => {
      result.current.validateForm();
    });

    expect(validate).toHaveBeenCalled();
    expect(result.current.errors.name).toBe('Name is required');
  });

  it('should handle form submission successfully', async () => {
    const onSubmit = vi.fn().mockResolvedValue();
    const { result } = renderHook(() => 
      useForm({ name: 'John' }, { onSubmit })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).toHaveBeenCalledWith({ name: 'John' });
    expect(result.current.submitting).toBe(false);
  });

  it('should prevent submission if validation fails', async () => {
    const validate = (values) => {
      const errors = {};
      if (!values.name) errors.name = 'Required';
      return errors;
    };
    const onSubmit = vi.fn();

    const { result } = renderHook(() => 
      useForm({ name: '' }, { validate, onSubmit })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onSubmit).not.toHaveBeenCalled();
    expect(result.current.errors.name).toBe('Required');
  });

  it('should set submitting state during submission', async () => {
    let resolvePromise;
    const promise = new Promise(resolve => {
      resolvePromise = resolve;
    });
    const onSubmit = vi.fn(() => promise);

    const { result } = renderHook(() => 
      useForm({ name: 'John' }, { onSubmit })
    );

    let submitPromise;
    act(() => {
      submitPromise = result.current.handleSubmit();
    });

    // After initiating submit but before resolution
    expect(result.current.submitting).toBe(true);

    await act(async () => {
      resolvePromise();
      await submitPromise;
    });

    expect(result.current.submitting).toBe(false);
  });

  it('should reset form values', () => {
    const initialValues = { name: 'John', email: 'john@test.com' };
    const { result } = renderHook(() => useForm(initialValues));

    act(() => {
      result.current.setValue('name', 'Jane');
    });

    act(() => {
      result.current.setValue('email', 'jane@test.com');
    });

    expect(result.current.values.name).toBe('Jane');

    act(() => {
      result.current.reset();
    });

    expect(result.current.values).toEqual(initialValues);
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});
  });

  it('should set multiple errors', () => {
    const { result } = renderHook(() => useForm({ name: '', email: '' }));

    act(() => {
      result.current.setErrors({
        name: 'Name is required',
        email: 'Email is required'
      });
    });

    expect(result.current.errors).toEqual({
      name: 'Name is required',
      email: 'Email is required'
    });
  });

  it('should set multiple values at once', () => {
    const { result } = renderHook(() => 
      useForm({ name: '', email: '' })
    );

    act(() => {
      result.current.setMultiple({
        name: 'Jane',
        email: 'jane@test.com'
      });
    });

    expect(result.current.values).toEqual({
      name: 'Jane',
      email: 'jane@test.com'
    });
  });

  it('should batch set values using setValues', () => {
    const { result } = renderHook(() => 
      useForm({ name: '', email: '' })
    );

    act(() => {
      result.current.setValues({
        name: 'Jane',
        email: 'jane@test.com'
      });
    });

    expect(result.current.values).toEqual({
      name: 'Jane',
      email: 'jane@test.com'
    });
  });
});
