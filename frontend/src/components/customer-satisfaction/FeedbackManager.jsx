/**
 * Feedback Manager Component
 * 反馈管理组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag, Space, Button, Rate, Typography } from 'antd';
import { FEEDBACK_CATEGORIES, TABLE_CONFIG } from '@/lib/constants/customer';

const { Text } = Typography;

const FeedbackManager = ({ responses = [], loading = false, onRefresh }) => {
  const columns = useMemo(() => {
    return [
      { title: '客户', dataIndex: 'customerName', key: 'customerName', width: 140 },
      { title: '日期', dataIndex: 'createdDate', key: 'createdDate', width: 120 },
      {
        title: '评分',
        dataIndex: 'satisfactionLevel',
        key: 'satisfactionLevel',
        width: 220,
        render: (value) => (
          <span>
            <Rate disabled value={Number(value || 0)} />
            <Text type="secondary" style={{ marginLeft: 8 }}>
              {Number(value || 0).toFixed(1)}
            </Text>
          </span>
        )
      },
      {
        title: '类别',
        dataIndex: 'category',
        key: 'category',
        width: 140,
        render: (category) => <Tag>{FEEDBACK_CATEGORIES[category?.toUpperCase()]?.label || category || '-'}</Tag>
      },
      { title: '反馈内容', dataIndex: 'feedback', key: 'feedback', ellipsis: true }
    ];
  }, []);

  return (
    <Card
      title="反馈管理"
      extra={
        <Space>
          <Button onClick={() => onRefresh?.()} disabled={loading}>
            刷新
          </Button>
        </Space>
      }
    >
      <Table
        rowKey="id"
        columns={columns}
        dataSource={responses}
        loading={loading}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default FeedbackManager;

