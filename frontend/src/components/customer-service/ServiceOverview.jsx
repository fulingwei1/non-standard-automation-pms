/**
 * Service Overview Component
 * 客服概览组件
 */

import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, List, Timeline, Alert, Rate } from 'antd';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Users,
  Wrench,
  Phone,
  Star,
  Trophy,
  AlertTriangle,
  Calendar,
  MessageSquare } from
'lucide-react';
import { Button } from "../ui";
import {
  TICKET_STATUS,
  PRIORITY_LEVELS,
  SERVICE_TYPES,
  SATISFACTION_LEVELS,
  PERFORMANCE_METRICS,
  CHART_COLORS
} from '../../lib/constants/service';

const ServiceOverview = ({ data, loading, onNavigate }) => {
  const [_selectedPeriod, _setSelectedPeriod] = useState('today');

  const overviewStats = useMemo(() => {
    if (!data?.tickets) {return {};}

    const totalTickets = data.tickets?.length;
    const openTickets = (data.tickets || []).filter((t) => ['open', 'in_progress'].includes(t.status)).length;
    const resolvedToday = (data.tickets || []).filter((t) =>
    t.status === 'resolved' && t.resolvedDate === new Date().toISOString().split('T')[0]
    ).length;

    const avgResponseTime = data.metrics?.avgResponseTime || 2.5;
    const avgSatisfaction = data.metrics?.avgSatisfaction || 4.2;
    const slaAchievement = data.metrics?.slaAchievement || 94.5;

    return {
      totalTickets,
      openTickets,
      resolvedToday,
      avgResponseTime,
      avgSatisfaction,
      slaAchievement
    };
  }, [data]);

  const statusDistribution = useMemo(() => {
    if (!data?.tickets) {return {};}

    const distribution = {};
    Object.keys(TICKET_STATUS).forEach((key) => {
      distribution[key] = 0;
    });

    (data.tickets || []).forEach((ticket) => {
      if (ticket.status && TICKET_STATUS[ticket.status.toUpperCase()]) {
        distribution[ticket.status.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const priorityDistribution = useMemo(() => {
    if (!data?.tickets) {return {};}

    const distribution = {};
    Object.keys(PRIORITY_LEVELS).forEach((key) => {
      distribution[key] = 0;
    });

    (data.tickets || []).forEach((ticket) => {
      if (ticket.priority && PRIORITY_LEVELS[ticket.priority.toUpperCase()]) {
        distribution[ticket.priority.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const urgentTickets = useMemo(() => {
    if (!data?.tickets) {return [];}

    return data.tickets.
    filter((ticket) => ticket.priority === 'critical' && ['open', 'in_progress'].includes(ticket.status)).
    sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt)).
    slice(0, 5);
  }, [data]);

  const recentActivities = useMemo(() => {
    if (!data?.activities) {return [];}

    return data.activities.
    sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).
    slice(0, 8);
  }, [data]);

  const renderStatusCard = (statusKey, count) => {
    const config = TICKET_STATUS[statusKey];
    const total = data?.tickets?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={statusKey} size="small" className="status-card">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 14, marginBottom: 4 }}>{config.icon || '📋'}</div>
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

  const renderPriorityCard = (priorityKey, count) => {
    const config = PRIORITY_LEVELS[priorityKey];
    const total = data?.tickets?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={priorityKey} size="small" className="priority-card">
        <div style={{ textAlign: 'center' }}>
          <AlertCircle
            style={{
              color: config.color,
              fontSize: 16,
              marginBottom: 4
            }} />

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

  const getMetricColor = (value, target) => {
    if (value >= target) {return CHART_COLORS.POSITIVE;}
    if (value >= target * 0.8) {return CHART_COLORS.WARNING;}
    return CHART_COLORS.NEGATIVE;
  };

  const renderUrgentTicket = (ticket) => {
    const priorityConfig = PRIORITY_LEVELS[ticket.priority?.toUpperCase()];

    return (
      <List.Item key={ticket.id}>
        <List.Item.Meta
          avatar={<AlertCircle size={20} style={{ color: priorityConfig?.color }} />}
          title={
          <div>
              <span style={{ fontWeight: 'bold' }}>{ticket.title}</span>
              <Tag color={priorityConfig?.color} size="small" style={{ marginLeft: 8 }}>
                {priorityConfig?.label}
              </Tag>
          </div>
          }
          description={
          <div>
              <div>{ticket.customerName} · {ticket.description?.substring(0, 50)}...</div>
              <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                <Clock size={10} /> 创建: {ticket.createdAt} · 期望响应: {priorityConfig?.responseTime}
              </div>
          </div>
          } />

      </List.Item>);

  };

  const renderActivity = (activity) => {
    return (
      <Timeline.Item key={activity.id} color={activity.type === 'resolved' ? '#52c41a' : '#1890ff'}>
        <div>
          <div style={{ fontWeight: 'bold' }}>{activity.title}</div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {activity.description}
          </div>
          <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
            {activity.engineer} · <Calendar size={10} /> {activity.timestamp}
          </div>
        </div>
      </Timeline.Item>);

  };

  return (
    <div className="service-overview">
      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="工单总数"
              value={overviewStats.totalTickets}
              prefix={<MessageSquare />}
              suffix={`(${overviewStats.openTickets} 待处理)`}
              styles={{ content: { color: CHART_COLORS.PRIMARY } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="今日解决"
              value={overviewStats.resolvedToday}
              prefix={<CheckCircle2 />}
              styles={{ content: { color: CHART_COLORS.POSITIVE } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="平均响应"
              value={overviewStats.avgResponseTime}
              suffix="小时"
              prefix={<Clock />}
              styles={{ content: { color: getMetricColor(overviewStats.avgResponseTime, PERFORMANCE_METRICS.RESPONSE_TIME.target) } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="客户满意度"
              value={overviewStats.avgSatisfaction}
              suffix="/ 5.0"
              prefix={<Star />}
              styles={{ content: { color: getMetricColor(overviewStats.avgSatisfaction, PERFORMANCE_METRICS.CUSTOMER_SATISFACTION.target) } }} />

          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 工单状态分布 */}
        <Col xs={24} lg={12}>
          <Card title="工单状态分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(statusDistribution).map(([status, count]) =>
              renderStatusCard(status, count)
              )}
            </Row>
          </Card>
        </Col>

        {/* 优先级分布 */}
        <Col xs={24} lg={12}>
          <Card title="优先级分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(priorityDistribution).map(([priority, count]) =>
              renderPriorityCard(priority, count)
              )}
            </Row>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mt-4">
        {/* 紧急工单 */}
        <Col xs={24} lg={12}>
          <Card
            title="紧急工单"
            loading={loading}
            extra={
            <Button type="link" onClick={() => onNavigate && onNavigate('urgent')}>
                查看更多
            </Button>
            }>

            <List
              dataSource={urgentTickets}
              renderItem={renderUrgentTicket}
              size="small" />

          </Card>
        </Col>

        {/* 最近活动 */}
        <Col xs={24} lg={12}>
          <Card
            title="最近活动"
            loading={loading}
            extra={
            <Button type="link" onClick={() => onNavigate && onNavigate('activities')}>
                查看更多
            </Button>
            }>

            <Timeline>
              {(recentActivities || []).map(renderActivity)}
            </Timeline>
          </Card>
        </Col>
      </Row>

      {/* 性能指标提醒 */}
      {overviewStats.slaAchievement < 95 &&
      <Card className="mt-4" loading={loading}>
          <Alert
          message={`SLA达成率 ${overviewStats.slaAchievement}% 低于目标值`}
          description="建议优化响应流程，提高服务质量"
          type="warning"
          showIcon
          action={
          <Button
            size="small"
            onClick={() => onNavigate && onNavigate('performance')}>

                查看详情
          </Button>
          } />

      </Card>
      }

      {/* 快速操作 */}
      <Card title="快速操作" className="mt-4" loading={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={6}>
            <Button
              type="primary"
              block
              icon={<Phone />}
              onClick={() => onNavigate && onNavigate('create-ticket')}>

              创建工单
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              block
              icon={<Wrench />}
              onClick={() => onNavigate && onNavigate('field-service')}>

              现场服务
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              block
              icon={<Trophy />}
              onClick={() => onNavigate && onNavigate('warranty')}>

              质保管理
            </Button>
          </Col>
          <Col xs={24} sm={6}>
            <Button
              block
              icon={<Star />}
              onClick={() => onNavigate && onNavigate('satisfaction')}>

              满意度管理
            </Button>
          </Col>
        </Row>
      </Card>
    </div>);

};

export default ServiceOverview;