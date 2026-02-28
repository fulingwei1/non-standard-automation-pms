import React, { useState, useEffect } from 'react';
import { Card, Table, Select, Input, Tag, Space, Button, Tabs } from 'antd';
import { SearchOutlined, FilterOutlined, TrophyOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const { Option } = Select;
const EngineerPerformanceRanking = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [rankings, setRankings] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    job_type: null,
    job_level: null,
    department_id: null,
    limit: 20,
    offset: 0
  });
  const [searchText, setSearchText] = useState('');
  const [currentTab, setCurrentTab] = useState('all');

  // 获取排名数据
  const fetchRankings = async () => {
    setLoading(true);
    try {
      const params = { ...filters };
      // 根据当前标签页设置岗位类型
      if (currentTab !== 'all') {
        params.job_type = currentTab;
      }

      const response = await axios.get('/api/v1/engineer-performance/ranking', { params });
      if (response.data.code === 200) {
        setRankings(response.data.data.items);
        setTotal(response.data.data.total);
      }
    } catch (error) {
      console.error('获取排名失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRankings();
  }, [filters, currentTab]);

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

  // 排名变化显示
  const renderRankChange = (change) => {
    if (!change || change === 0) {return <span className="text-gray-400">-</span>;}
    if (change > 0) {return <span className="text-green-600">↑{change}</span>;}
    return <span className="text-red-600">↓{Math.abs(change)}</span>;
  };

  // 分数变化显示
  const renderScoreChange = (change) => {
    if (!change || change === 0) {return <span className="text-gray-400">-</span>;}
    if (change > 0) {return <span className="text-green-600">+{change.toFixed(2)}</span>;}
    return <span className="text-red-600">{change.toFixed(2)}</span>;
  };

  // 表格列定义
  const columns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      fixed: 'left',
      render: (rank) => {
        if (rank === 1) {return <TrophyOutlined style={{ color: '#FFD700', fontSize: 24 }} />;}
        if (rank === 2) {return <TrophyOutlined style={{ color: '#C0C0C0', fontSize: 22 }} />;}
        if (rank === 3) {return <TrophyOutlined style={{ color: '#CD7F32', fontSize: 20 }} />;}
        return <span className="font-semibold text-lg">{rank}</span>;
      }
    },
    {
      title: '姓名',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
      fixed: 'left',
      render: (name, record) => (
        <a
          className="text-blue-600 hover:text-blue-800 font-medium"
          onClick={() => navigate(`/engineer-performance/engineer/${record.user_id}`)}
        >
          {name}
        </a>
      )
    },
    {
      title: '岗位',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 120,
      render: (jobType) => <Tag color="blue">{getJobTypeName(jobType)}</Tag>
    },
    {
      title: '职级',
      dataIndex: 'job_level',
      key: 'job_level',
      width: 100,
      render: (level) => getJobLevelName(level)
    },
    {
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 150,
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 100,
      sorter: (a, b) => a.total_score - b.total_score,
      render: (score) => (
        <span className="font-bold text-blue-600 text-lg">{score?.toFixed(2)}</span>
      )
    },
    {
      title: '等级',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level) => <Tag color={getLevelColor(level)}>{getLevelName(level)}</Tag>
    },
    {
      title: '分数变化',
      dataIndex: 'score_change',
      key: 'score_change',
      width: 100,
      render: (change) => renderScoreChange(change)
    },
    {
      title: '排名变化',
      dataIndex: 'rank_change',
      key: 'rank_change',
      width: 100,
      render: (change) => renderRankChange(change)
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => navigate(`/engineer-performance/engineer/${record.user_id}`)}
          >
            查看详情
          </Button>
        </Space>
      )
    }
  ];

  // 过滤后的数据（用于搜索）
  const filteredRankings = searchText
    ? (rankings || []).filter(r => r.user_name?.includes(searchText) || r.department_name?.includes(searchText))
    : rankings;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">工程师绩效排名</h1>
        <p className="text-gray-500">按综合得分排序，实时更新</p>
      </div>

      <Card>
        {/* 筛选栏 */}
        <div className="mb-4 flex justify-between items-center">
          <Space>
            <Input
              placeholder="搜索姓名或部门"
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <Select
              placeholder="职级"
              allowClear
              style={{ width: 120 }}
              onChange={(value) => setFilters({ ...filters, job_level: value, offset: 0 })}
            >
              <Option value="junior">初级</Option>
              <Option value="intermediate">中级</Option>
              <Option value="senior">高级</Option>
              <Option value="expert">专家</Option>
            </Select>
          </Space>
          <Button icon={<FilterOutlined />} onClick={fetchRankings}>
            刷新
          </Button>
        </div>

        {/* 标签页 */}
        <Tabs
          activeKey={currentTab}
          onChange={setCurrentTab}
          items={[
            { key: 'all', label: '全部' },
            { key: 'mechanical', label: '机械工程师' },
            { key: 'test', label: '测试工程师' },
            { key: 'electrical', label: '电气工程师' },
          ]}
        />

        {/* 排名表格 */}
        <Table
          columns={columns}
          dataSource={filteredRankings}
          rowKey="user_id"
          loading={loading}
          pagination={{
            total,
            pageSize: filters.limit,
            current: filters.offset / filters.limit + 1,
            onChange: (page, pageSize) => {
              setFilters({
                ...filters,
                limit: pageSize,
                offset: (page - 1) * pageSize
              });
            },
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 人`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default EngineerPerformanceRanking;
