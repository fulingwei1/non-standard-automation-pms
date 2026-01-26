/**
 * 通用筛选面板组件
 * 统一处理各种类型的筛选器
 */

import React from 'react';
import { Form, Select, Input, DatePicker, InputNumber, Space, Button } from 'antd';
import { FilterOutlined, ClearOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

export interface FilterConfig {
  key: string;
  label: string;
  type: 'select' | 'input' | 'date' | 'dateRange' | 'number' | 'numberRange';
  options?: Array<{ label: string; value: any }>;
  placeholder?: string;
  defaultValue?: any;
}

export interface FilterPanelProps {
  /** 筛选配置 */
  filters: FilterConfig[];
  /** 当前筛选值 */
  values: Record<string, any>;
  /** 筛选变更回调 */
  onChange: (values: Record<string, any>) => void;
  /** 是否显示清除按钮 */
  showClear?: boolean;
  /** 布局方式 */
  layout?: 'horizontal' | 'vertical';
}

/**
 * 通用筛选面板组件
 * 
 * @example
 * ```tsx
 * <FilterPanel
 *   filters={[
 *     { key: 'status', label: '状态', type: 'select', options: statusOptions },
 *     { key: 'date', label: '日期', type: 'dateRange' }
 *   ]}
 *   values={filters}
 *   onChange={handleFilterChange}
 * />
 * ```
 */
export function FilterPanel({
  filters,
  values,
  onChange,
  showClear = true,
  layout = 'horizontal',
}: FilterPanelProps) {
  const [form] = Form.useForm();

  // 初始化表单值
  React.useEffect(() => {
    form.setFieldsValue(values);
  }, [form, values]);

  // 处理筛选变更
  const handleValuesChange = (changedValues: any, allValues: any) => {
    // 处理日期范围
    const processedValues: Record<string, any> = {};
    
    for (const [key, value] of Object.entries(allValues)) {
      if (value === undefined || value === null) {
        continue;
      }
      
      // 处理日期范围
      if (Array.isArray(value) && value.length === 2 && dayjs.isDayjs(value[0])) {
        processedValues[key] = {
          min: value[0].format('YYYY-MM-DD'),
          max: value[1].format('YYYY-MM-DD'),
        };
      }
      // 处理单个日期
      else if (dayjs.isDayjs(value)) {
        processedValues[key] = value.format('YYYY-MM-DD');
      }
      // 处理数字范围
      else if (typeof value === 'object' && value !== null && 'min' in value && 'max' in value) {
        processedValues[key] = value;
      }
      else {
        processedValues[key] = value;
      }
    }
    
    onChange(processedValues);
  };

  // 清除筛选
  const handleClear = () => {
    form.resetFields();
    onChange({});
  };

  // 渲染筛选器
  const renderFilter = (filter: FilterConfig) => {
    const { key, label, type, options, placeholder, defaultValue } = filter;

    switch (type) {
      case 'select':
        return (
          <Form.Item key={key} name={key} label={label} style={{ marginBottom: 16 }}>
            <Select
              placeholder={placeholder || `请选择${label}`}
              allowClear
              style={{ minWidth: 150 }}
              options={options}
            />
          </Form.Item>
        );

      case 'input':
        return (
          <Form.Item key={key} name={key} label={label} style={{ marginBottom: 16 }}>
            <Input
              placeholder={placeholder || `请输入${label}`}
              allowClear
              style={{ width: 200 }}
            />
          </Form.Item>
        );

      case 'date':
        return (
          <Form.Item key={key} name={key} label={label} style={{ marginBottom: 16 }}>
            <DatePicker
              placeholder={placeholder || `请选择${label}`}
              style={{ width: 200 }}
            />
          </Form.Item>
        );

      case 'dateRange':
        return (
          <Form.Item key={key} name={key} label={label} style={{ marginBottom: 16 }}>
            <RangePicker
              placeholder={['开始日期', '结束日期']}
              style={{ width: 300 }}
            />
          </Form.Item>
        );

      case 'number':
        return (
          <Form.Item key={key} name={key} label={label} style={{ marginBottom: 16 }}>
            <InputNumber
              placeholder={placeholder || `请输入${label}`}
              style={{ width: 150 }}
            />
          </Form.Item>
        );

      case 'numberRange':
        return (
          <Form.Item key={key} name={key} label={label} style={{ marginBottom: 16 }}>
            <Input.Group compact>
              <InputNumber
                placeholder="最小值"
                style={{ width: '50%' }}
                formatter={(value) => (value ? `min: ${value}` : '')}
              />
              <InputNumber
                placeholder="最大值"
                style={{ width: '50%' }}
                formatter={(value) => (value ? `max: ${value}` : '')}
              />
            </Input.Group>
          </Form.Item>
        );

      default:
        return null;
    }
  };

  return (
    <div className="filter-panel">
      <Form
        form={form}
        layout={layout}
        onValuesChange={handleValuesChange}
        initialValues={values}
      >
        <Space wrap>
          {filters.map(renderFilter)}
          
          {showClear && (
            <Form.Item>
              <Button
                icon={<ClearOutlined />}
                onClick={handleClear}
              >
                清除
              </Button>
            </Form.Item>
          )}
        </Space>
      </Form>
    </div>
  );
}
