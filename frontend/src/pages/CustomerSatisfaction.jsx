/**
 * Customer Satisfaction Survey (Refactored)
 * 客户满意度调查 - 客服工程师高级功能 (重构版本)
 */

import { useState, useMemo, useEffect, useCallback as _useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Filter,
  Eye,
  Send,
  Star,
  TrendingUp,
  TrendingDown,
  Calendar,
  User,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Download,
  BarChart3,
  PieChart,
  FileText,
  Settings,
  MessageSquare,
  ThumbsUp,
  ThumbsDown } from
"lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Rate,
  Progress,
  Tabs,
  Modal,
  Form,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Divider,
  List,
  Avatar,
  Typography,
  Alert,
  Badge,
  Dropdown,
  Menu,
  Switch,
  Radio,
  Checkbox,
  Upload,
  message,
  Spin } from
"antd";

// 导入拆分后的组件
import {
  CustomerSatisfactionOverview,
  SurveyManager,
  SatisfactionAnalytics,
  FeedbackManager,
  SurveyTemplates } from
'../components/customer-satisfaction';

import {
  SATISFACTION_LEVELS,
  SURVEY_STATUS,
  SURVEY_TYPES,
  QUESTION_TYPES,
  ANALYSIS_PERIODS,
  FEEDBACK_CATEGORIES,
  CHART_COLORS,
  EXPORT_FORMATS,
  DEFAULT_FILTERS,
  TABLE_CONFIG } from
'@/lib/constants/customer';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const CustomerSatisfaction = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [surveys, setSurveys] = useState([]);
  const [responses, setResponses] = useState([]);
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, _setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, _setSearchText] = useState('');
  const [_showCreateModal, setShowCreateModal] = useState(false);
  const [_showTemplateModal, _setShowTemplateModal] = useState(false);
  const [_editingSurvey, setEditingSurvey] = useState(null);

  // 模拟数据
  const mockData = {
    surveys: [
    {
      id: 1,
      title: '客户服务满意度调查',
      type: 'service',
      status: 'active',
      createdDate: '2024-01-15',
      completedDate: '2024-01-20',
      avgScore: 4.2,
      responseCount: 156,
      targetCount: 200
    }
    // 更多模拟数据...
    ],
    responses: [
    {
      id: 1,
      surveyId: 1,
      customerName: '张三',
      satisfactionLevel: 4,
      feedback: '服务质量很好，响应及时',
      category: 'service',
      createdDate: '2024-01-18'
    }
    // 更多模拟数据...
    ]
  };

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      setTimeout(() => {
        setSurveys(mockData.surveys);
        setResponses(mockData.responses);
        setLoading(false);
      }, 1000);
    } catch (_error) {
      message.error('加载数据失败');
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredSurveys = useMemo(() => {
    return surveys.filter((survey) => {
      const searchLower = (searchText || "").toLowerCase();
    const matchesSearch = (survey.title || "").toLowerCase().includes(searchLower);
      const matchesType = !filters.surveyType || survey.type === filters.surveyType;
      const matchesStatus = !filters.status || survey.status === filters.status;

      return matchesSearch && matchesType && matchesStatus;
    });
  }, [surveys, searchText, filters]);

  const filteredResponses = useMemo(() => {
    return responses.filter((response) => {
      const matchesLevel = !filters.satisfactionLevel || response.satisfactionLevel === filters.satisfactionLevel;
      const matchesCategory = !filters.category || response.category === filters.category;

      return matchesLevel && matchesCategory;
    });
  }, [responses, filters]);

  // 事件处理
  const handleCreateSurvey = () => {
    setShowCreateModal(true);
  };

  const handleEditSurvey = (survey) => {
    setEditingSurvey(survey);
    setShowCreateModal(true);
  };

  const handleDeleteSurvey = async (surveyId) => {
    try {
      setLoading(true);
      // 模拟删除API调用
      setTimeout(() => {
        setSurveys(surveys.filter((s) => s.id !== surveyId));
        message.success('删除成功');
        setLoading(false);
      }, 500);
    } catch (_error) {
      message.error('删除失败');
      setLoading(false);
    }
  };

  const handleExportData = (format) => {
    message.success(`正在导出${format.label}格式数据...`);
  };

  // 表格列配置
  const _surveyColumns = [
  {
    title: '调查标题',
    dataIndex: 'title',
    key: 'title',
    render: (text, record) =>
    <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {SURVEY_TYPES[record.type?.toUpperCase()]?.label}
          </div>
    </div>

  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status) => {
      const config = SURVEY_STATUS[status?.toUpperCase()];
      return <Tag color={config?.color}>{config?.label}</Tag>;
    }
  },
  {
    title: '平均评分',
    dataIndex: 'avgScore',
    key: 'avgScore',
    render: (score) =>
    <div>
          <Rate disabled value={score} style={{ fontSize: 14 }} />
          <div style={{ fontSize: 12, color: '#666' }}>{score}/5.0</div>
    </div>

  },
  {
    title: '响应情况',
    key: 'responses',
    render: (_, record) =>
    <div>
          <Progress
        percent={(record.responseCount / record.targetCount * 100).toFixed(1)}
        size="small" />

          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            {record.responseCount}/{record.targetCount}
          </div>
    </div>

  },
  {
    title: '操作',
    key: 'actions',
    render: (_, record) =>
    <Space>
          <Button
        type="link"
        icon={<Eye size={16} />}
        onClick={() => setSelectedSurvey(record)}>

            查看
          </Button>
          <Button
        type="link"
        icon={<FileText size={16} />}
        onClick={() => handleEditSurvey(record)}>

            编辑
          </Button>
          <Button
        type="link"
        danger
        icon={<XCircle size={16} />}
        onClick={() => handleDeleteSurvey(record.id)}>

            删除
          </Button>
    </Space>

  }];


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="customer-satisfaction-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <MessageSquare className="inline-block mr-2" />
              客户满意度管理
            </Title>
            <Text type="secondary">
              创建、管理和分析客户满意度调查，提升服务质量
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<Plus size={16} />}
              onClick={handleCreateSurvey}>

              创建调查
            </Button>
            <Button
              icon={<RefreshCw size={16} />}
              onClick={loadData}>

              刷新
            </Button>
            <Dropdown
              overlay={
              <Menu>
                  {Object.values(EXPORT_FORMATS).map((format) =>
                <Menu.Item
                  key={format.value}
                  onClick={() => handleExportData(format)}>

                      <Download size={14} className="mr-2" />
                      导出{format.label}
                </Menu.Item>
                )}
              </Menu>
              }>

              <Button icon={<Download size={16} />}>
                导出数据
              </Button>
            </Dropdown>
          </Space>
        </div>
      </div>

      {/* 主要内容区域 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        style={{ marginBottom: '24px' }}>

        <TabPane
          tab={
          <span>
              <BarChart3 size={16} />
              概览分析
          </span>
          }
          key="overview">

          <CustomerSatisfactionOverview
            data={{ surveys, responses, trend: { direction: 'up', percentage: 5.2 } }}
            loading={loading}
            onRefresh={loadData} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <FileText size={16} />
              调查管理
          </span>
          }
          key="surveys">

          <SurveyManager
            surveys={filteredSurveys}
            loading={loading}
            onCreate={handleCreateSurvey}
            onEdit={handleEditSurvey}
            onDelete={handleDeleteSurvey} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <PieChart size={16} />
              满意度分析
          </span>
          }
          key="analytics">

          <SatisfactionAnalytics
            surveys={surveys}
            responses={filteredResponses}
            loading={loading} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <MessageSquare size={16} />
              反馈管理
          </span>
          }
          key="feedback">

          <FeedbackManager
            responses={filteredResponses}
            loading={loading}
            onRefresh={loadData} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <Settings size={16} />
              问卷模板
          </span>
          }
          key="templates">

          <SurveyTemplates
            loading={loading}
            onUseTemplate={handleCreateSurvey} />

        </TabPane>
      </Tabs>

      {/* 调查详情模态框 */}
      <Modal
        title="调查详情"
        visible={!!selectedSurvey}
        onCancel={() => setSelectedSurvey(null)}
        footer={null}
        width={1000}>

        {selectedSurvey &&
        <div>
            <Title level={4}>{selectedSurvey.title}</Title>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic title="平均评分" value={selectedSurvey.avgScore} suffix="/5.0" />
              </Col>
              <Col span={8}>
                <Statistic title="响应人数" value={selectedSurvey.responseCount} />
              </Col>
              <Col span={8}>
                <Statistic title="完成率" value={(selectedSurvey.responseCount / selectedSurvey.targetCount * 100).toFixed(1)} suffix="%" />
              </Col>
            </Row>
        </div>
        }
      </Modal>
    </motion.div>);

};

export default CustomerSatisfaction;