/**
 * Field Service Manager Component
 * 现场服务管理组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag, Space, Button, Typography } from 'antd';
import { SERVICE_PHASES, TABLE_CONFIG, CHART_COLORS } from '../../lib/constants/service';

const { Text } = Typography;

const FieldServiceManager = ({ services = [], loading = false, onRefresh }) => {
  const columns = useMemo(() => {
    return [
      { title: '服务ID', dataIndex: 'id', key: 'id', width: 120 },
      {
        title: '服务',
        key: 'title',
        render: (_, record) => (
          <div>
            <div style={{ fontWeight: 600 }}>{record.title}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.customerName || '-'} · {record.location || '-'}
            </Text>
          </div>
        )
      },
      {
        title: '阶段',
        dataIndex: 'servicePhase',
        key: 'servicePhase',
        width: 140,
        render: (phase) => <Tag color={CHART_COLORS.PRIMARY}>{SERVICE_PHASES[phase?.toUpperCase()]?.label || phase || '-'}</Tag>
      },
      { title: '计划日期', dataIndex: 'scheduledDate', key: 'scheduledDate', width: 120 },
      { title: '工程师', dataIndex: 'engineer', key: 'engineer', width: 120 },
      { title: '状态', dataIndex: 'status', key: 'status', width: 120 }
    ];
  }, []);

  return (
    <Card
      title="现场服务"
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
        dataSource={services}
        loading={loading}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default FieldServiceManager;

