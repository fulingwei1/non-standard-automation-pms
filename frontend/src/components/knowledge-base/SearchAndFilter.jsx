/**
 * Search And Filter Component
 * 高级搜索组件（占位实现）
 */

import { useMemo } from 'react';
import { Card, Form, Row, Col, Select, Space, Button, Tag, Typography } from 'antd';
import {
  KNOWLEDGE_TYPES,
  CATEGORIES,
  ACCESS_LEVELS,
  STATUS_OPTIONS
} from '@/lib/constants/knowledge';

const { Text } = Typography;

const SearchAndFilter = ({ filters, onFiltersChange, documents = [], loading = false }) => {
  const [form] = Form.useForm();

  const summary = useMemo(() => {
    return {
      total: documents.length
    };
  }, [documents.length]);

  const apply = (values) => {
    onFiltersChange?.({ ...filters, ...values });
  };

  const reset = () => {
    const next = {
      ...filters,
      type: undefined,
      category: undefined,
      accessLevel: undefined,
      status: 'published'
    };
    form.resetFields();
    onFiltersChange?.(next);
  };

  return (
    <Card title="高级搜索" loading={loading}>
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          type: filters?.type,
          category: filters?.category,
          accessLevel: filters?.accessLevel,
          status: filters?.status ?? 'published'
        }}
        onFinish={apply}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} md={6}>
            <Form.Item label="文档类型" name="type">
              <Select allowClear placeholder="选择类型">
                {Object.values(KNOWLEDGE_TYPES).map((t) => (
                  <Select.Option key={t.value} value={t.value}>
                    {t.icon} {t.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} md={6}>
            <Form.Item label="分类" name="category">
              <Select allowClear placeholder="选择分类">
                {Object.values(CATEGORIES).map((c) => (
                  <Select.Option key={c.value} value={c.value}>
                    {c.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} md={6}>
            <Form.Item label="权限" name="accessLevel">
              <Select allowClear placeholder="选择权限">
                {Object.values(ACCESS_LEVELS).map((a) => (
                  <Select.Option key={a.value} value={a.value}>
                    <Tag color={a.color}>{a.label}</Tag>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col xs={24} md={6}>
            <Form.Item label="状态" name="status">
              <Select allowClear placeholder="选择状态">
                {Object.values(STATUS_OPTIONS).map((s) => (
                  <Select.Option key={s.value} value={s.value}>
                    <Tag color={s.color}>{s.label}</Tag>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Space>
          <Button type="primary" htmlType="submit">
            应用筛选
          </Button>
          <Button onClick={reset}>重置</Button>
          <Text type="secondary">当前结果：{summary.total} 条</Text>
        </Space>
      </Form>
    </Card>
  );
};

export default SearchAndFilter;

