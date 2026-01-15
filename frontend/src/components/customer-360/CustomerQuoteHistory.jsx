/**
 * Customer Quote History Component
 * 客户报价历史组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag } from 'antd';
import { TABLE_CONFIG, CHART_COLORS } from './customer360Constants';

const QUOTE_STATUS_COLORS = {
  accepted: '#52c41a',
  rejected: '#ff4d4f',
  pending: '#faad14',
  expired: '#8c8c8c'
};

const CustomerQuoteHistory = ({ quotes = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '报价单号', dataIndex: 'id', key: 'id', width: 160 },
      { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
      { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
      {
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
        width: 140,
        render: (value) => <span style={{ color: CHART_COLORS.PRIMARY }}>¥{Number(value || 0).toLocaleString()}</span>
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => <Tag color={QUOTE_STATUS_COLORS[status] || '#1890ff'}>{status || '-'}</Tag>
      },
      { title: '有效期至', dataIndex: 'validUntil', key: 'validUntil', width: 120 }
    ];
  }, []);

  return (
    <Card title="报价历史" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={quotes}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default CustomerQuoteHistory;

