/**
 * 通用表单Hook
 * 统一处理表单状态、验证、提交
 */

import { useState, useCallback, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

export interface UseFormOptions<T> {
  initialValues?: Partial<T>;
  onSubmit: (values: T) => Promise<any>;
  onSuccess?: (data: any, values: T) => void;
  onError?: (error: Error, values: T) => void;
  validate?: (values: Partial<T>) => Record<string, string>;
  resetOnSuccess?: boolean;
}

/**
 * 通用表单Hook
 * 
 * @example
 * ```tsx
 * const {
 *   values,
 *   errors,
 *   touched,
 *   isSubmitting,
 *   handleChange,
 *   handleSubmit,
 *   reset
 * } = useForm({
 *   initialValues: { name: '', code: '' },
 *   onSubmit: async (values) => {
 *     return await projectApi.createProject(values);
 *   },
 *   onSuccess: () => {
 *     message.success('创建成功');
 *     navigate('/projects');
 *   }
 * });
 * ```
 */
export function useForm<T extends Record<string, any>>(
  options: UseFormOptions<T>
) {
  const {
    initialValues = {} as Partial<T>,
    onSubmit,
    onSuccess,
    onError,
    validate,
    resetOnSuccess = true,
  } = options;

  const [values, setValues] = useState<Partial<T>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const queryClient = useQueryClient();

  // 提交Mutation
  const mutation = useMutation({
    mutationFn: onSubmit,
    onSuccess: (data, variables) => {
      if (resetOnSuccess) {
        reset();
      }
      onSuccess?.(data, variables);
    },
    onError: (error: Error, variables) => {
      onError?.(error, variables);
    },
  });

  // 字段变更处理
  const handleChange = useCallback((
    name: keyof T,
    value: any
  ) => {
    setValues(prev => ({ ...prev, [name]: value }));
    setTouched(prev => ({ ...prev, [name]: true }));
    
    // 清除该字段的错误
    if (errors[name as string]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name as string];
        return newErrors;
      });
    }
  }, [errors]);

  // 批量更新值
  const setValuesBatch = useCallback((newValues: Partial<T>) => {
    setValues(prev => ({ ...prev, ...newValues }));
  }, []);

  // 验证表单
  const validateForm = useCallback((): boolean => {
    if (validate) {
      const validationErrors = validate(values);
      setErrors(validationErrors);
      return Object.keys(validationErrors).length === 0;
    }
    return true;
  }, [values, validate]);

  // 提交表单
  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();
    
    // 验证
    if (!validateForm()) {
      return;
    }

    // 提交
    await mutation.mutateAsync(values as T);
  }, [values, validateForm, mutation]);

  // 重置表单
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  // 设置错误
  const setFieldError = useCallback((name: keyof T, error: string) => {
    setErrors(prev => ({ ...prev, [name as string]: error }));
  }, []);

  // 设置字段值
  const setFieldValue = useCallback((name: keyof T, value: any) => {
    handleChange(name, value);
  }, [handleChange]);

  // 检查字段是否被触摸
  const isFieldTouched = useCallback((name: keyof T) => {
    return touched[name as string] || false;
  }, [touched]);

  // 获取字段错误
  const getFieldError = useCallback((name: keyof T) => {
    return errors[name as string];
  }, [errors]);

  return {
    // 值
    values,
    
    // 状态
    errors,
    touched,
    isSubmitting: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    
    // 方法
    handleChange,
    handleSubmit,
    setValues: setValuesBatch,
    setFieldValue,
    setFieldError,
    reset,
    validate: validateForm,
    
    // 辅助方法
    isFieldTouched,
    getFieldError,
  };
}
