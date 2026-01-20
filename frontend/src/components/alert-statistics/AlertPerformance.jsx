/**
 * Alert Performance Component
 * 告警性能分析组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Typography } from 'antd';
import { STATISTICS_METRICS, CHART_COLORS } from './alertStatisticsConstants';

const { Text } = Typography;

const AlertPerformance = ({ data, loading = false }) => {
  const metrics = useMemo(() => {
    return {
      avgResolutionTime: Number(data?.metrics?.avgResolutionTime ?? 0),
      escalationRate: Number(data?.metrics?.escalationRate ?? 0),
      falsePositiveRate: Number(data?.metrics?.falsePositiveRate ?? 0)
    };
  }, [data]);

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic
              title={STATISTICS_METRICS.AVG_RESOLUTION_TIME.label}
              value={metrics.avgResolutionTime}
              suffix={STATISTICS_METRICS.AVG_RESOLUTION_TIME.unit}
              valueStyle={{ color: CHART_COLORS.PRIMARY }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic
              title={STATISTICS_METRICS.ESCALATION_RATE.label}
              value={metrics.escalationRate}
              suffix={STATISTICS_METRICS.ESCALATION_RATE.unit}
              precision={1}
              valueStyle={{ color: CHART_COLORS.WARNING }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic
              title={STATISTICS_METRICS.FALSE_POSITIVE_RATE.label}
              value={metrics.falsePositiveRate}
              suffix={STATISTICS_METRICS.FALSE_POSITIVE_RATE.unit}
              precision={1}
              valueStyle={{ color: CHART_COLORS.ERROR }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="升级率" loading={loading}>
            <Text type="secondary">告警升级/转派趋势</Text>
            <Progress percent={metrics.escalationRate} strokeColor={CHART_COLORS.WARNING} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="误报率" loading={loading}>
            <Text type="secondary">误报/噪声告警比例</Text>
            <Progress percent={metrics.falsePositiveRate} strokeColor={CHART_COLORS.ERROR} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AlertPerformance;

