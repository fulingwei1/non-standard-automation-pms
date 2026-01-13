import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Tag, Progress, Tabs, Table, Empty, Spin } from 'antd';
import { TrophyOutlined, RiseOutlined, FallOutlined, LineChartOutlined } from '@ant-design/icons';
import { Radar, Line } from '@ant-design/plots';
import axios from 'axios';
import { useParams } from 'react-router-dom';

const { TabPane } = Tabs;

const EngineerPerformanceDetail = () => {
  const { userId } = useParams();
  const [loading, setLoading] = useState(false);
  const [performance, setPerformance] = useState(null);
  const [trend, setTrend] = useState([]);
  const [comparison, setComparison] = useState(null);

  // 获取个人绩效详情
  const fetchPerformance = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/v1/engineer-performance/engineer/${userId}`);
      if (response.data.code === 200) {
        setPerformance(response.data.data);
      }
    } catch (error) {
      console.error('获取绩效详情失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取历史趋势
  const fetchTrend = async () => {
    try {
      const response = await axios.get(`/api/v1/engineer-performance/engineer/${userId}/trend`);
      if (response.data.code === 200) {
        setTrend(response.data.data.trends);
      }
    } catch (error) {
      console.error('获取趋势失败:', error);
    }
  };

  // 获取对比数据
  const fetchComparison = async () => {
    try {
      const response = await axios.get(`/api/v1/engineer-performance/engineer/${userId}/comparison`);
      if (response.data.code === 200) {
        setComparison(response.data.data);
      }
    } catch (error) {
      console.error('获取对比数据失败:', error);
    }
  };

  useEffect(() => {
    if (userId) {
      fetchPerformance();
      fetchTrend();
      fetchComparison();
    }
  }, [userId]);

  // 等级标签颜色
  const getLevelColor = (level) => {
    const colors = {
      'S': 'green',
      'A': 'blue',
      'B': 'orange',
      'C': 'volcano',
      'D': 'red'
    };
    return colors[level] || 'default';
  };

  // 等级名称
  const getLevelName = (level) => {
    const names = {
      'S': '优秀',
      'A': '良好',
      'B': '合格',
      'C': '待改进',
      'D': '不合格'
    };
    return names[level] || level;
  };

  // 岗位类型名称
  const getJobTypeName = (jobType) => {
    const names = {
      'mechanical': '机械工程师',
      'test': '测试工程师',
      'electrical': '电气工程师'
    };
    return names[jobType] || jobType;
  };

  // 职级名称
  const getJobLevelName = (level) => {
    const names = {
      'junior': '初级',
      'intermediate': '中级',
      'senior': '高级',
      'expert': '专家'
    };
    return names[level] || level;
  };

  // 五维雷达图数据
  const radarData = performance?.dimension_scores ? [
    { dimension: '技术能力', score: performance.dimension_scores.technical || 0 },
    { dimension: '项目执行', score: performance.dimension_scores.execution || 0 },
    { dimension: '成本质量', score: performance.dimension_scores.cost_quality || 0 },
    { dimension: '知识沉淀', score: performance.dimension_scores.knowledge || 0 },
    { dimension: '团队协作', score: performance.dimension_scores.collaboration || 0 },
  ] : [];

  // 雷达图配置
  const radarConfig = {
    data: radarData,
    xField: 'dimension',
    yField: 'score',
    meta: {
      score: {
        alias: '得分',
        min: 0,
        max: 100,
      },
    },
    xAxis: {
      line: null,
      tickLine: null,
    },
    yAxis: {
      label: false,
      grid: {
        alternateColor: 'rgba(0, 0, 0, 0.04)',
      },
    },
    point: {
      size: 4,
    },
    area: {},
  };

  // 趋势图数据
  const trendConfig = {
    data: trend,
    xField: 'period_name',
    yField: 'total_score',
    seriesField: 'type',
    yAxis: {
      label: {
        formatter: (v) => `${v}分`,
      },
    },
    legend: {
      position: 'top',
    },
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
  };

  if (loading) {
    return (
      <div className="p-6 flex justify-center items-center h-96">
        <Spin size="large" />
      </div>
    );
  }

  if (!performance) {
    return (
      <div className="p-6">
        <Empty description="未找到绩效数据" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 头部信息 */}
      <Card className="mb-6">
        <Row gutter={16}>
          <Col span={16}>
            <h1 className="text-2xl font-bold mb-2">{performance.user_name}</h1>
            <Space size="large">
              <Tag color="blue">{getJobTypeName(performance.job_type)}</Tag>
              <span className="text-gray-600">{getJobLevelName(performance.job_level)}</span>
              <span className="text-gray-600">周期：{performance.period_name || '当前周期'}</span>
            </Space>
          </Col>
          <Col span={8} className="text-right">
            <div className="text-4xl font-bold text-blue-600 mb-2">
              {performance.total_score?.toFixed(2) || '--'}
            </div>
            <Tag color={getLevelColor(performance.level)} className="text-lg px-4 py-1">
              {getLevelName(performance.level)}
            </Tag>
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={16} className="mb-6">
        <Col span={8}>
          <Card>
            <Statistic
              title="部门排名"
              value={performance.dept_rank || '--'}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="公司排名"
              value={performance.company_rank || '--'}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="与平均分差距"
              value={comparison ? (performance.total_score - comparison.job_type_avg).toFixed(2) : '--'}
              prefix={comparison && performance.total_score > comparison.job_type_avg ?
                <RiseOutlined /> : <FallOutlined />}
              valueStyle={{
                color: comparison && performance.total_score > comparison.job_type_avg ? '#52c41a' : '#f5222d'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 五维得分 */}
      <Row gutter={16} className="mb-6">
        <Col span={12}>
          <Card title="五维雷达图" className="h-full">
            {radarData.length > 0 ? (
              <Radar {...radarConfig} height={300} />
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="各维度得分详情" className="h-full">
            <div className="space-y-4">
              {performance.dimension_scores && Object.entries({
                '技术能力': performance.dimension_scores.technical,
                '项目执行': performance.dimension_scores.execution,
                '成本质量': performance.dimension_scores.cost_quality,
                '知识沉淀': performance.dimension_scores.knowledge,
                '团队协作': performance.dimension_scores.collaboration,
              }).map(([name, score]) => (
                <div key={name}>
                  <div className="flex justify-between mb-1">
                    <span>{name}</span>
                    <span className="font-semibold">{score?.toFixed(2) || '--'}</span>
                  </div>
                  <Progress
                    percent={score || 0}
                    strokeColor={score >= 85 ? '#52c41a' : score >= 70 ? '#1890ff' : '#faad14'}
                    showInfo={false}
                  />
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 标签页：趋势、对比 */}
      <Card>
        <Tabs defaultActiveKey="trend">
          <TabPane tab="历史趋势" key="trend">
            {trend.length > 0 ? (
              <Line {...trendConfig} height={300} />
            ) : (
              <Empty description="暂无历史数据" />
            )}
          </TabPane>
          <TabPane tab="同岗位对比" key="comparison">
            {comparison ? (
              <div className="space-y-4">
                <Card title="与同岗位平均对比" bordered={false}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <div className="text-center">
                        <div className="text-gray-600 mb-2">我的得分</div>
                        <div className="text-3xl font-bold text-blue-600">
                          {performance.total_score?.toFixed(2)}
                        </div>
                      </div>
                    </Col>
                    <Col span={12}>
                      <div className="text-center">
                        <div className="text-gray-600 mb-2">
                          同岗位平均 ({comparison.job_type_count}人)
                        </div>
                        <div className="text-3xl font-bold text-gray-600">
                          {comparison.job_type_avg?.toFixed(2)}
                        </div>
                      </div>
                    </Col>
                  </Row>
                </Card>
                <Card title="与同级别平均对比" bordered={false}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <div className="text-center">
                        <div className="text-gray-600 mb-2">我的得分</div>
                        <div className="text-3xl font-bold text-blue-600">
                          {performance.total_score?.toFixed(2)}
                        </div>
                      </div>
                    </Col>
                    <Col span={12}>
                      <div className="text-center">
                        <div className="text-gray-600 mb-2">
                          同级别平均 ({comparison.level_count}人)
                        </div>
                        <div className="text-3xl font-bold text-gray-600">
                          {comparison.level_avg?.toFixed(2)}
                        </div>
                      </div>
                    </Col>
                  </Row>
                </Card>
              </div>
            ) : (
              <Empty description="暂无对比数据" />
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default EngineerPerformanceDetail;
