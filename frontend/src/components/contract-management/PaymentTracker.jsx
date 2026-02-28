/**
 * Payment Tracker Component
 * 付款跟踪组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Table, Tag } from 'antd';
import { DollarSign } from 'lucide-react';
import { CONTRACT_STATUS, CHART_COLORS } from '@/lib/constants/contractManagement';

const PaymentTracker = ({ contracts = [], loading = false }) => {
  const stats = useMemo(() => {
    const total = contracts.reduce((acc, c) => acc + Number(c.value || 0), 0);
    const signed = contracts.filter((c) => c.status === 'signed').length;
    const executing = contracts.filter((c) => c.status === 'executing').length;
    return { total, signed, executing };
  }, [contracts]);

  const columns = useMemo(() => {
    return [
      {
        title: '合同',
        key: 'title',
        render: (_, record) => record.title || record.contract_no || `合同-${record.id}`
      },
      {
        title: '状态',
        key: 'status',
        render: (_, record) => {
          const statusConfig = CONTRACT_STATUS[record.status?.toUpperCase()];
          return <Tag color={statusConfig?.color}>{statusConfig?.label || record.status || '-'}</Tag>;
        }
      },
      {
        title: '金额',
        dataIndex: 'value',
        key: 'value',
        render: (value) => <span style={{ color: CHART_COLORS.POSITIVE }}>¥{Number(value || 0).toLocaleString()}</span>
      },
      {
        title: '付款状态',
        key: 'paymentStatus',
        render: () => <Tag color={CHART_COLORS.WARNING}>未接入</Tag>
      }
    ];
  }, []);

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic
              title="合同总金额"
              value={stats.total}
              prefix={<DollarSign size={16} />}
              styles={{ content: { color: CHART_COLORS.POSITIVE } }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic title="已签署合同数" value={stats.signed} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic title="执行中合同数" value={stats.executing} />
          </Card>
        </Col>
      </Row>

      <Card title="付款明细" loading={loading}>
        <Table rowKey="id" dataSource={contracts} columns={columns} pagination={false} />
      </Card>
    </div>
  );
};

export default PaymentTracker;
