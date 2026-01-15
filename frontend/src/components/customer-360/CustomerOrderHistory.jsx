/**
 * Customer Order History Component
 * 客户订单历史组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag } from 'antd';
import { ORDER_STATUS, TABLE_CONFIG, CHART_COLORS } from './customer360Constants';

const CustomerOrderHistory = ({ orders = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '订单号', dataIndex: 'id', key: 'id', width: 160 },
      { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
      { title: '产品/项目', dataIndex: 'product', key: 'product', ellipsis: true },
      {
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
        width: 140,
        render: (value) => <span style={{ color: CHART_COLORS.SUCCESS }}>¥{Number(value || 0).toLocaleString()}</span>
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => {
          const config = ORDER_STATUS[status?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || status || '-'}</Tag>;
        }
      },
      { title: '交付日期', dataIndex: 'deliveryDate', key: 'deliveryDate', width: 120 }
    ];
  }, []);

  return (
    <Card title="订单历史" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={orders}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default CustomerOrderHistory;

