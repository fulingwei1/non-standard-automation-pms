/**
 * Customer Satisfaction Component
 * 客户满意度组件（占位实现，保证页面可运行）
 */

import { useMemo } from 'react';
import { Card, Table, Rate, Tag, Typography } from 'antd';
import { TABLE_CONFIG } from '@/lib/constants/customer360';

const { Text } = Typography;

const SATISFACTION_TYPE_LABELS = {
  project_completion: '项目验收',
  service_feedback: '服务反馈',
  periodic_review: '周期回访'
};

const CustomerSatisfaction = ({ satisfactions = [], loading = false }) => {
  const columns = useMemo(() => {
    return [
      { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type',
        width: 140,
        render: (type) => <Tag>{SATISFACTION_TYPE_LABELS[type] || type || '-'}</Tag>
      },
      {
        title: '评分',
        dataIndex: 'score',
        key: 'score',
        width: 200,
        render: (score) => (
          <span>
            <Rate allowHalf disabled value={Number(score || 0)} />
            <Text type="secondary" style={{ marginLeft: 8 }}>
              {Number(score || 0).toFixed(1)}
            </Text>
          </span>
        )
      },
      { title: '反馈', dataIndex: 'feedback', key: 'feedback', ellipsis: true },
      { title: '改进建议', dataIndex: 'improvements', key: 'improvements', ellipsis: true }
    ];
  }, []);

  return (
    <Card title="满意度记录" loading={loading}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={satisfactions}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default CustomerSatisfaction;

