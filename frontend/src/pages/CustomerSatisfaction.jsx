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

import { serviceApi } from '@/services/api/service';

const { Title, Text, Paragraph } = Typography;
// Using Tabs items prop instead of TabPane
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

  // 满意度趋势数据
  const [trendData, setTrendData] = useState({ direction: 'up', percentage: 0 });

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [satisfactionRes, statsRes] = await Promise.all([
        serviceApi.satisfaction.list(),
        serviceApi.satisfaction.statistics().catch(() => ({ data: {} })),
      ]);
      const satisfactionList = satisfactionRes.data?.items || satisfactionRes.data?.items || satisfactionRes.data || [];
      // 将满意度记录映射为 surveys 和 responses 格式
      const surveyItems = satisfactionList.map((item) => ({
        id: item.id,
        title: item.title || item.survey_title || `满意度调查 #${item.id}`,
        type: item.type || item.survey_type || 'service',
        status: item.status || 'active',
        createdDate: item.created_at || item.createdDate || '',
        completedDate: item.completed_at || item.completedDate || '',
        avgScore: item.avg_score ?? item.avgScore ?? 0,
        responseCount: item.response_count ?? item.responseCount ?? 0,
        targetCount: item.target_count ?? item.targetCount ?? 100,
      }));
      const responseItems = satisfactionList
        .filter((item) => item.feedback || item.satisfaction_level != null)
        .map((item) => ({
          id: item.id,
          surveyId: item.survey_id ?? item.id,
          customerName: item.customer_name || item.customerName || '',
          satisfactionLevel: item.satisfaction_level ?? item.satisfactionLevel ?? item.score ?? 0,
          feedback: item.feedback || item.comment || '',
          category: item.category || 'service',
          createdDate: item.created_at || item.createdDate || '',
        }));
      setSurveys(surveyItems);
      setResponses(responseItems);
      const stats = statsRes.data || {};
      setTrendData({
        direction: stats.trend_direction || 'up',
        percentage: stats.trend_percentage ?? 0,
      });
    } catch (_error) {
      message.error('加载数据失败');
    } finally {
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
      // Note: satisfaction API may not have delete; remove locally for now
      setSurveys(surveys.filter((s) => s.id !== surveyId));
      message.success('删除成功');
    } catch (_error) {
      message.error('删除失败');
    } finally {
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
        style={{ marginBottom: '24px' }}
        items={[
          {
            key: 'overview',
            label: <span><BarChart3 size={16} /> 概览分析</span>,
            children: <CustomerSatisfactionOverview data={{ surveys, responses, trend: trendData }} loading={loading} onRefresh={loadData} />,
          },
          {
            key: 'surveys',
            label: <span><FileText size={16} /> 调查管理</span>,
            children: <SurveyManager surveys={filteredSurveys} loading={loading} onCreate={handleCreateSurvey} onEdit={handleEditSurvey} onDelete={handleDeleteSurvey} />,
          },
          {
            key: 'analytics',
            label: <span><PieChart size={16} /> 满意度分析</span>,
            children: <SatisfactionAnalytics surveys={surveys} responses={filteredResponses} loading={loading} />,
          },
          {
            key: 'feedback',
            label: <span><MessageSquare size={16} /> 反馈管理</span>,
            children: <FeedbackManager responses={filteredResponses} loading={loading} onRefresh={loadData} />,
          },
          {
            key: 'templates',
            label: <span><Settings size={16} /> 问卷模板</span>,
            children: <SurveyTemplates loading={loading} onUseTemplate={handleCreateSurvey} />,
          },
        ]}
      />

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