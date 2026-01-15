/**
 * Customer Service Records Component
 * 客户服务记录组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Rate, Tag, Typography } from 'antd';
import { TABLE_CONFIG } from './customer360Constants';

const { Text } = Typography;

const CustomerServiceRecords = ({ services = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
      { title: '类型', dataIndex: 'type', key: 'type', width: 160, render: (type) => <Tag>{type || '-'}</Tag> },
      { title: '问题', dataIndex: 'issue', key: 'issue', ellipsis: true },
      { title: '解决方案', dataIndex: 'resolution', key: 'resolution', ellipsis: true },
      {
        title: '满意度',
        dataIndex: 'satisfaction',
        key: 'satisfaction',
        width: 200,
        render: (score) =>
          score == null ? (
            <Text type="secondary">-</Text>
          ) : (
            <span>
              <Rate allowHalf disabled value={Number(score || 0)} />
              <Text type="secondary" style={{ marginLeft: 8 }}>
                {Number(score || 0).toFixed(1)}
              </Text>
            </span>
          )
      },
      {
        title: '响应时间(小时)',
        dataIndex: 'responseTime',
        key: 'responseTime',
        width: 140,
        render: (rt) => <Text type="secondary">{rt ?? '-'}</Text>
      }
    ];
  }, []);

  return (
    <Card title="服务记录" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={services}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default CustomerServiceRecords;

