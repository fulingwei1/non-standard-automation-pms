/**
 * Satisfaction Analytics Component
 * 满意度分析组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Typography } from 'antd';
import { CHART_COLORS, SATISFACTION_LEVELS } from './customerSatisfactionConstants';

const { Text } = Typography;

const SatisfactionAnalytics = ({ surveys = [], responses = [], loading = false }) => {
  const stats = useMemo(() => {
    const surveyCount = surveys.length;
    const responseCount = responses.length;
    const avgScore = responseCount > 0 ? responses.reduce((acc, r) => acc + Number(r.satisfactionLevel || 0), 0) / responseCount : 0;

    const dist = {};
    Object.keys(SATISFACTION_LEVELS).forEach((k) => (dist[k] = 0));
    responses.forEach((r) => {
      const hit = Object.entries(SATISFACTION_LEVELS).find(([_, cfg]) => cfg.value === r.satisfactionLevel);
      if (hit) {dist[hit[0]] += 1;}
    });

    return { surveyCount, responseCount, avgScore, dist };
  }, [responses, surveys.length]);

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic title="调查数量" value={stats.surveyCount} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic title="反馈数量" value={stats.responseCount} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic
              title="平均满意度"
              value={stats.avgScore}
              precision={2}
              suffix="/5.0"
              valueStyle={{ color: CHART_COLORS.PRIMARY }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="满意度分布" loading={loading}>
        {Object.entries(stats.dist).map(([key, count]) => {
          const cfg = SATISFACTION_LEVELS[key];
          const percent = stats.responseCount > 0 ? (count / stats.responseCount) * 100 : 0;
          return (
            <div key={key} style={{ marginBottom: 12 }}>
              <Text style={{ display: 'block', marginBottom: 4 }}>
                {cfg.icon} {cfg.label}：{count} 条
              </Text>
              <Progress percent={Number(percent.toFixed(1))} strokeColor={cfg.color} />
            </div>
          );
        })}
      </Card>
    </div>
  );
};

export default SatisfactionAnalytics;

