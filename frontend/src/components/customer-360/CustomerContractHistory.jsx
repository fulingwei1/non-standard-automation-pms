/**
 * Customer Contract History Component
 * 客户合同历史组件（占位实现，保证页面可运行）
 */

import { useMemo } from 'react';
import { Card, Table, Tag } from 'antd';
import { TABLE_CONFIG, CHART_COLORS } from '@/lib/constants/customer360';

const CONTRACT_STATUS_COLORS = {
  active: '#52c41a',
  expired: '#8c8c8c',
  terminated: '#ff4d4f',
  pending: '#faad14'
};

const CustomerContractHistory = ({ contracts = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '合同号', dataIndex: 'id', key: 'id', width: 160 },
      { title: '合同名称', dataIndex: 'title', key: 'title', ellipsis: true },
      { title: '类型', dataIndex: 'type', key: 'type', width: 120 },
      {
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
        width: 140,
        render: (value) => <span style={{ color: CHART_COLORS.PURPLE }}>¥{Number(value || 0).toLocaleString()}</span>
      },
      { title: '开始日期', dataIndex: 'startDate', key: 'startDate', width: 120 },
      { title: '结束日期', dataIndex: 'endDate', key: 'endDate', width: 120 },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => <Tag color={CONTRACT_STATUS_COLORS[status] || '#1890ff'}>{status || '-'}</Tag>
      }
    ];
  }, []);

  return (
    <Card title="合同历史" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={contracts}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default CustomerContractHistory;

