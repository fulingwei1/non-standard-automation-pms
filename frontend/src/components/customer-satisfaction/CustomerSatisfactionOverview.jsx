/**
 * Customer Satisfaction Overview Component
 * 客户满意度概览组件
 */

import React, { useState, useMemo } from 'react';
import { Card, Row, Col, Statistic, Progress, Rate, Trend } from 'antd';
import { 
  SmileOutlined, 
  MehOutlined, 
  FrownOutlined,
  TrophyOutlined,
  RiseOutlined,
  UserOutlined
} from '@ant-design/icons';
import { 
  SATISFACTION_LEVELS, 
  SURVEY_STATUS, 
  CHART_COLORS 
} from './customerSatisfactionConstants';

const CustomerSatisfactionOverview = ({ data, loading, onRefresh }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('month');

  const overviewStats = useMemo(() => {
    if (!data?.surveys) return {};

    const totalSurveys = data.surveys.length;
    const completedSurveys = data.surveys.filter(s => s.status === 'completed').length;
    const avgScore = data.surveys.reduce((acc, s) => acc + (s.avgScore || 0), 0) / totalSurveys || 0;
    const responseRate = (completedSurveys / totalSurveys * 100).toFixed(1);

    return {
      totalSurveys,
      completedSurveys,
      avgScore: avgScore.toFixed(1),
      responseRate,
      trend: data.trend || { direction: 'up', percentage: 5.2 }
    };
  }, [data]);

  const satisfactionDistribution = useMemo(() => {
    if (!data?.responses) return {};

    const distribution = {};
    Object.keys(SATISFACTION_LEVELS).forEach(key => {
      distribution[key] = 0;
    });

    data.responses.forEach(response => {
      const level = Object.entries(SATISFACTION_LEVELS).find(([_, config]) => 
        config.value === response.satisfactionLevel
      );
      if (level) {
        distribution[level[0]]++;
      }
    });

    return distribution;
  }, [data]);

  const renderSatisfactionCard = (level, count, total) => {
    const config = SATISFACTION_LEVELS[level];
    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;

    return (
      <Card key={level} size="small" className="satisfaction-card">
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>{config.icon}</div>
          <div style={{ color: config.color, fontWeight: 'bold', fontSize: 18 }}>
            {count}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            {config.label} ({percentage}%)
          </div>
          <Progress 
            percent={percentage} 
            strokeColor={config.color}
            showInfo={false}
            size="small"
          />
        </div>
      </Card>
    );
  };

  return (
    <div className="customer-satisfaction-overview">
      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="平均满意度"
              value={overviewStats.avgScore}
              suffix="/ 5.0"
              prefix={<Rate disabled value={parseFloat(overviewStats.avgScore)} />}
              valueStyle={{ color: CHART_COLORS.PRIMARY }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="完成调查数"
              value={overviewStats.completedSurveys}
              suffix={`/ ${overviewStats.totalSurveys}`}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: CHART_COLORS.POSITIVE }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="响应率"
              value={overviewStats.responseRate}
              suffix="%"
              prefix={<UserOutlined />}
              valueStyle={{ color: CHART_COLORS.NEUTRAL }}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card loading={loading}>
            <Statistic
              title="满意度趋势"
              value={overviewStats.trend.percentage}
              suffix="%"
              prefix={overviewStats.trend.direction === 'up' ? 
                <RiseOutlined /> : <Trend />}
              valueStyle={{ 
                color: overviewStats.trend.direction === 'up' ? 
                  CHART_COLORS.POSITIVE : CHART_COLORS.NEGATIVE 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 满意度分布 */}
      <Card title="满意度分布" className="mb-4" loading={loading}>
        <Row gutter={[16, 16]}>
          {Object.entries(satisfactionDistribution).map(([level, count]) => 
            renderSatisfactionCard(level, count, data?.responses?.length || 0)
          )}
        </Row>
      </Card>

      {/* 快速操作 */}
      <Card title="快速操作" loading={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card hoverable className="quick-action-card">
              <div style={{ textAlign: 'center' }}>
                <SmileOutlined style={{ fontSize: 32, color: CHART_COLORS.POSITIVE }} />
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontWeight: 'bold' }}>创建新调查</div>
                  <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                    设计新的满意度调查问卷
                  </div>
                </div>
              </div>
            </Card>
          </Col>
          
          <Col xs={24} sm={8}>
            <Card hoverable className="quick-action-card">
              <div style={{ textAlign: 'center' }}>
                <MehOutlined style={{ fontSize: 32, color: CHART_COLORS.NEUTRAL }} />
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontWeight: 'bold' }}>查看分析报告</div>
                  <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                    详细的满意度数据分析
                  </div>
                </div>
              </div>
            </Card>
          </Col>
          
          <Col xs={24} sm={8}>
            <Card hoverable className="quick-action-card">
              <div style={{ textAlign: 'center' }}>
                <FrownOutlined style={{ fontSize: 32, color: CHART_COLORS.NEGATIVE }} />
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontWeight: 'bold' }}>处理负面反馈</div>
                  <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                    回复和处理不满意反馈
                  </div>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default CustomerSatisfactionOverview;