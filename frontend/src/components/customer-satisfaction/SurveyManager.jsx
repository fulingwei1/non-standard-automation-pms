/**
 * Survey Manager Component
 * 调查管理组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag, Space, Button, Progress, Typography } from 'antd';
import { SURVEY_STATUS, SURVEY_TYPES, TABLE_CONFIG, CHART_COLORS } from './customerSatisfactionConstants';

const { Text } = Typography;

const SurveyManager = ({ surveys = [], loading = false, onCreate, onEdit, onDelete }) => {
  const columns = useMemo(() => {
    return [
      {
        title: '调查',
        key: 'title',
        render: (_, record) => (
          <div>
            <div style={{ fontWeight: 600 }}>{record.title}</div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {SURVEY_TYPES[record.type?.toUpperCase()]?.label || record.type || '-'} · {record.createdDate || '-'}
            </Text>
          </div>
        )
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        width: 120,
        render: (status) => {
          const config = SURVEY_STATUS[status?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || status || '-'}</Tag>;
        }
      },
      {
        title: '平均评分',
        dataIndex: 'avgScore',
        key: 'avgScore',
        width: 120,
        render: (score) => <Text>{score ?? '-'} / 5.0</Text>
      },
      {
        title: '完成率',
        key: 'completion',
        width: 180,
        render: (_, record) => {
          const percent = record.targetCount ? (record.responseCount / record.targetCount) * 100 : 0;
          return <Progress percent={Number(percent.toFixed(1))} size="small" strokeColor={CHART_COLORS.PRIMARY} />;
        }
      },
      {
        title: '操作',
        key: 'actions',
        width: 220,
        render: (_, record) => (
          <Space>
            <Button type="link" onClick={() => onEdit?.(record)}>
              编辑
            </Button>
            <Button type="link" danger onClick={() => onDelete?.(record.id)}>
              删除
            </Button>
          </Space>
        )
      }
    ];
  }, [onDelete, onEdit]);

  return (
    <Card
      title="调查管理"
      extra={
        <Button type="primary" onClick={() => onCreate?.()} disabled={loading}>
          新建调查
        </Button>
      }
    >
      <Table
        rowKey="id"
        columns={columns}
        dataSource={surveys}
        loading={loading}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default SurveyManager;

