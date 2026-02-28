/**
 * Ticket Manager Component
 * 工单管理组件（占位实现，保证页面可运行）
 */

import { useMemo } from 'react';
import { Card, Table, Tag, Space, Button, Typography } from 'antd';
import { SERVICE_TYPES, TICKET_STATUS, PRIORITY_LEVELS, TABLE_CONFIG } from '../../lib/constants/service';

const { Text } = Typography;

const TicketManager = ({ tickets = [], loading = false, onEdit, onResolve, onEscalate }) => {
  const columns = useMemo(() => {
    return [
      {
        title: '工单',
        key: 'title',
        render: (_, record) => (
          <div>
            <div style={{ fontWeight: 600 }}>{record.title}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.customerName || '-'} · {record.createdAt || '-'}
            </Text>
          </div>
        )
      },
      {
        title: '服务类型',
        dataIndex: 'serviceType',
        key: 'serviceType',
        width: 140,
        render: (type) => {
          const config = SERVICE_TYPES[type?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || type || '-'}</Tag>;
        }
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => {
          const config = TICKET_STATUS[status?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || status || '-'}</Tag>;
        }
      },
      {
        title: '优先级',
        dataIndex: 'priority',
        key: 'priority',
        width: 120,
        render: (priority) => {
          const config = PRIORITY_LEVELS[priority?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || priority || '-'}</Tag>;
        }
      },
      { title: '负责人', dataIndex: 'engineer', key: 'engineer', width: 120 },
      {
        title: '操作',
        key: 'actions',
        width: 220,
        render: (_, record) => (
          <Space>
            <Button type="link" onClick={() => onEdit?.(record)}>
              编辑
            </Button>
            <Button type="link" onClick={() => onResolve?.(record)}>
              解决
            </Button>
            <Button type="link" onClick={() => onEscalate?.(record)}>
              升级
            </Button>
          </Space>
        )
      }
    ];
  }, [onEdit, onEscalate, onResolve]);

  return (
    <Card title="工单列表">
      <Table
        rowKey="id"
        columns={columns}
        dataSource={tickets}
        loading={loading}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default TicketManager;

