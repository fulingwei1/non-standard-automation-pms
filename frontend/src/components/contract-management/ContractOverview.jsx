/**
 * Contract Overview Component
 * 合同概览组件
 */

import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, Timeline, Alert, Button } from 'antd';
import {
  FileCheck,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Users,
  Calendar } from
'lucide-react';
import {
  CONTRACT_STATUS,
  SIGNATURE_STATUS,
  RISK_LEVELS,
  CHART_COLORS } from
'./contractManagementConstants';

const ContractOverview = ({ data, loading, onNavigate }) => {
  const [_selectedPeriod, _setSelectedPeriod] = useState('month');

  const overviewStats = useMemo(() => {
    if (!data?.contracts) {return {};}

    const totalContracts = data.contracts.length;
    const activeContracts = data.contracts.filter((c) =>
    ['signed', 'executing'].includes(c.status)
    ).length;
    const totalValue = data.contracts.reduce((acc, c) => acc + (c.value || 0), 0);
    const pendingSignatures = data.contracts.filter((c) =>
    c.signatureStatus === 'pending'
    ).length;

    const monthlyGrowth = data.monthlyStats?.growth || 8.5;
    const completionRate = data.contracts.filter((c) => c.status === 'completed').length / totalContracts * 100 || 0;

    return {
      totalContracts,
      activeContracts,
      totalValue,
      pendingSignatures,
      monthlyGrowth,
      completionRate: completionRate.toFixed(1)
    };
  }, [data]);

  const statusDistribution = useMemo(() => {
    if (!data?.contracts) {return {};}

    const distribution = {};
    Object.keys(CONTRACT_STATUS).forEach((key) => {
      distribution[key] = 0;
    });

    data.contracts.forEach((contract) => {
      if (contract.status && CONTRACT_STATUS[contract.status.toUpperCase()]) {
        distribution[contract.status.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const upcomingDeadlines = useMemo(() => {
    if (!data?.contracts) {return [];}

    return data.contracts.
    filter((c) => {
      const today = new Date();
      const deadline = new Date(c.signingDeadline || c.expiryDate);
      const daysUntil = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
      return daysUntil >= 0 && daysUntil <= 30;
    }).
    sort((a, b) => new Date(a.signingDeadline || a.expiryDate) - new Date(b.signingDeadline || b.expiryDate)).
    slice(0, 5);
  }, [data]);

  const renderStatusCard = (statusKey, count) => {
    const config = CONTRACT_STATUS[statusKey];
    const total = data?.contracts?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={statusKey} size="small" className="status-card">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 16, marginBottom: 4 }}>{config.icon || '📄'}</div>
          <div style={{ color: config.color, fontWeight: 'bold', fontSize: 14 }}>
            {count}
          </div>
          <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>
            {config.label}
          </div>
          <Progress
            percent={percentage}
            strokeColor={config.color}
            showInfo={false}
            size="small" />

        </div>
      </Card>);

  };

  const renderDeadlineItem = (contract) => {
    const today = new Date();
    const deadline = new Date(contract.signingDeadline || contract.expiryDate);
    const daysUntil = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));

    const urgency = daysUntil <= 3 ? 'critical' : daysUntil <= 7 ? 'warning' : 'normal';
    const urgencyConfig = {
      critical: { color: '#ff4d4f', text: '紧急' },
      warning: { color: '#faad14', text: '警告' },
      normal: { color: '#1890ff', text: '提醒' }
    }[urgency];

    return (
      <Timeline.Item
        key={contract.id}
        color={urgencyConfig.color}
        dot={urgency === 'critical' ? <AlertTriangle /> : <Clock />}>

        <div>
          <div style={{ fontWeight: 'bold' }}>{contract.title}</div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {contract.signingDeadline ? '签署期限' : '到期日期'}: {contract.signingDeadline || contract.expiryDate}
          </div>
          <Tag size="small" color={urgencyConfig.color}>
            {urgencyConfig.text} ({daysUntil}天)
          </Tag>
        </div>
      </Timeline.Item>);

  };

  return (
    <div className="contract-overview">
      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="合同总数"
              value={overviewStats.totalContracts}
              prefix={<FileCheck />}
              suffix={`(${overviewStats.activeContracts} 执行中)`}
              valueStyle={{ color: CHART_COLORS.PRIMARY }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="合同总价值"
              value={overviewStats.totalValue}
              prefix={<DollarSign />}
              precision={2}
              valueStyle={{ color: CHART_COLORS.POSITIVE }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="待签署"
              value={overviewStats.pendingSignatures}
              prefix={<Users />}
              valueStyle={{ color: CHART_COLORS.WARNING }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="完成率"
              value={overviewStats.completionRate}
              suffix="%"
              prefix={<CheckCircle2 />}
              valueStyle={{ color: CHART_COLORS.SECONDARY }}
              trend={overviewStats.monthlyGrowth} />

          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 合同状态分布 */}
        <Col xs={24} lg={12}>
          <Card title="合同状态分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(statusDistribution).map(([status, count]) =>
              renderStatusCard(status, count)
              )}
            </Row>
          </Card>
        </Col>

        {/* 即将到期提醒 */}
        <Col xs={24} lg={12}>
          <Card
            title="即将到期/签署"
            loading={loading}
            extra={
            <span style={{ fontSize: 12, color: '#666' }}>
                未来30天内
            </span>
            }>

            {upcomingDeadlines.length > 0 ?
            <Timeline>
                {upcomingDeadlines.map(renderDeadlineItem)}
            </Timeline> :

            <Alert
              message="暂无即将到期的合同"
              type="success"
              showIcon />

            }
          </Card>
        </Col>
      </Row>

      {/* 风险提醒 */}
      {data?.riskContracts?.length > 0 &&
      <Card
        title="风险提醒"
        className="mt-4"
        loading={loading}>

          <Alert
          message={`发现 ${data.riskContracts.length} 个高风险合同需要关注`}
          description="建议及时处理高风险合同，避免潜在损失"
          type="warning"
          showIcon
          action={
          <Button
            size="small"
            onClick={() => onNavigate && onNavigate('risks')}>

                查看详情
          </Button>
          } />

      </Card>
      }
    </div>);

};

export default ContractOverview;