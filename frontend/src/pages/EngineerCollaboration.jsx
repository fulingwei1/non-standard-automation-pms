import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Rate, Input, Select, Tag, Space, message, Tabs } from 'antd';
import { TeamOutlined, StarOutlined, CommentOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Option } = Select;
const EngineerCollaboration = () => {
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [pendingList, setPendingList] = useState([]);
  const [receivedRatings, setReceivedRatings] = useState([]);
  const [givenRatings, setGivenRatings] = useState([]);
  const [collaborationMatrix, setCollaborationMatrix] = useState(null);
  const [form] = Form.useForm();

  // 获取待评价列表
  const fetchPendingList = async () => {
    try {
      const response = await axios.get('/api/v1/engineer-performance/collaboration/pending');
      if (response.data.code === 200) {
        setPendingList(response.data.data);
      }
    } catch (error) {
      console.error('获取待评价列表失败:', error);
    }
  };

  // 获取收到的评价
  const fetchReceivedRatings = async () => {
    setLoading(true);
    try {
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const response = await axios.get(`/api/v1/engineer-performance/collaboration/received/${currentUser.id}`);
      if (response.data.code === 200) {
        setReceivedRatings(response.data.data.items);
      }
    } catch (error) {
      console.error('获取收到的评价失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取给出的评价
  const fetchGivenRatings = async () => {
    setLoading(true);
    try {
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const response = await axios.get(`/api/v1/engineer-performance/collaboration/given/${currentUser.id}`);
      if (response.data.code === 200) {
        setGivenRatings(response.data.data.items);
      }
    } catch (error) {
      console.error('获取给出的评价失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取协作矩阵
  const fetchCollaborationMatrix = async () => {
    try {
      const response = await axios.get('/api/v1/engineer-performance/collaboration/matrix');
      if (response.data.code === 200) {
        setCollaborationMatrix(response.data.data);
      }
    } catch (error) {
      console.error('获取协作矩阵失败:', error);
    }
  };

  useEffect(() => {
    fetchPendingList();
    fetchReceivedRatings();
    fetchGivenRatings();
    fetchCollaborationMatrix();
  }, []);

  // 打开评价弹窗
  const openRatingModal = (engineer) => {
    form.setFieldsValue({
      ratee_id: engineer.user_id,
      ratee_name: engineer.user_name
    });
    setModalVisible(true);
  };

  // 提交评价
  const handleSubmit = async (values) => {
    try {
      const response = await axios.post('/api/v1/engineer-performance/collaboration', values);
      if (response.data.code === 200) {
        message.success('评价提交成功');
        setModalVisible(false);
        form.resetFields();
        fetchPendingList();
        fetchGivenRatings();
      }
    } catch (error) {
      message.error(error.response?.data?.detail || '提交失败');
    }
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

  // 待评价列表表格列
  const pendingColumns = [
    {
      title: '姓名',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
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
      render: (level) => {
        const names = { 'junior': '初级', 'intermediate': '中级', 'senior': '高级', 'expert': '专家' };
        return names[level] || level;
      }
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 150,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Button type="primary" size="small" onClick={() => openRatingModal(record)}>
          立即评价
        </Button>
      )
    }
  ];

  // 收到的评价表格列
  const receivedColumns = [
    {
      title: '评价人',
      dataIndex: 'rater_name',
      key: 'rater_name',
      width: 120,
    },
    {
      title: '岗位',
      dataIndex: 'rater_job_type',
      key: 'rater_job_type',
      width: 120,
      render: (jobType) => <Tag color="blue">{getJobTypeName(jobType)}</Tag>
    },
    {
      title: '沟通配合',
      dataIndex: 'communication_score',
      key: 'communication_score',
      width: 100,
      render: (score) => <Rate disabled value={score} count={5} />
    },
    {
      title: '响应速度',
      dataIndex: 'response_score',
      key: 'response_score',
      width: 100,
      render: (score) => <Rate disabled value={score} count={5} />
    },
    {
      title: '交付质量',
      dataIndex: 'delivery_score',
      key: 'delivery_score',
      width: 100,
      render: (score) => <Rate disabled value={score} count={5} />
    },
    {
      title: '接口规范',
      dataIndex: 'interface_score',
      key: 'interface_score',
      width: 100,
      render: (score) => <Rate disabled value={score} count={5} />
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 80,
      render: (score) => <span className="font-semibold text-blue-600">{score?.toFixed(1)}</span>
    },
    {
      title: '评价时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString() : '-'
    }
  ];

  // 给出的评价表格列
  const givenColumns = [
    {
      title: '被评价人',
      dataIndex: 'ratee_name',
      key: 'ratee_name',
      width: 120,
    },
    {
      title: '岗位',
      dataIndex: 'ratee_job_type',
      key: 'ratee_job_type',
      width: 120,
      render: (jobType) => <Tag color="blue">{getJobTypeName(jobType)}</Tag>
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 80,
      render: (score) => <span className="font-semibold text-blue-600">{score?.toFixed(1)}</span>
    },
    {
      title: '评价时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString() : '-'
    }
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">跨部门协作评价</h1>
        <p className="text-gray-500">促进跨部门沟通与协作</p>
      </div>

      {/* 协作矩阵 */}
      {collaborationMatrix && (
        <Card title="部门协作评分矩阵" className="mb-6">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr>
                  <th className="px-4 py-2 bg-gray-50">评价人 \ 被评价人</th>
                  <th className="px-4 py-2 bg-gray-50">机械部</th>
                  <th className="px-4 py-2 bg-gray-50">测试部</th>
                  <th className="px-4 py-2 bg-gray-50">电气部</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(collaborationMatrix.matrix || {}).map(([raterType, scores]) => (
                  <tr key={raterType}>
                    <td className="px-4 py-2 font-semibold">{getJobTypeName(raterType)}</td>
                    <td className="px-4 py-2 text-center">
                      {scores.mechanical ? (
                        <span className={`font-semibold ${
                          scores.mechanical >= 80 ? 'text-green-600' :
                          scores.mechanical >= 60 ? 'text-blue-600' : 'text-orange-600'
                        }`}>
                          {scores.mechanical.toFixed(1)}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {scores.test ? (
                        <span className={`font-semibold ${
                          scores.test >= 80 ? 'text-green-600' :
                          scores.test >= 60 ? 'text-blue-600' : 'text-orange-600'
                        }`}>
                          {scores.test.toFixed(1)}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {scores.electrical ? (
                        <span className={`font-semibold ${
                          scores.electrical >= 80 ? 'text-green-600' :
                          scores.electrical >= 60 ? 'text-blue-600' : 'text-orange-600'
                        }`}>
                          {scores.electrical.toFixed(1)}
                        </span>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* 待评价列表 */}
      <Card
        title={
          <Space>
            <TeamOutlined />
            <span>待评价工程师</span>
            <Tag color="orange">{pendingList.length}</Tag>
          </Space>
        }
        className="mb-6"
      >
        <Table
          columns={pendingColumns}
          dataSource={pendingList}
          rowKey="user_id"
          pagination={false}
        />
      </Card>

      {/* 评价记录 */}
      <Card>
        <Tabs
          defaultActiveKey="received"
          items={[
            {
              key: 'received',
              label: `收到的评价 (${receivedRatings.length})`,
              children: (
                <Table
                  columns={receivedColumns}
                  dataSource={receivedRatings}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                />
              ),
            },
            {
              key: 'given',
              label: `给出的评价 (${givenRatings.length})`,
              children: (
                <Table
                  columns={givenColumns}
                  dataSource={givenRatings}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                />
              ),
            },
          ]}
        />
      </Card>

      {/* 评价弹窗 */}
      <Modal
        title="跨部门协作评价"
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
          <Form.Item name="ratee_id" hidden>
            <Input />
          </Form.Item>

          <Form.Item label="被评价人" name="ratee_name">
            <Input disabled />
          </Form.Item>

          <Form.Item
            label="沟通配合"
            name="communication_score"
            rules={[{ required: true, message: '请评分' }]}
            extra="评价与该工程师的日常沟通配合情况"
          >
            <Rate count={5} />
          </Form.Item>

          <Form.Item
            label="响应速度"
            name="response_score"
            rules={[{ required: true, message: '请评分' }]}
            extra="评价对需求和问题的响应速度"
          >
            <Rate count={5} />
          </Form.Item>

          <Form.Item
            label="交付质量"
            name="delivery_score"
            rules={[{ required: true, message: '请评分' }]}
            extra="评价交付内容的质量和完整性"
          >
            <Rate count={5} />
          </Form.Item>

          <Form.Item
            label="接口规范"
            name="interface_score"
            rules={[{ required: true, message: '请评分' }]}
            extra="评价接口定义、文档等规范性"
          >
            <Rate count={5} />
          </Form.Item>

          <Form.Item
            label="评价备注"
            name="comment"
            extra="可选，提供具体的评价意见"
          >
            <TextArea rows={4} placeholder="请输入评价备注..." />
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
                提交评价
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EngineerCollaboration;
