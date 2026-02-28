/**
 * Alert Details Component
 * 告警详情组件（占位实现，保证页面可运行）
 */

import { useMemo } from 'react';
import { Card, Table, Tag, Space, Typography } from 'antd';
import { ALERT_TYPES, ALERT_LEVELS, ALERT_STATUS, TABLE_CONFIG } from '@/lib/constants/alert';

const { Text } = Typography;

const AlertDetails = ({ alerts = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      {
        title: '告警',
        key: 'title',
        render: (_, record) => (
          <div>
            <div style={{ fontWeight: 600 }}>{record.title}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.source || '-'} · {record.createdAt || '-'}
            </Text>
          </div>
        )
      },
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type',
        width: 120,
        render: (type) => {
          const config = ALERT_TYPES[type?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || type || '-'}</Tag>;
        }
      },
      {
        title: '级别',
        dataIndex: 'level',
        key: 'level',
        width: 120,
        render: (level) => {
          const config = ALERT_LEVELS[level?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || level || '-'}</Tag>;
        }
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => {
          const config = ALERT_STATUS[status?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || status || '-'}</Tag>;
        }
      },
      {
        title: '标签',
        dataIndex: 'tags',
        key: 'tags',
        width: 220,
        render: (tags) =>
          Array.isArray(tags) && tags.length > 0 ? (
            <Space wrap>
              {tags.slice(0, 3).map((t) => (
                <Tag key={t}>{t}</Tag>
              ))}
            </Space>
          ) : (
            <Text type="secondary">-</Text>
          )
      }
    ];
  }, []);

  return (
    <Card title="告警明细" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={alerts}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default AlertDetails;

