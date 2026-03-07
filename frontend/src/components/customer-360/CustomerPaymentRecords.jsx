/**
 * Customer Payment Records Component
 * 客户付款记录组件（占位实现，保证页面可运行）
 */

import { useMemo } from 'react';
import { Card, Table, Tag } from 'antd';
import { PAYMENT_STATUS, TABLE_CONFIG, CHART_COLORS } from '@/lib/constants/customer360';

const CustomerPaymentRecords = ({ payments = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '流水号', dataIndex: 'id', key: 'id', width: 160 },
      { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
      {
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
        width: 140,
        render: (value) => <span style={{ color: CHART_COLORS.SUCCESS }}>¥{Number(value || 0).toLocaleString()}</span>
      },
      { title: '方式', dataIndex: 'method', key: 'method', width: 140 },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => {
          const config = PAYMENT_STATUS[status?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || status || '-'}</Tag>;
        }
      },
      { title: '关联订单', dataIndex: 'orderId', key: 'orderId', width: 160 }
    ];
  }, []);

  return (
    <Card title="付款记录" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={payments}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default CustomerPaymentRecords;

