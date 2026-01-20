import { useState, useCallback } from 'react';

/**
 * 表单管理 Hook
 * 
 * @param {Object} initialValues - 初始表单值
 * @param {Object} options - 配置选项
 * @param {Function} options.validate - 验证函数
 * @param {Function} options.onSubmit - 提交回调
 * 
 * @example
 * const form = useForm({
 *   name: '',
 *   email: '',
 * }, {
 *   validate: (values) => {
 *     const errors = {};
 *     if (!values.name) errors.name = '请输入姓名';
 *     return errors;
 *   },
 *   onSubmit: async (values) => {
 *     await api.create(values);
 *   },
 * });
 * 
 * <input
 *   name="name"
 *   value={form.values.name}
 *   onChange={form.handleChange}
 * />
 * {form.errors.name && <span>{form.errors.name}</span>}
 * 
 * <button onClick={form.handleSubmit} disabled={form.submitting}>
 *   提交
 * </button>
 */
export function useForm(initialValues = {}, options = {}) {
  const { validate, onSubmit } = options;

  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [submitting, setSubmitting] = useState(false);

  // 设置单个字段值
  const setValue = useCallback((name, value) => {
    setValues(prev => ({
      ...prev,
      [name]: value,
    }));
    // 清除该字段的错误
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  }, [errors]);

  // 处理onChange事件
  const handleChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    setValue(name, type === 'checkbox' ? checked : value);
  }, [setValue]);

  // 处理onBlur事件
  const handleBlur = useCallback((e) => {
    const { name } = e.target;
    setTouched(prev => ({
      ...prev,
      [name]: true,
    }));
  }, []);

  // 验证表单
  const validateForm = useCallback(() => {
    if (!validate) return {};
    const validationErrors = validate(values);
    setErrors(validationErrors || {});
    return validationErrors || {};
  }, [validate, values]);

  // 提交表单
  const handleSubmit = useCallback(async (e) => {
    e?.preventDefault();

    // 标记所有字段为已触摸
    const allTouched = {};
    Object.keys(values).forEach(key => {
      allTouched[key] = true;
    });
    setTouched(allTouched);

    // 验证
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      return { success: false, errors: validationErrors };
    }

    // 提交
    if (onSubmit) {
      try {
        setSubmitting(true);
        setErrors({});
        const result = await onSubmit(values);
        return { success: true, data: result };
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message;
        setErrors({ _form: errorMessage });
        return { success: false, error: errorMessage };
      } finally {
        setSubmitting(false);
      }
    }

    return { success: true };
  }, [values, validateForm, onSubmit]);

  // 重置表单
  const reset = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
    setSubmitting(false);
  }, [initialValues]);

  // 设置多个值
  const setMultiple = useCallback((updates) => {
    setValues(prev => ({
      ...prev,
      ...updates,
    }));
  }, []);

  // 检查字段是否有错误
  const hasError = useCallback((name) => {
    return touched[name] && errors[name];
  }, [touched, errors]);

  // 获取字段的错误信息
  const getError = useCallback((name) => {
    return touched[name] ? errors[name] : undefined;
  }, [touched, errors]);

  return {
    // 状态
    values,
    errors,
    touched,
    submitting,
    isValid: Object.keys(errors).length === 0,
    isDirty: JSON.stringify(values) !== JSON.stringify(initialValues),

    // 操作
    setValue,
    setMultiple,
    setValues,
    setErrors,
    handleChange,
    handleBlur,
    handleSubmit,
    validateForm,
    reset,
    hasError,
    getError,
  };
}
