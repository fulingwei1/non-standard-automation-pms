/**
 * Customer Basic Info Component
 * 客户基本信息组件
 */

import React from 'react';
import { Card, Row, Col, Tag, Avatar, Space, Divider, Typography, Progress } from 'antd';
import { 
  Building2, 
  User, 
  Phone, 
  Mail, 
  MapPin, 
  Calendar,
  Award,
  TrendingUp,
  Star
} from 'lucide-react';
import { 
  CUSTOMER_TYPES, 
  CUSTOMER_STATUS, 
  CUSTOMER_LEVELS,
  BUSINESS_METRICS 
} from '@/lib/constants/customer360';

const { Title, Text, Paragraph } = Typography;

const CustomerBasicInfo = ({ customer, loading }) => {
  if (!customer) {return null;}

  const customerTypeConfig = CUSTOMER_TYPES[customer.type?.toUpperCase()];
  const customerStatusConfig = CUSTOMER_STATUS[customer.status?.toUpperCase()];
  const customerLevelConfig = CUSTOMER_LEVELS[customer.level?.toUpperCase()];

  const satisfactionScore = customer.satisfactionScore || 0;
  const satisfactionColor = satisfactionScore >= 4.5 ? '#52c41a' : 
                          satisfactionScore >= 3.5 ? '#1890ff' : 
                          satisfactionScore >= 2.5 ? '#faad14' : '#ff4d4f';

  return (
    <Card 
      loading={loading}
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Avatar size={64} icon={<Building2 />} style={{ marginRight: 16 }} />
            <div>
              <Title level={3} style={{ margin: 0 }}>
                {customer.name}
              </Title>
              <Space>
                <Tag color={customerTypeConfig?.color}>
                  {customerTypeConfig?.icon} {customerTypeConfig?.label}
                </Tag>
                <Tag color={customerStatusConfig?.color}>
                  {customerStatusConfig?.label}
                </Tag>
                <Tag color={customerLevelConfig?.color}>
                  {customerLevelConfig?.label}
                </Tag>
              </Space>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 24, color: satisfactionColor, fontWeight: 'bold' }}>
              {satisfactionScore.toFixed(1)}
            </div>
            <div style={{ fontSize: 12, color: '#666' }}>
              <Star size={12} /> 客户满意度
            </div>
          </div>
        </div>
      }
    >
      <Row gutter={[24, 16]}>
        {/* 基本信息 */}
        <Col xs={24} lg={12}>
          <div style={{ marginBottom: 16 }}>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>联系信息</Text>
            <Space direction="vertical" size={8}>
              <div>
                <User size={14} style={{ marginRight: 8, color: '#666' }} />
                <Text>联系人: {customer.contactPerson}</Text>
              </div>
              <div>
                <Phone size={14} style={{ marginRight: 8, color: '#666' }} />
                <Text>电话: {customer.phone}</Text>
              </div>
              <div>
                <Mail size={14} style={{ marginRight: 8, color: '#666' }} />
                <Text>邮箱: {customer.email}</Text>
              </div>
              <div>
                <MapPin size={14} style={{ marginRight: 8, color: '#666' }} />
                <Text>地址: {customer.address}</Text>
              </div>
            </Space>
          </div>

          <Divider />

          <div>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>业务信息</Text>
            <Space direction="vertical" size={8}>
              <div>
                <Building2 size={14} style={{ marginRight: 8, color: '#666' }} />
                <Text>行业: {customer.industry}</Text>
              </div>
              <div>
                <Calendar size={14} style={{ marginRight: 8, color: '#666' }} />
                <Text>合作开始: {customer.sinceDate}</Text>
              </div>
              <div>
                <Award size={14} style={{ marginRight: 8, color: '#666' }} />
                <Text>服务等级: {customer.serviceLevel}</Text>
              </div>
            </Space>
          </div>
        </Col>

        {/* 业务指标 */}
        <Col xs={24} lg={12}>
          <Text strong style={{ marginBottom: 16, display: 'block' }}>关键业务指标</Text>
          
          <Row gutter={[16, 16]}>
            <Col xs={12}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, color: '#1890ff', fontWeight: 'bold' }}>
                  ¥{customer.lifetimeValue?.toLocaleString() || 0}
                </div>
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                  {BUSINESS_METRICS.LIFETIME_VALUE.label}
                </div>
              </Card>
            </Col>
            <Col xs={12}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, color: '#52c41a', fontWeight: 'bold' }}>
                  {customer.orderCount || 0}
                </div>
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                  历史订单
                </div>
              </Card>
            </Col>
            <Col xs={12}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, color: '#722ed1', fontWeight: 'bold' }}>
                  ¥{customer.avgOrderValue?.toLocaleString() || 0}
                </div>
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                  {BUSINESS_METRICS.AVERAGE_ORDER.label}
                </div>
              </Card>
            </Col>
            <Col xs={12}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, color: '#faad14', fontWeight: 'bold' }}>
                  {customer.projectSuccessRate || 0}%
                </div>
                <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                  {BUSINESS_METRICS.PROJECT_SUCCESS_RATE.label}
                </div>
              </Card>
            </Col>
          </Row>

          <Divider style={{ margin: '24px 0' }} />

          <div>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>客户分层分析</Text>
            <div style={{ marginBottom: 16 }}>
              <Text style={{ marginBottom: 4, display: 'block' }}>
                <TrendingUp size={14} style={{ marginRight: 8 }} />
                增长趋势
              </Text>
              <Progress 
                percent={customer.growthTrend || 65} 
                strokeColor="#52c41a"
                format={percent => `${percent}%`}
              />
            </div>
            <div>
              <Text style={{ marginBottom: 4, display: 'block' }}>
                <Star size={14} style={{ marginRight: 8 }} />
                忠诚度指数
              </Text>
              <Progress 
                percent={customer.loyaltyIndex || 78} 
                strokeColor="#722ed1"
                format={percent => `${percent}%`}
              />
            </div>
          </div>
        </Col>
      </Row>

      {/* 备注 */}
      {customer.notes && (
        <>
          <Divider />
          <div>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>备注</Text>
            <Paragraph style={{ background: '#f5f5f5', padding: '12px', borderRadius: '6px' }}>
              {customer.notes}
            </Paragraph>
          </div>
        </>
      )}
    </Card>
  );
};

export default CustomerBasicInfo;