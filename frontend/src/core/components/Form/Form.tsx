/**
 * 通用表单组件
 * 统一处理表单布局、验证、提交
 */

import React from 'react';
import { Form as AntForm, FormProps, Button, Space } from 'antd';
import { useForm } from '../../hooks/useForm';

export interface CommonFormProps<T> extends Omit<FormProps, 'onFinish'> {
  /** 初始值 */
  initialValues?: Partial<T>;
  /** 提交函数 */
  onSubmit: (values: T) => Promise<any>;
  /** 提交成功回调 */
  onSuccess?: (data: any, values: T) => void;
  /** 提交失败回调 */
  onError?: (error: Error, values: T) => void;
  /** 验证函数 */
  validate?: (values: Partial<T>) => Record<string, string>;
  /** 是否显示提交按钮 */
  showSubmitButton?: boolean;
  /** 是否显示重置按钮 */
  showResetButton?: boolean;
  /** 提交按钮文本 */
  submitText?: string;
  /** 重置按钮文本 */
  resetText?: string;
  /** 提交按钮加载状态 */
  loading?: boolean;
  /** 子元素 */
  children: React.ReactNode;
}

/**
 * 通用表单组件
 * 
 * @example
 * ```tsx
 * <CommonForm
 *   initialValues={{ name: '', code: '' }}
 *   onSubmit={async (values) => {
 *     return await projectApi.createProject(values);
 *   }}
 *   onSuccess={() => {
 *     message.success('创建成功');
 *     navigate('/projects');
 *   }}
 * >
 *   <Form.Item name="name" label="名称" rules={[{ required: true }]}>
 *     <Input />
 *   </Form.Item>
 *   <Form.Item name="code" label="编码" rules={[{ required: true }]}>
 *     <Input />
 *   </Form.Item>
 * </CommonForm>
 * ```
 */
export function CommonForm<T extends Record<string, any>>({
  initialValues,
  onSubmit,
  onSuccess,
  onError,
  validate,
  showSubmitButton = true,
  showResetButton = true,
  submitText = '提交',
  resetText = '重置',
  loading: externalLoading,
  children,
  ...formProps
}: CommonFormProps<T>) {
  const {
    values,
    errors,
    isSubmitting,
    handleChange,
    handleSubmit,
    reset,
  } = useForm({
    initialValues,
    onSubmit,
    onSuccess,
    onError,
    validate,
  });

  const loading = externalLoading ?? isSubmitting;

  return (
    <AntForm
      {...formProps}
      initialValues={initialValues}
      onFinish={handleSubmit}
      layout="vertical"
    >
      {children}

      {/* 表单按钮 */}
      {(showSubmitButton || showResetButton) && (
        <AntForm.Item>
          <Space>
            {showSubmitButton && (
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
              >
                {submitText}
              </Button>
            )}
            {showResetButton && (
              <Button onClick={reset}>
                {resetText}
              </Button>
            )}
          </Space>
        </AntForm.Item>
      )}
    </AntForm>
  );
}
