/**
 * Customer Project Delivery Component
 * 客户项目交付组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag, Progress } from 'antd';
import { PROJECT_PHASES, TABLE_CONFIG } from './customer360Constants';

const CustomerProjectDelivery = ({ projects = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '项目ID', dataIndex: 'id', key: 'id', width: 160 },
      { title: '项目名称', dataIndex: 'name', key: 'name', ellipsis: true },
      {
        title: '阶段',
        dataIndex: 'phase',
        key: 'phase',
        width: 120,
        render: (phase) => {
          const config = PROJECT_PHASES[phase?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || phase || '-'}</Tag>;
        }
      },
      { title: '开始日期', dataIndex: 'startDate', key: 'startDate', width: 120 },
      { title: '预计完成', dataIndex: 'expectedDate', key: 'expectedDate', width: 120 },
      {
        title: '进度',
        dataIndex: 'progress',
        key: 'progress',
        width: 200,
        render: (progress) => <Progress percent={Number(progress || 0)} size="small" />
      }
    ];
  }, []);

  return (
    <Card title="项目交付" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={projects}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default CustomerProjectDelivery;

