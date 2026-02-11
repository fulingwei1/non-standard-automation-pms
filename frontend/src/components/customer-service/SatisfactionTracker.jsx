/**
 * Satisfaction Tracker Component
 * 满意度跟踪组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Table, Rate, Typography } from 'antd';
import { CHART_COLORS } from '../../lib/constants/service';

const { Text } = Typography;

const SatisfactionTracker = ({ tickets = [], loading = false }) => {
  const stats = useMemo(() => {
    const scored = tickets.filter((t) => t.satisfaction != null);
    const avg = scored.length > 0 ? scored.reduce((acc, t) => acc + Number(t.satisfaction || 0), 0) / scored.length : 0;
    return { scoredCount: scored.length, avg: Number(avg.toFixed(2)) };
  }, [tickets]);

  const columns = useMemo(() => {
    return [
      { title: '工单', dataIndex: 'title', key: 'title', ellipsis: true },
      { title: '客户', dataIndex: 'customerName', key: 'customerName', width: 160 },
      {
        title: '满意度',
        dataIndex: 'satisfaction',
        key: 'satisfaction',
        width: 240,
        render: (score) =>
          score == null ? (
            <Text type="secondary">未评价</Text>
          ) : (
            <span>
              <Rate allowHalf disabled value={Number(score || 0)} />
              <Text type="secondary" style={{ marginLeft: 8 }}>
                {Number(score || 0).toFixed(1)}
              </Text>
            </span>
          )
      },
      { title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt', width: 160 }
    ];
  }, []);

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic title="已评价工单" value={stats.scoredCount} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic title="平均满意度" value={stats.avg} precision={2} valueStyle={{ color: CHART_COLORS.POSITIVE }} />
          </Card>
        </Col>
      </Row>

      <Card title="满意度明细" loading={loading}>
        <Table rowKey="id" dataSource={tickets} columns={columns} pagination={false} />
      </Card>
    </div>
  );
};

export default SatisfactionTracker;

