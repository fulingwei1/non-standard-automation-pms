/**
 * Lead Overview Component
 * 线索概览组件
 */

import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Tag, List, Timeline, Alert, Button, Avatar } from 'antd';
import {
  Target,
  TrendingUp,
  Users,
  Star,
  Calendar,
  Phone,
  Trophy,
  Clock } from
'lucide-react';
import {
  LEAD_SOURCES,
  LEAD_STATUS,
  QUALIFICATION_LEVELS,
  SCORE_COLORS } from
'./leadAssessmentConstants';

const LeadOverview = ({ data, loading, onNavigate }) => {
  const [_selectedPeriod, _setSelectedPeriod] = useState('month');

  const overviewStats = useMemo(() => {
    if (!data?.leads) return {};

    const totalLeads = data.leads.length;
    const qualifiedLeads = data.leads.filter((l) => l.qualification === 'qualified').length;
    const convertedLeads = data.leads.filter((l) => l.status === 'converted').length;
    const avgScore = data.leads.reduce((acc, l) => acc + (l.score || 0), 0) / totalLeads || 0;

    const monthlyGrowth = data.monthlyStats?.growth || 12.5;
    const conversionRate = totalLeads > 0 ? (convertedLeads / totalLeads * 100).toFixed(1) : 0;
    const qualificationRate = totalLeads > 0 ? (qualifiedLeads / totalLeads * 100).toFixed(1) : 0;

    return {
      totalLeads,
      qualifiedLeads,
      convertedLeads,
      avgScore: avgScore.toFixed(1),
      monthlyGrowth,
      conversionRate,
      qualificationRate
    };
  }, [data]);

  const sourceDistribution = useMemo(() => {
    if (!data?.leads) return {};

    const distribution = {};
    LEAD_SOURCES.forEach((source) => {
      distribution[source.value] = 0;
    });

    data.leads.forEach((lead) => {
      if (!lead.source) return;
      if (distribution[lead.source] !== undefined) {
        distribution[lead.source] += 1;
      }
    });

    return distribution;
  }, [data]);

  const qualificationDistribution = useMemo(() => {
    if (!data?.leads) return {};

    const distribution = {};
    Object.keys(QUALIFICATION_LEVELS).forEach((key) => {
      distribution[key] = 0;
    });

    data.leads.forEach((lead) => {
      if (lead.qualification && QUALIFICATION_LEVELS[lead.qualification.toUpperCase()]) {
        distribution[lead.qualification.toUpperCase()]++;
      }
    });

    return distribution;
  }, [data]);

  const hotLeads = useMemo(() => {
    if (!data?.leads) return [];

    return data.leads.
    filter((lead) => lead.qualification === 'hot' && lead.score >= 80).
    sort((a, b) => b.score - a.score).
    slice(0, 5);
  }, [data]);

  const upcomingFollowUps = useMemo(() => {
    if (!data?.followUps) return [];

    const today = new Date();
    return data.followUps.
    filter((f) => {
      const followUpDate = new Date(f.dueDate);
      const daysUntil = Math.ceil((followUpDate - today) / (1000 * 60 * 60 * 24));
      return daysUntil >= 0 && daysUntil <= 7;
    }).
    sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate)).
    slice(0, 5);
  }, [data]);

  const renderSourceCard = (sourceKey, count) => {
    const config = LEAD_SOURCES.find((source) => source.value === sourceKey);
    const total = data?.leads?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={sourceKey} size="small" className="source-card">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 14, marginBottom: 4 }}>{config?.icon}</div>
          <div style={{ color: config?.color, fontWeight: 'bold', fontSize: 14 }}>
            {count}
          </div>
          <div style={{ fontSize: 11, color: '#666', marginTop: 2 }}>
            {config?.label || sourceKey}
          </div>
          <Progress
            percent={percentage}
            strokeColor={config?.color}
            showInfo={false}
            size="small" />

        </div>
      </Card>);

  };

  const renderQualificationCard = (qualKey, count) => {
    const config = QUALIFICATION_LEVELS[qualKey];
    const total = data?.leads?.length || 0;
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={qualKey} size="small" className="qualification-card">
        <div style={{ textAlign: 'center' }}>
          <Tag color={config.color} style={{ marginBottom: 4 }}>
            {config.label}
          </Tag>
          <div style={{ color: config.color, fontWeight: 'bold', fontSize: 16 }}>
            {count}
          </div>
          <Progress
            percent={percentage}
            strokeColor={config.color}
            showInfo={false}
            size="small" />

        </div>
      </Card>);

  };

  const getScoreColor = (score) => {
    const color = Object.values(SCORE_COLORS).find((c) => score >= c.min);
    return color?.color || '#8c8c8c';
  };

  const _getScoreLabel = (score) => {
    const color = Object.values(SCORE_COLORS).find((c) => score >= c.min);
    return color?.label || '未知';
  };

  return (
    <div className="lead-overview">
      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="线索总数"
              value={overviewStats.totalLeads}
              prefix={<Target />}
              suffix={`(${overviewStats.qualifiedLeads} 合格)`}
              valueStyle={{ color: '#1890ff' }}
              trend={overviewStats.monthlyGrowth} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="转化率"
              value={overviewStats.conversionRate}
              suffix="%"
              prefix={<TrendingUp />}
              valueStyle={{ color: '#52c41a' }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="合格率"
              value={overviewStats.qualificationRate}
              suffix="%"
              prefix={<Star />}
              valueStyle={{ color: '#722ed1' }} />

          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="平均评分"
              value={overviewStats.avgScore}
              suffix="/ 100"
              prefix={<Trophy />}
              valueStyle={{ color: getScoreColor(parseFloat(overviewStats.avgScore)) }} />

          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 线索来源分布 */}
        <Col xs={24} lg={12}>
          <Card title="线索来源分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(sourceDistribution).map(([source, count]) =>
              renderSourceCard(source, count)
              )}
            </Row>
          </Card>
        </Col>

        {/* 资格分级分布 */}
        <Col xs={24} lg={12}>
          <Card title="资格分级分布" loading={loading}>
            <Row gutter={[8, 8]}>
              {Object.entries(qualificationDistribution).map(([qual, count]) =>
              renderQualificationCard(qual, count)
              )}
            </Row>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mt-4">
        {/* 热门线索 */}
        <Col xs={24} lg={12}>
          <Card
            title="热门线索"
            loading={loading}
            extra={
            <Button type="link" onClick={() => onNavigate && onNavigate('hot-leads')}>
                查看更多
              </Button>
            }>

            <List
              dataSource={hotLeads}
              renderItem={(lead) =>
              <List.Item>
                  <List.Item.Meta
                  avatar={<Avatar icon={<Users />} />}
                  title={
                  <div>
                        <span>{lead.companyName}</span>
                        <Tag color={getScoreColor(lead.score)} style={{ marginLeft: 8 }}>
                          {lead.score}分
                        </Tag>
                      </div>
                  }
                  description={
                  <div>
                        <div>{lead.contactPerson} · {lead.industry}</div>
                        <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                          <Phone size={10} /> {lead.phone}
                        </div>
                      </div>
                  } />

                </List.Item>
              }
              size="small" />

          </Card>
        </Col>

        {/* 即将跟进 */}
        <Col xs={24} lg={12}>
          <Card
            title="即将跟进"
            loading={loading}
            extra={
            <Button type="link" onClick={() => onNavigate && onNavigate('follow-ups')}>
                查看更多
              </Button>
            }>

            <Timeline>
              {upcomingFollowUps.map((followUp) =>
              <Timeline.Item
                key={followUp.id}
                color="#1890ff"
                dot={<Clock />}>

                  <div>
                    <div style={{ fontWeight: 'bold' }}>{followUp.leadCompany}</div>
                    <div style={{ fontSize: 12, color: '#666' }}>
                      {followUp.type} - {followUp.description}
                    </div>
                    <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
                      <Calendar size={10} /> {followUp.dueDate}
                    </div>
                  </div>
                </Timeline.Item>
              )}
            </Timeline>
          </Card>
        </Col>
      </Row>

      {/* 重要提醒 */}
      {data?.overdueFollowUps?.length > 0 &&
      <Card className="mt-4" loading={loading}>
          <Alert
          message={`发现 ${data.overdueFollowUps.length} 个逾期跟进任务`}
          description="建议及时处理逾期跟进，避免流失潜在客户"
          type="warning"
          showIcon
          action={
          <Button
            size="small"
            onClick={() => onNavigate && onNavigate('overdue')}>

                立即处理
              </Button>
          } />

        </Card>
      }
    </div>);

};

export default LeadOverview;