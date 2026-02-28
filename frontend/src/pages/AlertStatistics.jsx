/**
 * Alert Statistics (Refactored)
 * 告警统计分析页面 (重构版本)
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Calendar,
  Download,
  Filter,
  FileText,
  RefreshCw,
  Settings,
  Shield,
  Activity,
  Eye,
  Edit } from
"lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
  Typography,
  Alert,
  Spin,
  Tabs,
  Progress,
  Badge,
  Radio,
  Modal,
  Form,
  message } from
"antd";

// 导入拆分后的组件
import {
  AlertOverview,
  AlertTrendAnalysis,
  AlertDistribution,
  AlertPerformance,
  AlertDetails } from
'../components/alert-statistics';

import { CheckCircle } from "lucide-react";
import {
  ALERT_TYPES,
  ALERT_LEVELS,
  ALERT_STATUS,
  TIME_PERIODS,
  STATISTICS_METRICS,
  CHART_TYPES,
  EXPORT_FORMATS,
  FILTER_CATEGORIES,
  TABLE_CONFIG,
  CHART_COLORS,
  DEFAULT_FILTERS,
  DASHBOARD_LAYOUTS } from
'@/lib/constants/alert';

import { alertApi } from '@/services/api/alerts';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const AlertStatistics = () => {
  const [_selectedAlert, setSelectedAlert] = useState(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingAlert, setEditingAlert] = useState(null);
  const [editLoading, setEditLoading] = useState(false);
  const [editForm] = Form.useForm();

  const handleEditAlert = (alert) => {
    setEditingAlert(alert);
    editForm.setFieldsValue({
      title: alert.title,
      description: alert.description,
      type: alert.type,
      level: alert.level,
      status: alert.status,
    });
    setEditModalVisible(true);
  };

  const handleEditSubmit = async () => {
    try {
      const values = await editForm.validateFields();
      setEditLoading(true);
      await alertApi.rules.update(editingAlert.id, values);
      message.success("告警规则更新成功");
      setEditModalVisible(false);
      setEditingAlert(null);
      editForm.resetFields();
      loadData();
    } catch (error) {
      if (error.errorFields) return; // form validation error
      message.error("更新告警规则失败");
    } finally {
      setEditLoading(false);
    }
  };
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [_selectedLayout, _setSelectedLayout] = useState('grid');
  const [searchText, setSearchText] = useState('');

  // API数据
  const [dashboardData, setDashboardData] = useState({
    alerts: [],
    metrics: { avgResolutionTime: 0, escalationRate: 0, falsePositiveRate: 0 },
    trend: { direction: 'down', percentage: 0 }
  });

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [alertsRes, dashboardRes] = await Promise.all([
        alertApi.list({ type: filters.type, level: filters.level, status: filters.status }),
        alertApi.dashboard(),
      ]);
      const alertsList = alertsRes.data?.items || alertsRes.data?.items || alertsRes.data || [];
      setAlerts(alertsList);
      const db = dashboardRes.data || {};
      setDashboardData({
        alerts: alertsList,
        metrics: {
          avgResolutionTime: db.avg_resolution_time ?? db.avgResolutionTime ?? 0,
          escalationRate: db.escalation_rate ?? db.escalationRate ?? 0,
          falsePositiveRate: db.false_positive_rate ?? db.falsePositiveRate ?? 0,
        },
        trend: {
          direction: db.trend_direction ?? db.trend?.direction ?? 'down',
          percentage: db.trend_percentage ?? db.trend?.percentage ?? 0,
        },
      });
    } catch (_error) {
      message.error('加载告警数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredAlerts = useMemo(() => {
    return (alerts || []).filter((alert) => {
      const searchLower = (searchText || "").toLowerCase();
    const matchesSearch = !searchText ||
      (alert.title || "").toLowerCase().includes(searchLower) ||
      (alert.description || "").toLowerCase().includes(searchLower);

      const matchesType = !filters.type || alert.type === filters.type;
      const matchesLevel = !filters.level || alert.level === filters.level;
      const matchesStatus = !filters.status || alert.status === filters.status;

      return matchesSearch && matchesType && matchesLevel && matchesStatus;
    });
  }, [alerts, searchText, filters]);

  // 事件处理
  const _handleExport = (format) => {
    message.success(`正在导出${format.label}格式报告...`);
  };

  const handleRefresh = () => {
    loadData();
  };

  const handleConfigureRules = () => {
    setActiveTab('details');
  };

  // 表格列配置
  const _alertColumns = [
  {
    title: '告警信息',
    key: 'info',
    render: (_, record) =>
    <div>
          <div style={{ fontWeight: 'bold', cursor: 'pointer' }}>
            <AlertTriangle size={16} style={{ marginRight: 8 }} />
            {record.title}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            {record.description?.substring(0, 60)}...
          </div>
          <div style={{ marginTop: 8 }}>
            {record.tags?.map((tag) =>
        <Tag key={tag} size="small" style={{ marginRight: 4 }}>
                {tag}
        </Tag>
        )}
          </div>
    </div>

  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    render: (type) => {
      const config = ALERT_TYPES[type?.toUpperCase()];
      return (
        <Tag color={config?.color}>
            {config?.icon} {config?.label}
        </Tag>);

    }
  },
  {
    title: '级别',
    dataIndex: 'level',
    key: 'level',
    render: (level) => {
      const config = ALERT_LEVELS[level?.toUpperCase()];
      return (
        <Tag color={config?.color}>
            {config?.label}
        </Tag>);

    }
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status) => {
      const config = ALERT_STATUS[status?.toUpperCase()];
      return (
        <Tag color={config?.color}>
            {config?.label}
        </Tag>);

    }
  },
  {
    title: '来源',
    dataIndex: 'source',
    key: 'source',
    render: (source) =>
    <Text code style={{ fontSize: 12 }}>{source}</Text>

  },
  {
    title: '时间',
    key: 'time',
    render: (_, record) =>
    <div>
          <div style={{ fontSize: 12 }}>
            <Calendar size={12} /> 创建: {record.createdAt}
          </div>
          {record.resolvedAt &&
      <div style={{ fontSize: 12, color: '#52c41a' }}>
              <CheckCircle size={12} /> 解决: {record.resolvedAt}
      </div>
      }
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
        onClick={() => setSelectedAlert(record)}>

            查看
          </Button>
          {record.status === 'active' &&
      <Button
        type="link"
        icon={<Edit size={16} />}
        onClick={() => handleEditAlert(record)}>

              处理
      </Button>
      }
    </Space>

  }];


  const tabItems = [
  {
    key: 'overview',
    tab:
    <span>
          <BarChart3 size={16} />
          概览分析
    </span>,

    content: <AlertOverview data={dashboardData} loading={loading} onNavigate={setActiveTab} />
  },
  {
    key: 'trend',
    tab:
    <span>
          <TrendingUp size={16} />
          趋势分析
    </span>,

    content: <AlertTrendAnalysis alerts={filteredAlerts} loading={loading} />
  },
  {
    key: 'distribution',
    tab:
    <span>
          <Filter size={16} />
          分布分析
    </span>,

    content: <AlertDistribution alerts={filteredAlerts} loading={loading} />
  },
  {
    key: 'performance',
    tab:
    <span>
          <Activity size={16} />
          性能指标
    </span>,

    content: <AlertPerformance data={dashboardData} loading={loading} />
  },
  {
    key: 'details',
    tab:
    <span>
          <FileText size={16} />
          详细列表 ({filteredAlerts.length})
    </span>,

    content: <AlertDetails alerts={filteredAlerts} loading={loading} />
  }];


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="alert-statistics-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <AlertTriangle className="inline-block mr-2" />
              告警统计分析
            </Title>
            <Text type="secondary">
              系统告警监控、统计分析、性能指标
            </Text>
          </div>
          <Space>
            <Button
              icon={<Shield size={16} />}
              onClick={handleConfigureRules}>

              配置规则
            </Button>
            <Button
              icon={<RefreshCw size={16} />}
              onClick={handleRefresh}>

              刷新
            </Button>
            <Button
              icon={<Download size={16} />}>

              导出报表
            </Button>
          </Space>
        </div>
      </div>

      {/* 搜索和过滤器 */}
      <Card className="mb-4">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Input
              placeholder="搜索告警标题、描述..."
              prefix={<Filter size={16} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear />

          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Select
                placeholder="告警类型"
                value={filters.type}
                onChange={(value) => setFilters({ ...filters, type: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(ALERT_TYPES).map((type) =>
                <Select.Option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="告警级别"
                value={filters.level}
                onChange={(value) => setFilters({ ...filters, level: value })}
                style={{ width: 100 }}
                allowClear>

                {Object.values(ALERT_LEVELS).map((level) =>
                <Select.Option key={level.value} value={level.value}>
                    <Tag color={level.color}>{level.label}</Tag>
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="状态"
                value={filters.status}
                onChange={(value) => setFilters({ ...filters, status: value })}
                style={{ width: 100 }}
                allowClear>

                {Object.values(ALERT_STATUS).map((status) =>
                <Select.Option key={status.value} value={status.value}>
                    <Tag color={status.color}>{status.label}</Tag>
                </Select.Option>
                )}
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 主要内容区域 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          size="large"
          items={(tabItems || []).map((item) => ({
            key: item.key,
            label: item.tab,
            children: item.content,
          }))}
        />
      </Card>

      {/* 编辑告警规则弹窗 */}
      <Modal
        title="编辑告警规则"
        open={editModalVisible}
        onOk={handleEditSubmit}
        onCancel={() => { setEditModalVisible(false); setEditingAlert(null); editForm.resetFields(); }}
        confirmLoading={editLoading}
        destroyOnClose>
        <Form form={editForm} layout="vertical">
          <Form.Item name="title" label="告警标题" rules={[{ required: true, message: '请输入告警标题' }]}>
            <Input placeholder="请输入告警标题" />
          </Form.Item>
          <Form.Item name="description" label="告警描述">
            <Input.TextArea rows={3} placeholder="请输入告警描述" />
          </Form.Item>
          <Form.Item name="type" label="告警类型">
            <Select placeholder="选择告警类型">
              {Object.values(ALERT_TYPES).map((type) =>
                <Select.Option key={type.value} value={type.value}>
                  {type.icon} {type.label}
                </Select.Option>
              )}
            </Select>
          </Form.Item>
          <Form.Item name="level" label="告警级别">
            <Select placeholder="选择告警级别">
              {Object.values(ALERT_LEVELS).map((level) =>
                <Select.Option key={level.value} value={level.value}>
                  <Tag color={level.color}>{level.label}</Tag>
                </Select.Option>
              )}
            </Select>
          </Form.Item>
          <Form.Item name="status" label="状态">
            <Select placeholder="选择状态">
              {Object.values(ALERT_STATUS).map((status) =>
                <Select.Option key={status.value} value={status.value}>
                  <Tag color={status.color}>{status.label}</Tag>
                </Select.Option>
              )}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </motion.div>);

};

export default AlertStatistics;
