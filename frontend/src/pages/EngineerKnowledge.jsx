import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, Tag, Space, message, Tabs, Statistic, Row, Col, Rate } from 'antd';
import { BulbOutlined, FileTextOutlined, CodeOutlined, PlusOutlined, CheckOutlined, CloseOutlined, StarOutlined } from '@ant-design/icons';
import api from '../services/api';

const { TextArea } = Input;
const { Option } = Select;
const EngineerKnowledge = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [reuseModalVisible, setReuseModalVisible] = useState(false);
  const [selectedContribution, setSelectedContribution] = useState(null);
  const [contributions, setContributions] = useState([]);
  const [rankings, setRankings] = useState([]);
  const [myStats, setMyStats] = useState(null);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    contribution_type: null,
    status: null,
    job_type: null,
    limit: 20,
    offset: 0
  });
  const [form] = Form.useForm();
  const [reuseForm] = Form.useForm();
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  // 获取知识贡献列表
  const fetchContributions = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/engineer-performance/knowledge/contributions', {
        params: filters
      });
      if (response.data.code === 200) {
        setContributions(response.data.data.items);
        setTotal(response.data.data.total);
      }
    } catch (error) {
      console.error('获取知识贡献列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取排行榜
  const fetchRankings = async () => {
    try {
      const response = await api.get('/api/v1/engineer-performance/knowledge/rankings', {
        params: { limit: 10 }
      });
      if (response.data.code === 200) {
        setRankings(response.data.data);
      }
    } catch (error) {
      console.error('获取排行榜失败:', error);
    }
  };

  // 获取我的统计
  const fetchMyStats = async () => {
    try {
      const response = await api.get(`/api/v1/engineer-performance/knowledge/contributor/${currentUser.id}/stats`);
      if (response.data.code === 200) {
        setMyStats(response.data.data);
      }
    } catch (error) {
      console.error('获取我的统计失败:', error);
    }
  };

  useEffect(() => {
    fetchContributions();
    fetchRankings();
    fetchMyStats();
  }, [filters]);

  // 提交新贡献
  const handleSubmit = async (values) => {
    try {
      const response = await api.post('/api/v1/engineer-performance/knowledge/contributions', values);
      if (response.data.code === 200) {
        message.success('知识贡献提交成功，等待审核');
        setModalVisible(false);
        form.resetFields();
        fetchContributions();
        fetchMyStats();
      }
    } catch (error) {
      message.error(error.response?.data?.detail || '提交失败');
    }
  };

  // 审核贡献
  const handleApprove = async (id, approve) => {
    try {
      const response = await api.put(`/api/v1/engineer-performance/knowledge/contributions/${id}/approve`, {
        approve,
        reviewer_comment: approve ? '通过审核' : '不符合要求'
      });
      if (response.data.code === 200) {
        message.success(approve ? '审核通过' : '已驳回');
        fetchContributions();
      }
    } catch (error) {
      message.error(error.response?.data?.detail || '审核失败');
    }
  };

  // 记录复用
  const handleRecordReuse = async (contribution) => {
    setSelectedContribution(contribution);
    setReuseModalVisible(true);
  };

  const handleReuseSubmit = async (values) => {
    try {
      const response = await api.post('/api/v1/engineer-performance/knowledge/reuse', {
        contribution_id: selectedContribution.id,
        ...values
      });
      if (response.data.code === 200) {
        message.success('复用记录提交成功');
        setReuseModalVisible(false);
        reuseForm.resetFields();
        fetchContributions();
      }
    } catch (error) {
      message.error(error.response?.data?.detail || '提交失败');
    }
  };

  // 贡献类型名称
  const getTypeName = (type) => {
    const names = {
      'design_doc': '设计文档',
      'technical_solution': '技术方案',
      'code_library': '代码库',
      'tool': '工具',
      'process_standard': '流程规范',
      'troubleshooting': '故障排查案例',
      'other': '其他'
    };
    return names[type] || type;
  };

  // 状态标签
  const renderStatus = (status) => {
    const statusConfig = {
      'pending': { color: 'orange', text: '待审核' },
      'approved': { color: 'green', text: '已通过' },
      'rejected': { color: 'red', text: '已驳回' }
    };
    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 贡献列表表格列
  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      render: (title, record) => (
        <div>
          <div className="font-semibold">{title}</div>
          {record.description && (
            <div className="text-xs text-gray-500 mt-1">{record.description.substring(0, 50)}...</div>
          )}
        </div>
      )
    },
    {
      title: '类型',
      dataIndex: 'contribution_type',
      key: 'contribution_type',
      width: 120,
      render: (type) => <Tag color="blue">{getTypeName(type)}</Tag>
    },
    {
      title: '贡献人',
      dataIndex: 'contributor_name',
      key: 'contributor_name',
      width: 100,
    },
    {
      title: '岗位',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 120,
      render: (jobType) => {
        const names = {
          'mechanical': '机械工程师',
          'test': '测试工程师',
          'electrical': '电气工程师'
        };
        return names[jobType] || jobType;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => renderStatus(status)
    },
    {
      title: '复用次数',
      dataIndex: 'reuse_count',
      key: 'reuse_count',
      width: 100,
      render: (count) => (
        <span className="font-semibold text-blue-600">{count || 0}</span>
      )
    },
    {
      title: '平均评分',
      dataIndex: 'rating_score',
      key: 'rating_score',
      width: 120,
      render: (score) => score ? <Rate disabled value={score || "unknown"} count={5} allowHalf /> : '-'
    },
    {
      title: '提交时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString() : '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          {record.status === 'pending' && currentUser.role === 'admin' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleApprove(record.id, true)}
              >
                通过
              </Button>
              <Button
                type="link"
                size="small"
                danger
                icon={<CloseOutlined />}
                onClick={() => handleApprove(record.id, false)}
              >
                驳回
              </Button>
            </>
          )}
          {record.status === 'approved' && (
            <Button
              type="link"
              size="small"
              onClick={() => handleRecordReuse(record)}
            >
              记录复用
            </Button>
          )}
          {record.file_path && (
            <Button
              type="link"
              size="small"
              onClick={() => window.open(record.file_path)}
            >
              查看
            </Button>
          )}
        </Space>
      )
    }
  ];

  // 排行榜表格列
  const rankingColumns = [
    {
      title: '排名',
      dataIndex: 'rank',
      key: 'rank',
      width: 60,
      render: (rank) => {
        if (rank === 1) {return <StarOutlined style={{ color: '#FFD700', fontSize: 20 }} />;}
        if (rank === 2) {return <StarOutlined style={{ color: '#C0C0C0', fontSize: 18 }} />;}
        if (rank === 3) {return <StarOutlined style={{ color: '#CD7F32', fontSize: 16 }} />;}
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
      render: (jobType) => {
        const names = {
          'mechanical': '机械工程师',
          'test': '测试工程师',
          'electrical': '电气工程师'
        };
        return <Tag color="blue">{names[jobType] || jobType}</Tag>;
      }
    },
    {
      title: '贡献数',
      dataIndex: 'contribution_count',
      key: 'contribution_count',
      width: 80,
      render: (count) => <span className="font-semibold">{count}</span>
    },
    {
      title: '总复用次数',
      dataIndex: 'total_reuse',
      key: 'total_reuse',
      width: 100,
      render: (count) => <span className="font-semibold text-green-600">{count}</span>
    },
    {
      title: '平均评分',
      dataIndex: 'avg_rating',
      key: 'avg_rating',
      width: 120,
      render: (score) => score ? <Rate disabled value={score || "unknown"} count={5} allowHalf /> : '-'
    }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">知识贡献管理</h1>
        <p className="text-gray-500">促进知识沉淀与复用</p>
      </div>

      {/* 我的统计 */}
      {myStats && (
        <Row gutter={16} className="mb-6">
          <Col span={6}>
            <Card>
              <Statistic
                title="我的贡献数"
                value={myStats.contribution_count}
                prefix={<FileTextOutlined />}
                styles={{ content: { color: '#1890ff' } }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总复用次数"
                value={myStats.total_reuse}
                prefix={<CodeOutlined />}
                styles={{ content: { color: '#52c41a' } }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均评分"
                value={myStats.avg_rating?.toFixed(2) || '--'}
                prefix={<StarOutlined />}
                styles={{ content: { color: '#faad14' } }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="我的排名"
                value={myStats.rank || '--'}
                prefix={<BulbOutlined />}
                styles={{ content: { color: '#722ed1' } }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Row gutter={16}>
        {/* 左侧：贡献列表 */}
        <Col span={16}>
          <Card
            title="知识贡献列表"
            extra={
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setModalVisible(true)}
              >
                新增贡献
              </Button>
            }
          >
            {/* 筛选栏 */}
            <div className="mb-4">
              <Space>
                <Select
                  placeholder="贡献类型"
                  allowClear
                  style={{ width: 150 }}
                  onChange={(value) => setFilters({ ...filters, contribution_type: value, offset: 0 })}
                >
                  <Option value="design_doc">设计文档</Option>
                  <Option value="technical_solution">技术方案</Option>
                  <Option value="code_library">代码库</Option>
                  <Option value="tool">工具</Option>
                  <Option value="process_standard">流程规范</Option>
                  <Option value="troubleshooting">故障排查案例</Option>
                  <Option value="other">其他</Option>
                </Select>
                <Select
                  placeholder="状态"
                  allowClear
                  style={{ width: 120 }}
                  onChange={(value) => setFilters({ ...filters, status: value, offset: 0 })}
                >
                  <Option value="pending">待审核</Option>
                  <Option value="approved">已通过</Option>
                  <Option value="rejected">已驳回</Option>
                </Select>
                <Select
                  placeholder="岗位类型"
                  allowClear
                  style={{ width: 140 }}
                  onChange={(value) => setFilters({ ...filters, job_type: value, offset: 0 })}
                >
                  <Option value="mechanical">机械工程师</Option>
                  <Option value="test">测试工程师</Option>
                  <Option value="electrical">电气工程师</Option>
                </Select>
              </Space>
            </div>

            <Table
              columns={columns}
              dataSource={contributions}
              rowKey="id"
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
                showTotal: (total) => `共 ${total} 条`
              }}
              scroll={{ x: 1400 }}
            />
          </Card>
        </Col>

        {/* 右侧：排行榜 */}
        <Col span={8}>
          <Card title="贡献排行榜">
            <Table
              columns={rankingColumns}
              dataSource={rankings}
              rowKey="user_id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* 新增贡献弹窗 */}
      <Modal
        title="提交知识贡献"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label="标题"
            name="title"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="简明扼要的标题" />
          </Form.Item>

          <Form.Item
            label="贡献类型"
            name="contribution_type"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select placeholder="选择贡献类型">
              <Option value="design_doc">设计文档</Option>
              <Option value="technical_solution">技术方案</Option>
              <Option value="code_library">代码库</Option>
              <Option value="tool">工具</Option>
              <Option value="process_standard">流程规范</Option>
              <Option value="troubleshooting">故障排查案例</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
            rules={[{ required: true, message: '请输入描述' }]}
          >
            <TextArea rows={4} placeholder="详细描述该知识贡献的内容、用途、适用场景等" />
          </Form.Item>

          <Form.Item
            label="文件路径/链接"
            name="file_path"
            extra="可选，提供文档路径或在线链接"
          >
            <Input placeholder="例如：/docs/design/xxx.md 或 https://..." />
          </Form.Item>

          <Form.Item
            label="关键词"
            name="tags"
            extra="可选，多个关键词用逗号分隔"
          >
            <Input placeholder="例如：机械设计,模块化,标准件" />
          </Form.Item>

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => {
                setModalVisible(false);
                form.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 记录复用弹窗 */}
      <Modal
        title="记录知识复用"
        open={reuseModalVisible}
        onCancel={() => {
          setReuseModalVisible(false);
          reuseForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={reuseForm}
          layout="vertical"
          onFinish={handleReuseSubmit}
        >
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <div className="font-semibold">{selectedContribution?.title}</div>
            <div className="text-sm text-gray-500 mt-1">{selectedContribution?.description}</div>
          </div>

          <Form.Item
            label="应用项目"
            name="project_id"
            rules={[{ required: true, message: '请输入项目ID' }]}
            extra="该知识在哪个项目中被复用"
          >
            <Input type="number" placeholder="项目ID" />
          </Form.Item>

          <Form.Item
            label="评分"
            name="rating_score"
            rules={[{ required: true, message: '请评分' }]}
            extra="评价该知识贡献的实用性"
          >
            <Rate count={5} />
          </Form.Item>

          <Form.Item
            label="复用说明"
            name="usage_note"
            extra="可选，说明如何使用以及效果"
          >
            <TextArea rows={3} placeholder="描述复用过程和效果..." />
          </Form.Item>

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => {
                setReuseModalVisible(false);
                reuseForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                提交
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EngineerKnowledge;
