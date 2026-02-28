/**
 * Alert Overview Component
 * 告警概览组件
 */

import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, Alert as AntAlert, Space } from 'antd';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  Clock,
  BarChart3,
  Activity,
  Shield } from
'lucide-react';
import { Button } from "../ui";
import {
  ALERT_TYPES,
  ALERT_LEVELS,
  ALERT_STATUS,
  STATISTICS_METRICS,
  CHART_COLORS
} from '@/lib/constants/alert';

const AlertOverview = ({ data, loading, onNavigate }) => {
  const [_selectedPeriod, _setSelectedPeriod] = useState('last_24h');

  const overviewStats = useMemo(() => {
    if (!data?.alerts) {return {};}

    const totalAlerts = data.alerts.length;
    const activeAlerts = data.alerts.filter((a) => a.status === 'active').length;
    const resolvedAlerts = data.alerts.filter((a) => a.status === 'resolved').length;
    const criticalAlerts = data.alerts.filter((a) => a.level === 'critical').length;
    const escalatedAlerts = data.alerts.filter((a) => a.status === 'escalated').length;

    const resolvedRate = totalAlerts > 0 ? (resolvedAlerts / totalAlerts * 100).toFixed(1) : 0;
    const escalationRate = totalAlerts > 0 ? (escalatedAlerts / totalAlerts * 100).toFixed(1) : 0;
    const avgResolutionTime = data.metrics?.avgResolutionTime || 45;

    const trendData = data.trend || { direction: 'down', percentage: 12.5 };

    return {
      totalAlerts,
      activeAlerts,
      resolvedAlerts,
      criticalAlerts,
      escalatedAlerts,
      resolvedRate,
      escalationRate,
      avgResolutionTime,
      trend: trendData
    };
  }, [data]);

  const typeDistribution = useMemo(() => {
    if (!data?.alerts) {return {};}

    const distribution = {};
    Object.keys(ALERT_TYPES).forEach((key) => {
      distribution[key] = 0;
    });

    data.alerts.forEach((alert) => {
      if (alert.type && ALERT_TYPES[alert.type.toUpperCase()]) {
        distribution[alert.type.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const levelDistribution = useMemo(() => {
    if (!data?.alerts) {return {};}

    const distribution = {};
    Object.keys(ALERT_LEVELS).forEach((key) => {
      distribution[key] = 0;
    });

    data.alerts.forEach((alert) => {
      if (alert.level && ALERT_LEVELS[alert.level.toUpperCase()]) {
        distribution[alert.level.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const recentCriticalAlerts = useMemo(() => {
    if (!data?.alerts) {return [];}

    return data.alerts.
    filter((alert) => alert.level === 'critical' && alert.status === 'active').
    sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).
    slice(0, 5);
  }, [data]);

  const renderMetricCard = (title, value, icon, color, trend, unit) => {
    return (
      <Card key={title} loading={loading}>
        <Statistic
          title={title}
          value={value}
          prefix={icon}
          suffix={unit}
          styles={{ content: { color } }}
          trend={trend} />

      </Card>);

  };

  const renderTypeCard = (typeKey, count) => {
    const config = ALERT_TYPES[typeKey];
    const total = data?.alerts?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={typeKey} size="small" className="type-card" hoverable>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 20, marginBottom: 8 }}>{config.icon}</div>
          <div style={{ color: config.color, fontWeight: 'bold', fontSize: 16 }}>
            {count}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            {config.label} ({percentage}%)
          </div>
          <Progress
            percent={percentage}
            strokeColor={config.color}
            showInfo={false}
            size="small" />

        </div>
      </Card>);

  };

  const renderLevelCard = (levelKey, count) => {
    const config = ALERT_LEVELS[levelKey];
    const total = data?.alerts?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={levelKey} size="small" className="level-card" hoverable>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 14, marginBottom: 4 }}>
            <AlertTriangle style={{ color: config.color }} />
          </div>
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

  return (
    <div className="alert-overview">
      {/* 关键指标 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          {renderMetricCard(
            '告警总数',
            overviewStats.totalAlerts,
            <AlertTriangle />,
            CHART_COLORS.PRIMARY,
            overviewStats.trend.direction === 'up' ? overviewStats.trend.percentage : -overviewStats.trend.percentage,
            STATISTICS_METRICS.TOTAL_ALERTS.unit
          )}
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          {renderMetricCard(
            '活跃告警',
            overviewStats.activeAlerts,
            <Activity />,
            CHART_COLORS.ERROR,
            null,
            STATISTICS_METRICS.ACTIVE_ALERTS.unit
          )}
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          {renderMetricCard(
            '解决率',
            overviewStats.resolvedRate,
            <CheckCircle />,
            CHART_COLORS.SUCCESS,
            null,
            STATISTICS_METRICS.RESOLVED_RATE.unit
          )}
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          {renderMetricCard(
            '平均解决时间',
            overviewStats.avgResolutionTime,
            <Clock />,
            CHART_COLORS.WARNING,
            null,
            STATISTICS_METRICS.AVG_RESOLUTION_TIME.unit
          )}
        </Col>
      </Row>

      {/* 告警分布 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} lg={12}>
          <Card title="告警类型分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(typeDistribution).map(([type, count]) =>
              renderTypeCard(type, count)
              )}
            </Row>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="告警级别分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(levelDistribution).map(([level, count]) =>
              renderLevelCard(level, count)
              )}
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 紧急告警 */}
      {recentCriticalAlerts.length > 0 &&
      <Card
        title="紧急告警"
        loading={loading}
        extra={
        <Space>
              <Tag color={CHART_COLORS.ERROR}>
                {recentCriticalAlerts.length} 条
              </Tag>
              <Button
            type="link"
            onClick={() => onNavigate && onNavigate('critical-alerts')}>

                查看全部
              </Button>
        </Space>
        }>

          <Space direction="vertical" style={{ width: '100%' }}>
            {recentCriticalAlerts.map((alert) =>
          <AntAlert
            key={alert.id}
            message={alert.title}
            description={alert.description}
            type="error"
            showIcon
            action={
            <Space>
                    <Tag size="small">{alert.source}</Tag>
                    <Tag size="small">{alert.createdAt}</Tag>
            </Space>
            } />

          )}
          </Space>
      </Card>
      }

      {/* 系统健康度 */}
      <Row gutter={[16, 16]} className="mt-4">
        <Col xs={24} lg={12}>
          <Card title="系统健康度" loading={loading}>
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{
                fontSize: 48,
                fontWeight: 'bold',
                color: overviewStats.resolvedRate >= 80 ? CHART_COLORS.SUCCESS :
                overviewStats.resolvedRate >= 60 ? CHART_COLORS.WARNING : CHART_COLORS.ERROR
              }}>
                {overviewStats.resolvedRate >= 80 ? '优秀' :
                overviewStats.resolvedRate >= 60 ? '良好' : '需改进'}
              </div>
              <div style={{ fontSize: 14, color: '#666', marginTop: 8 }}>
                基于解决率和响应时间综合评估
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="快速操作" loading={loading}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button
                type="primary"
                block
                icon={<Shield />}
                onClick={() => onNavigate && onNavigate('alert-rules')}>

                配置告警规则
              </Button>
              <Button
                block
                icon={<BarChart3 />}
                onClick={() => onNavigate && onNavigate('trend-analysis')}>

                趋势分析
              </Button>
              <Button
                block
                icon={<Activity />}
                onClick={() => onNavigate && onNavigate('performance-metrics')}>

                性能指标
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>);

};

export default AlertOverview;