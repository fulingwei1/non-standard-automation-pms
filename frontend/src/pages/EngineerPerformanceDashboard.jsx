import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Tabs, Select, DatePicker, Space, Button } from 'antd';
import { TrophyOutlined, RiseOutlined, TeamOutlined, BulbOutlined, FireOutlined } from '@ant-design/icons';
import api from '../services/api';

const { Option } = Select;
const { RangePicker } = DatePicker;
const EngineerPerformanceDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [companySummary, setCompanySummary] = useState(null);
  const [topEngineers, setTopEngineers] = useState([]);
  const [selectedJobType, setSelectedJobType] = useState(null);
  const [currentPeriod, setCurrentPeriod] = useState(null);

  // 获取公司整体概况
  const fetchCompanySummary = async (periodId = null) => {
    setLoading(true);
    try {
      const params = periodId ? { period_id: periodId } : {};
      const response = await api.get('/api/v1/engineer-performance/summary/company', { params });
      if (response.data.code === 200) {
        setCompanySummary(response.data.data);
        setCurrentPeriod(response.data.data.period_name);
      }
    } catch (error) {
      console.error('获取公司概况失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取 Top N 工程师
  const fetchTopEngineers = async (jobType = null) => {
    try {
      const params = { n: 10 };
      if (jobType) {params.job_type = jobType;}
      const response = await api.get('/api/v1/engineer-performance/ranking/top', { params });
      if (response.data.code === 200) {
        setTopEngineers(response.data.data);
      }
    } catch (error) {
      console.error('获取 Top 工程师失败:', error);
    }
  };

  useEffect(() => {
    fetchCompanySummary();
    fetchTopEngineers();
  }, []);

  useEffect(() => {
    fetchTopEngineers(selectedJobType);
  }, [selectedJobType]);

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

  // Top 工程师表格列
  const topEngineersColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank) => {
        if (rank === 1) {return <TrophyOutlined style={{ color: '#FFD700', fontSize: 20 }} />;}
        if (rank === 2) {return <TrophyOutlined style={{ color: '#C0C0C0', fontSize: 18 }} />;}
        if (rank === 3) {return <TrophyOutlined style={{ color: '#CD7F32', fontSize: 16 }} />;}
        return rank;
      }
    },
    {
      title: '姓名',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 100,
    },
    {
      title: '岗位',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 120,
      render: (jobType) => getJobTypeName(jobType)
    },
    {
      title: '职级',
      dataIndex: 'job_level',
      key: 'job_level',
      width: 80,
      render: (level) => {
        const names = { 'junior': '初级', 'intermediate': '中级', 'senior': '高级', 'expert': '专家' };
        return names[level] || level;
      }
    },
    {
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 120,
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 80,
      render: (score) => <span style={{ fontWeight: 'bold', color: '#1890ff' }}>{score?.toFixed(2)}</span>
    },
    {
      title: '等级',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level) => <Tag color={getLevelColor(level)}>{getLevelName(level)}</Tag>
    }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">工程师绩效评价总览</h1>
        <p className="text-gray-500">当前周期：{currentPeriod || '加载中...'}</p>
      </div>

      {/* 统计卡片 */}
      {companySummary && (
        <Row gutter={16} className="mb-6">
          <Col span={6}>
            <Card>
              <Statistic
                title="工程师总数"
                value={companySummary.total_engineers}
                prefix={<TeamOutlined />}
                styles={{ content: { color: '#1890ff' } }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均分"
                value={companySummary.avg_score}
                precision={2}
                prefix={<RiseOutlined />}
                styles={{ content: { color: '#52c41a' } }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="最高分"
                value={companySummary.max_score}
                precision={2}
                prefix={<FireOutlined />}
                styles={{ content: { color: '#faad14' } }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="优秀率"
                value={companySummary.level_distribution?.S ?
                  (companySummary.level_distribution.S / companySummary.total_engineers * 100).toFixed(1) : 0}
                suffix="%"
                prefix={<BulbOutlined />}
                styles={{ content: { color: '#52c41a' } }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 按岗位类型统计 */}
      {companySummary?.by_job_type && (
        <Row gutter={16} className="mb-6">
          {Object.entries(companySummary.by_job_type).map(([jobType, stats]) => (
            <Col span={8} key={jobType}>
              <Card title={getJobTypeName(jobType)} bordered={false}>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>人数：</span>
                    <span className="font-semibold">{stats.count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>平均分：</span>
                    <span className="font-semibold text-blue-600">{stats.avg_score?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>最高分：</span>
                    <span className="font-semibold text-green-600">{stats.max_score?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>最低分：</span>
                    <span className="font-semibold text-orange-600">{stats.min_score?.toFixed(2)}</span>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* 等级分布 */}
      {companySummary?.level_distribution && (
        <Card title="等级分布" className="mb-6">
          <Row gutter={16}>
            {Object.entries(companySummary.level_distribution).map(([level, count]) => (
              <Col span={4} key={level}>
                <Statistic
                  title={getLevelName(level)}
                  value={count || "unknown"}
                  suffix={`人 (${(count / companySummary.total_engineers * 100).toFixed(1)}%)`}
                  styles={{ content: { color: getLevelColor(level) === 'green' ? '#52c41a' :
                               getLevelColor(level) === 'blue' ? '#1890ff' :
                               getLevelColor(level) === 'orange' ? '#faad14' :
                               getLevelColor(level) === 'volcano' ? '#fa8c16' : '#f5222d' } }}
                />
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Top 工程师排行 */}
      <Card
        title="Top 10 工程师"
        className="mb-6"
        extra={
          <Select
            placeholder="选择岗位类型"
            allowClear
            style={{ width: 150 }}
            onChange={setSelectedJobType}
          >
            <Option value="mechanical">机械工程师</Option>
            <Option value="test">测试工程师</Option>
            <Option value="electrical">电气工程师</Option>
          </Select>
        }
      >
        <Table
          columns={topEngineersColumns}
          dataSource={topEngineers}
          rowKey="user_id"
          pagination={false}
          loading={loading}
        />
      </Card>

      {/* 快捷操作 */}
      <Row gutter={16}>
        <Col span={8}>
          <Card hoverable onClick={() => window.location.href = '/engineer-performance/ranking'}>
            <div className="text-center">
              <TrophyOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              <h3 className="mt-4 text-lg font-semibold">查看完整排名</h3>
              <p className="text-gray-500">按部门、岗位、职级查看详细排名</p>
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card hoverable onClick={() => window.location.href = '/engineer-performance/collaboration'}>
            <div className="text-center">
              <TeamOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <h3 className="mt-4 text-lg font-semibold">跨部门协作评价</h3>
              <p className="text-gray-500">查看和提交跨部门互评</p>
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card hoverable onClick={() => window.location.href = '/engineer-performance/knowledge'}>
            <div className="text-center">
              <BulbOutlined style={{ fontSize: 48, color: '#faad14' }} />
              <h3 className="mt-4 text-lg font-semibold">知识贡献</h3>
              <p className="text-gray-500">查看知识贡献排行和提交贡献</p>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default EngineerPerformanceDashboard;
