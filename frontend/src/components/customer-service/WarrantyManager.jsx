/**
 * Warranty Manager Component
 * 质保管理组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag, Progress, Typography } from 'antd';
import { WARRANTY_TYPES, TABLE_CONFIG, CHART_COLORS } from '../../lib/constants/service';

const { Text } = Typography;

const WarrantyManager = ({ projects = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '项目', dataIndex: 'projectName', key: 'projectName', ellipsis: true },
      { title: '客户', dataIndex: 'customerName', key: 'customerName', width: 160 },
      {
        title: '质保类型',
        dataIndex: 'warrantyType',
        key: 'warrantyType',
        width: 140,
        render: (type) => <Tag color={CHART_COLORS.SECONDARY}>{WARRANTY_TYPES[type?.toUpperCase()]?.label || type || '-'}</Tag>
      },
      { title: '开始', dataIndex: 'startDate', key: 'startDate', width: 120 },
      { title: '结束', dataIndex: 'endDate', key: 'endDate', width: 120 },
      {
        title: '剩余天数',
        dataIndex: 'remainingDays',
        key: 'remainingDays',
        width: 160,
        render: (days) => {
          const percent = Math.max(0, Math.min(100, (Number(days || 0) / 365) * 100));
          return (
            <div style={{ minWidth: 140 }}>
              <Progress percent={Number(percent.toFixed(0))} size="small" strokeColor={CHART_COLORS.POSITIVE} />
              <Text type="secondary">{days ?? '-'} 天</Text>
            </div>
          );
        }
      },
      {
        title: '索赔',
        key: 'claims',
        width: 140,
        render: (_, record) => (
          <Text type="secondary">
            {record.resolvedClaims ?? 0}/{record.totalClaims ?? 0}
          </Text>
        )
      },
      { title: '状态', dataIndex: 'status', key: 'status', width: 120 }
    ];
  }, []);

  return (
    <Card title="质保项目" loading={loading}>
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

export default WarrantyManager;

