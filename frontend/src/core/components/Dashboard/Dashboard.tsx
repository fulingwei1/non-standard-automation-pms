/**
 * 通用Dashboard组件
 * 统一处理Dashboard布局、统计卡片、图表
 */

import React from 'react';
import { Row, Col, Card, Statistic, Spin } from 'antd';
import { useDataLoader } from '../../hooks/useDataLoader';

export interface StatCard {
  key: string;
  title: string;
  value: number | string;
  suffix?: string;
  prefix?: string;
  trend?: {
    value: number;
    isUp: boolean;
  };
  icon?: React.ReactNode;
}

export interface DashboardProps {
  /** Dashboard标题 */
  title?: string;
  /** 查询Key */
  queryKey: (string | number)[];
  /** 查询函数 */
  queryFn: () => Promise<{
    stats: StatCard[];
    charts?: Array<{
      key: string;
      title: string;
      type: 'line' | 'bar' | 'pie';
      data: any;
    }>;
  }>;
  /** 统计卡片列数 */
  statsCols?: number;
  /** 自定义渲染 */
  renderCustom?: (data: any) => React.ReactNode;
}

/**
 * 通用Dashboard组件
 * 
 * @example
 * ```tsx
 * <Dashboard
 *   title="项目Dashboard"
 *   queryKey={['dashboard', 'projects']}
 *   queryFn={() => dashboardApi.getProjectDashboard()}
 *   statsCols={4}
 * />
 * ```
 */
export function Dashboard({
  title,
  queryKey,
  queryFn,
  statsCols = 4,
  renderCustom,
}: DashboardProps) {
  const { data, isLoading, error, refetch } = useDataLoader(queryKey, queryFn);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <p>加载失败，请重试</p>
      </div>
    );
  }

  const stats = data?.stats ?? [];
  const charts = data?.charts ?? [];

  return (
    <div className="dashboard">
      {title && <h2 style={{ marginBottom: 24 }}>{title}</h2>}

      {/* 统计卡片 */}
      {stats.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {stats.map((stat) => (
            <Col key={stat.key} xs={24} sm={12} md={24 / statsCols}>
              <Card>
                <Statistic
                  title={stat.title}
                  value={stat.value}
                  prefix={stat.prefix}
                  suffix={stat.suffix}
                  valueStyle={{ color: stat.trend?.isUp ? '#3f8600' : '#cf1322' }}
                />
                {stat.trend && (
                  <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                    {stat.trend.isUp ? '↑' : '↓'} {Math.abs(stat.trend.value)}%
                  </div>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* 图表 */}
      {charts.length > 0 && (
        <Row gutter={[16, 16]}>
          {charts.map((chart) => (
            <Col key={chart.key} xs={24} md={12}>
              <Card title={chart.title}>
                {/* 这里可以集成图表库，如 ECharts、Recharts 等 */}
                <div style={{ height: 300 }}>
                  Chart: {chart.type} - {chart.key}
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* 自定义渲染 */}
      {renderCustom && renderCustom(data)}
    </div>
  );
}
