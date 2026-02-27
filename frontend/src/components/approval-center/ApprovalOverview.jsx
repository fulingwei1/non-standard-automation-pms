/**
 * Approval Overview Component
 * 审批概览组件
 */

import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, List, Avatar, Badge, Timeline, Button } from 'antd';
import {
  ClipboardCheck,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Users,
  FileText,
  Calendar,
  MessageSquare } from
'lucide-react';
import { Alert } from "../ui";
import {
  APPROVAL_TYPES,
  APPROVAL_STATUS,
  APPROVAL_PRIORITY,
  WORKFLOW_STEPS,
  CHART_COLORS
} from
'@/lib/constants/approval';

const ApprovalOverview = ({ data, loading, onNavigate }) => {
  const [_selectedPeriod, _setSelectedPeriod] = useState('week');

  const overviewStats = useMemo(() => {
    if (!data?.approvals) {return {};}

    const totalApprovals = data.approvals.length;
    const pendingApprovals = data.approvals.filter((a) => a.status === 'pending').length;
    const approvedApprovals = data.approvals.filter((a) => a.status === 'approved').length;
    const rejectedApprovals = data.approvals.filter((a) => a.status === 'rejected').length;
    const urgentApprovals = data.approvals.filter((a) => a.priority === 'urgent' && a.status === 'pending').length;

    const approvalRate = totalApprovals > 0 ? (approvedApprovals / totalApprovals * 100).toFixed(1) : 0;
    const avgProcessingTime = data.metrics?.avgProcessingTime || 48;

    const weeklyTrend = data.trend || { direction: 'up', percentage: 8.5 };

    return {
      totalApprovals,
      pendingApprovals,
      approvedApprovals,
      rejectedApprovals,
      urgentApprovals,
      approvalRate,
      avgProcessingTime,
      weeklyTrend
    };
  }, [data]);

  const typeDistribution = useMemo(() => {
    if (!data?.approvals) {return {};}

    const distribution = {};
    Object.keys(APPROVAL_TYPES).forEach((key) => {
      distribution[key] = 0;
    });

    data.approvals.forEach((approval) => {
      if (approval.type && APPROVAL_TYPES[approval.type.toUpperCase()]) {
        distribution[approval.type.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const priorityDistribution = useMemo(() => {
    if (!data?.approvals) {return {};}

    const distribution = {};
    Object.keys(APPROVAL_PRIORITY).forEach((key) => {
      distribution[key] = 0;
    });

    data.approvals.forEach((approval) => {
      if (approval.priority && APPROVAL_PRIORITY[approval.priority.toUpperCase()]) {
        distribution[approval.priority.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const myPendingApprovals = useMemo(() => {
    if (!data?.approvals) {return [];}

    return data.approvals.
    filter((approval) =>
    approval.status === 'pending' &&
    approval.assignee === '当前用户' // 模拟当前用户
    ).
    sort((a, b) => {
      // 优先级排序
      const priorityWeight = APPROVAL_PRIORITY[a.priority?.toUpperCase()]?.weight || 0;
      const bPriorityWeight = APPROVAL_PRIORITY[b.priority?.toUpperCase()]?.weight || 0;
      if (priorityWeight !== bPriorityWeight) {
        return bPriorityWeight - priorityWeight;
      }
      // 时间排序
      return new Date(b.createdAt) - new Date(a.createdAt);
    }).
    slice(0, 5);
  }, [data]);

  const recentApprovals = useMemo(() => {
    if (!data?.approvals) {return [];}

    return data.approvals.
    sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)).
    slice(0, 8);
  }, [data]);

  const renderTypeCard = (typeKey, count) => {
    const config = APPROVAL_TYPES[typeKey];
    const total = data?.approvals?.length || 0;
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

  const renderPriorityCard = (priorityKey, count) => {
    const config = APPROVAL_PRIORITY[priorityKey];
    const total = data?.approvals?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={priorityKey} size="small" className="priority-card">
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

  const renderApprovalItem = (approval) => {
    const typeConfig = APPROVAL_TYPES[approval.type?.toUpperCase()];
    const statusConfig = APPROVAL_STATUS[approval.status?.toUpperCase()];
    const priorityConfig = APPROVAL_PRIORITY[approval.priority?.toUpperCase()];

    return (
      <List.Item
        key={approval.id}
        actions={[
        <Button key="view" type="link" size="small">
            查看
        </Button>]
        }>

        <List.Item.Meta
          avatar={
          <Avatar
            icon={<FileText />}
            style={{ backgroundColor: typeConfig?.color }} />

          }
          title={
          <div>
              <span>{approval.title}</span>
              <Tag color={priorityConfig?.color} size="small" style={{ marginLeft: 8 }}>
                {priorityConfig?.label}
              </Tag>
              <Tag color={statusConfig?.color} size="small" style={{ marginLeft: 4 }}>
                {statusConfig?.label}
              </Tag>
          </div>
          }
          description={
          <div>
              <div style={{ fontSize: 12, color: '#666' }}>
                {typeConfig?.icon} {typeConfig?.label} · ¥{approval.amount?.toLocaleString()}
              </div>
              <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                <Users size={10} /> {approval.initiator} · <Calendar size={10} /> {approval.createdAt}
              </div>
          </div>
          } />

      </List.Item>);

  };

  return (
    <div className="approval-overview">
      {/* 关键指标 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="待审批"
              value={overviewStats.pendingApprovals}
              prefix={<Clock />}
              suffix={`/ ${overviewStats.totalApprovals}`}
              styles={{ content: { color: CHART_COLORS.WARNING } }}
              trend={overviewStats.weeklyTrend.percentage} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="已通过"
              value={overviewStats.approvedApprovals}
              prefix={<CheckCircle />}
              styles={{ content: { color: CHART_COLORS.SUCCESS } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="通过率"
              value={overviewStats.approvalRate}
              suffix="%"
              prefix={<TrendingUp />}
              styles={{ content: { color: CHART_COLORS.PRIMARY } }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="平均处理时间"
              value={overviewStats.avgProcessingTime}
              suffix="小时"
              prefix={<MessageSquare />}
              styles={{ content: { color: CHART_COLORS.PURPLE } }} />

          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 审批类型分布 */}
        <Col xs={24} lg={12}>
          <Card title="审批类型分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(typeDistribution).map(([type, count]) =>
              renderTypeCard(type, count)
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
        {/* 我的待审批 */}
        <Col xs={24} lg={12}>
          <Card
            title="我的待审批"
            loading={loading}
            extra={
            <Badge count={overviewStats.urgentApprovals} style={{ backgroundColor: '#ff4d4f' }}>
                <Button type="link" onClick={() => onNavigate && onNavigate('my-approvals')}>
                  查看全部
                </Button>
            </Badge>
            }>

            <List
              dataSource={myPendingApprovals}
              renderItem={renderApprovalItem}
              size="small" />

          </Card>
        </Col>
        
        {/* 最近审批记录 */}
        <Col xs={24} lg={12}>
          <Card
            title="最近审批记录"
            loading={loading}
            extra={
            <Button type="link" onClick={() => onNavigate && onNavigate('recent-approvals')}>
                查看更多
            </Button>
            }>

            <Timeline
              items={recentApprovals.slice(0, 6).map((approval) => {
                const statusConfig = APPROVAL_STATUS[approval.status?.toUpperCase()];
                return {
                  key: approval.id,
                  color: statusConfig?.color,
                  dot: approval.status === 'approved' ? <CheckCircle /> :
                  approval.status === 'rejected' ? <XCircle /> : <Clock />,
                  children:
                  <div>
                      <div style={{ fontWeight: 'bold' }}>{approval.title}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {approval.initiator} · {approval.updatedAt}
                      </div>
                      <Tag size="small" color={statusConfig?.color} style={{ marginTop: 4 }}>
                        {statusConfig?.label}
                      </Tag>
                  </div>

                };
              })} />

          </Card>
        </Col>
      </Row>

      {/* 紧急提醒 */}
      {overviewStats.urgentApprovals > 0 &&
      <Card className="mt-4" loading={loading}>
          <Alert
          message={`您有 ${overviewStats.urgentApprovals} 个紧急审批待处理`}
          description="请及时处理紧急审批事项，避免影响业务进展"
          type="warning"
          showIcon
          action={
          <Button size="small" onClick={() => onNavigate && onNavigate('urgent-approvals')}>
                立即处理
          </Button>
          } />

      </Card>
      }
    </div>);

};

export default ApprovalOverview;