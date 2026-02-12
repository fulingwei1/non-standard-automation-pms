/**
 * Customer Analytics Component
 * 客户分析组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Typography } from 'antd';
import { CHART_COLORS } from '@/lib/constants/customer360';

const { Text } = Typography;

const CustomerAnalytics = ({ customer, loading = false }) => {
  const stats = useMemo(() => {
    if (!customer) {return null;}

    return {
      lifetimeValue: Number(customer.lifetimeValue || 0),
      orderCount: Number(customer.orderCount || 0),
      avgOrderValue: Number(customer.avgOrderValue || 0),
      growthTrend: Number(customer.growthTrend || 0),
      loyaltyIndex: Number(customer.loyaltyIndex || 0),
      projectSuccessRate: Number(customer.projectSuccessRate || 0)
    };
  }, [customer]);

  if (!customer) {return null;}

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic
              title="客户终身价值"
              value={stats?.lifetimeValue}
              valueStyle={{ color: CHART_COLORS.PRIMARY }}
              prefix="¥"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic title="历史订单数" value={stats?.orderCount} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card loading={loading}>
            <Statistic
              title="平均订单金额"
              value={stats?.avgOrderValue}
              valueStyle={{ color: CHART_COLORS.PURPLE }}
              prefix="¥"
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="增长趋势" loading={loading}>
            <Text type="secondary">近期开票/订单增长</Text>
            <Progress percent={stats?.growthTrend || 0} strokeColor={CHART_COLORS.SUCCESS} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="忠诚度与项目成功率" loading={loading}>
            <div style={{ marginBottom: 12 }}>
              <Text type="secondary">忠诚度指数</Text>
              <Progress percent={stats?.loyaltyIndex || 0} strokeColor={CHART_COLORS.PURPLE} />
            </div>
            <div>
              <Text type="secondary">项目成功率</Text>
              <Progress percent={stats?.projectSuccessRate || 0} strokeColor={CHART_COLORS.CYAN} />
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default CustomerAnalytics;

