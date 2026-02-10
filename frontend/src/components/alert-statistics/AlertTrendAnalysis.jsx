/**
 * Alert Trend Analysis Component
 * 告警趋势分析组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag } from 'antd';
import { ALERT_LEVELS, ALERT_STATUS, CHART_COLORS } from './alertStatsConstants';

const AlertTrendAnalysis = ({ alerts = [], loading = false }) => {
  const stats = useMemo(() => {
    const total = alerts.length;
    const active = alerts.filter((a) => a.status === 'active').length;
    const resolved = alerts.filter((a) => a.status === 'resolved').length;
    const critical = alerts.filter((a) => a.level === 'critical').length;
    const resolvedRate = total > 0 ? (resolved / total) * 100 : 0;
    return { total, active, resolved, critical, resolvedRate };
  }, [alerts]);

  const recentColumns = useMemo(() => {
    return [
      { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
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
      { title: '时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 }
    ];
  }, []);

  const recentAlerts = useMemo(() => {
    return [...alerts].slice(0, 10);
  }, [alerts]);

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="告警总数" value={stats.total} valueStyle={{ color: CHART_COLORS.PRIMARY }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="活跃告警" value={stats.active} valueStyle={{ color: CHART_COLORS.ERROR }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="紧急告警" value={stats.critical} valueStyle={{ color: CHART_COLORS.CRITICAL }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic title="解决率" value={stats.resolvedRate} precision={1} suffix="%" valueStyle={{ color: CHART_COLORS.SUCCESS }} />
          </Card>
        </Col>
      </Row>

      <Card title="解决率趋势" loading={loading} style={{ marginBottom: 16 }}>
        <Progress percent={stats.resolvedRate} strokeColor={CHART_COLORS.SUCCESS} />
      </Card>

      <Card title="近期告警" loading={loading}>
        <Table rowKey="id" dataSource={recentAlerts} columns={recentColumns} pagination={false} />
      </Card>
    </div>
  );
};

export default AlertTrendAnalysis;

