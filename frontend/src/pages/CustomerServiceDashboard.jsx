/**
 * Customer Service Engineer Dashboard (Refactored)
 * 客服工程师工作台 - 客户技术支持、问题处理、现场服务、客户沟通 (重构版本)
 */

import { useState, useMemo, useEffect, useCallback as _useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Users,
  Wrench,
  FileText,
  Phone,
  MapPin,
  Calendar,
  Star,
  ChevronRight,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  MessageSquare,
  Settings,
  RefreshCw,
  Download,
  Upload,
  BarChart3,
  Headphones,
  Car,
  Shield,
  Award } from
"lucide-react";

import {
  Card,
  Table,
  Button,
  Input,
  Select,
  DatePicker,
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
  message,
  Spin,
  Tabs,
  Progress,
  Timeline,
  Rate,
  InputNumber,
  Steps } from
"antd";

// 导入拆分后的组件
import {
  ServiceOverview,
  TicketManager,
  FieldServiceManager,
  WarrantyManager,
  SatisfactionTracker } from
'../components/customer-service';

import {
  SERVICE_TYPES,
  TICKET_STATUS,
  PRIORITY_LEVELS,
  SATISFACTION_LEVELS,
  SERVICE_PHASES,
  RESPONSE_CHANNELS,
  RESOLUTION_METHODS,
  WARRANTY_TYPES,
  PERFORMANCE_METRICS,
  ESCALATION_LEVELS,
  TABLE_CONFIG,
  CHART_COLORS,
  DEFAULT_FILTERS } from
'../components/customer-service/customerServiceConstants';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { TextArea } = Input;
const { Step } = Steps;

const CustomerServiceDashboard = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [tickets, setTickets] = useState([]);
  const [fieldServices, setFieldServices] = useState([]);
  const [warrantyProjects, setWarrantyProjects] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, setSearchText] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 模拟数据
  const mockData = {
    tickets: [
    {
      id: 1,
      title: '光伏系统故障排查',
      customerName: '绿色能源公司',
      description: '光伏系统突然停止工作，需要紧急排查故障原因',
      serviceType: 'technical_support',
      status: 'in_progress',
      priority: 'critical',
      engineer: '张工程师',
      createdAt: '2024-01-18 09:30',
      updatedAt: '2024-01-18 14:20',
      responseTime: 0.5,
      resolvedDate: null,
      satisfaction: null
    }
    // 更多模拟数据...
    ],
    fieldServices: [
    {
      id: 1,
      ticketId: 1,
      title: '现场设备检修',
      customerName: '绿色能源公司',
      location: '北京市海淀区XX园区',
      servicePhase: 's8',
      scheduledDate: '2024-01-20',
      engineer: '李工程师',
      status: 'scheduled',
      description: '现场检修光伏逆变器设备'
    }],

    warrantyProjects: [
    {
      id: 1,
      projectName: '绿色能源光伏项目',
      customerName: '绿色能源公司',
      warrantyType: 'standard',
      startDate: '2023-01-15',
      endDate: '2025-01-14',
      status: 'active',
      remainingDays: 362,
      totalClaims: 2,
      resolvedClaims: 1
    }],

    metrics: {
      avgResponseTime: 2.5,
      avgSatisfaction: 4.2,
      slaAchievement: 94.5,
      firstContactResolution: 78.5
    },
    activities: [
    {
      id: 1,
      type: 'resolved',
      title: '工单 #1001 已解决',
      description: '客户对服务结果表示满意',
      engineer: '张工程师',
      timestamp: '2024-01-18 15:30'
    }]

  };

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      setTimeout(() => {
        setTickets(mockData.tickets);
        setFieldServices(mockData.fieldServices);
        setWarrantyProjects(mockData.warrantyProjects);
        setLoading(false);
      }, 1000);
    } catch (_error) {
      message.error('加载数据失败');
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredTickets = useMemo(() => {
    return tickets.filter((ticket) => {
      const matchesSearch = !searchText ||
      ticket.title.toLowerCase().includes(searchText.toLowerCase()) ||
      ticket.customerName?.toLowerCase().includes(searchText.toLowerCase());

      const matchesStatus = !filters.status || ticket.status === filters.status;
      const matchesPriority = !filters.priority || ticket.priority === filters.priority;
      const matchesType = !filters.serviceType || ticket.serviceType === filters.serviceType;

      return matchesSearch && matchesStatus && matchesPriority && matchesType;
    });
  }, [tickets, searchText, filters]);

  // 事件处理
  const handleCreateTicket = () => {
    setShowCreateModal(true);
  };

  const handleEditTicket = (ticket) => {
    setSelectedTicket(ticket);
    setShowCreateModal(true);
  };

  const handleResolveTicket = async (ticketId) => {
    try {
      setLoading(true);
      // 模拟解决API调用
      setTimeout(() => {
        setTickets(tickets.map((t) =>
        t.id === ticketId ?
        { ...t, status: 'resolved', resolvedDate: new Date().toISOString().split('T')[0] } :
        t
        ));
        message.success('工单已标记为解决');
        setLoading(false);
      }, 500);
    } catch (_error) {
      message.error('操作失败');
      setLoading(false);
    }
  };

  const handleEscalateTicket = async (ticket) => {
    message.success(`工单 ${ticket.title} 已升级处理`);
  };

  const handleAssignTicket = async (ticket, engineer) => {
    try {
      setLoading(true);
      // 模拟分配API调用
      setTimeout(() => {
        setTickets(tickets.map((t) =>
        t.id === ticket.id ? { ...t, engineer, status: 'in_progress' } : t
        ));
        message.success('工单分配成功');
        setLoading(false);
      }, 500);
    } catch (_error) {
      message.error('分配失败');
      setLoading(false);
    }
  };

  // 表格列配置
  const _ticketColumns = [
  {
    title: '工单信息',
    key: 'info',
    render: (_, record) =>
    <div>
          <div style={{ fontWeight: 'bold', cursor: 'pointer' }}>
            <AlertCircle size={16} /> {record.title}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            <Users size={12} /> {record.customerName}
          </div>
        </div>

  },
  {
    title: '服务类型',
    dataIndex: 'serviceType',
    key: 'serviceType',
    render: (type) => {
      const config = SERVICE_TYPES[type?.toUpperCase()];
      return (
        <Tag color={config?.color}>
            {config?.icon} {config?.label}
          </Tag>);

    }
  },
  {
    title: '状态',
    key: 'status',
    render: (_, record) =>
    <div>
          <Tag color={TICKET_STATUS[record.status?.toUpperCase()]?.color}>
            {TICKET_STATUS[record.status?.toUpperCase()]?.label}
          </Tag>
          {record.engineer &&
      <div style={{ fontSize: 11, color: '#999', marginTop: 4 }}>
              负责人: {record.engineer}
            </div>
      }
        </div>

  },
  {
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority',
    render: (priority) => {
      const config = PRIORITY_LEVELS[priority?.toUpperCase()];
      return (
        <Tag color={config?.color}>
            {config?.label}
          </Tag>);

    }
  },
  {
    title: '响应时间',
    key: 'response',
    render: (_, record) =>
    <div>
          <div style={{ fontSize: 12 }}>
            <Clock size={12} /> {record.responseTime}小时
          </div>
          <div style={{ fontSize: 11, color: '#666' }}>
            创建: {record.createdAt}
          </div>
        </div>

  },
  {
    title: '满意度',
    dataIndex: 'satisfaction',
    key: 'satisfaction',
    render: (satisfaction) =>
    satisfaction ?
    <div>
            <Rate disabled value={satisfaction} style={{ fontSize: 12 }} />
            <div style={{ fontSize: 11, color: '#666', marginTop: 4 }}>
              {satisfaction}/5.0
            </div>
          </div> :

    <span style={{ color: '#999' }}>未评价</span>


  },
  {
    title: '操作',
    key: 'actions',
    render: (_, record) =>
    <Space>
          <Button
        type="link"
        icon={<Eye size={16} />}
        onClick={() => setSelectedTicket(record)}>

            查看
          </Button>
          <Button
        type="link"
        icon={<Edit size={16} />}
        onClick={() => handleEditTicket(record)}>

            编辑
          </Button>
          {record.status !== 'resolved' &&
      <Button
        type="link"
        icon={<CheckCircle2 size={16} />}
        onClick={() => handleResolveTicket(record.id)}>

              解决
            </Button>
      }
          <Dropdown
        overlay={
        <Menu>
                <Menu.Item onClick={() => handleEscalateTicket(record)}>
                  <TrendingUp size={14} /> 升级处理
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item onClick={() => handleAssignTicket(record, '张工程师')}>
                  <Users size={14} /> 分配给张工程师
                </Menu.Item>
                <Menu.Item onClick={() => handleAssignTicket(record, '李工程师')}>
                  <Users size={14} /> 分配给李工程师
                </Menu.Item>
              </Menu>
        }>

            <Button type="link" icon={<Settings size={16} />}>
              更多
            </Button>
          </Dropdown>
        </Space>

  }];


  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="customer-service-dashboard"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>

      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <Headphones className="inline-block mr-2" />
              客服工程师工作台
            </Title>
            <Text type="secondary">
              客户技术支持、问题处理、现场服务、客户沟通
            </Text>
          </div>
          <Space>
            <Button
              type="primary"
              icon={<Plus size={16} />}
              onClick={handleCreateTicket}>

              创建工单
            </Button>
            <Button
              icon={<RefreshCw size={16} />}
              onClick={loadData}>

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
              placeholder="搜索工单标题、客户名称..."
              prefix={<Search size={16} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear />

          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Select
                placeholder="状态"
                value={filters.status}
                onChange={(value) => setFilters({ ...filters, status: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(TICKET_STATUS).map((status) =>
                <Select.Option key={status.value} value={status.value}>
                    <Tag color={status.color}>{status.label}</Tag>
                  </Select.Option>
                )}
              </Select>
              <Select
                placeholder="优先级"
                value={filters.priority}
                onChange={(value) => setFilters({ ...filters, priority: value })}
                style={{ width: 100 }}
                allowClear>

                {Object.values(PRIORITY_LEVELS).map((priority) =>
                <Select.Option key={priority.value} value={priority.value}>
                    <Tag color={priority.color}>{priority.label}</Tag>
                  </Select.Option>
                )}
              </Select>
              <Select
                placeholder="服务类型"
                value={filters.serviceType}
                onChange={(value) => setFilters({ ...filters, serviceType: value })}
                style={{ width: 150 }}
                allowClear>

                {Object.values(SERVICE_TYPES).map((type) =>
                <Select.Option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                  </Select.Option>
                )}
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

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

          <ServiceOverview
            data={mockData}
            loading={loading}
            onNavigate={(type) => {
              if (type === 'urgent') {
                setFilters({ ...filters, priority: 'critical' });
                setActiveTab('tickets');
              } else if (type === 'field-service') {
                setActiveTab('field-service');
              } else if (type === 'warranty') {
                setActiveTab('warranty');
              } else if (type === 'satisfaction') {
                setActiveTab('satisfaction');
              } else if (type === 'create-ticket') {
                handleCreateTicket();
              } else if (type === 'activities') {
                setActiveTab('tickets');
              } else if (type === 'performance') {
                setActiveTab('overview');
              }
            }} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <FileText size={16} />
              工单管理 ({filteredTickets.length})
            </span>
          }
          key="tickets">

          <TicketManager
            tickets={filteredTickets}
            loading={loading}
            onEdit={handleEditTicket}
            onResolve={handleResolveTicket}
            onEscalate={handleEscalateTicket} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <Car size={16} />
              现场服务 ({fieldServices.length})
            </span>
          }
          key="field-service">

          <FieldServiceManager
            services={fieldServices}
            loading={loading}
            onRefresh={loadData} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <Shield size={16} />
              质保管理 ({warrantyProjects.length})
            </span>
          }
          key="warranty">

          <WarrantyManager
            projects={warrantyProjects}
            loading={loading} />

        </TabPane>

        <TabPane
          tab={
          <span>
              <Star size={16} />
              满意度跟踪
            </span>
          }
          key="satisfaction">

          <SatisfactionTracker
            tickets={tickets}
            loading={loading} />

        </TabPane>
      </Tabs>

      {/* 工单创建/编辑模态框 */}
      <Modal
        title={selectedTicket ? '编辑工单' : '创建工单'}
        open={showCreateModal}
        onCancel={() => {
          setShowCreateModal(false);
          setSelectedTicket(null);
        }}
        footer={null}
        width={800}>

        <Form layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="工单标题" required>
                <Input placeholder="请输入工单标题" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="客户名称" required>
                <Input placeholder="请输入客户名称" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="服务类型" required>
                <Select placeholder="选择服务类型">
                  {Object.values(SERVICE_TYPES).map((type) =>
                  <Select.Option key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </Select.Option>
                  )}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="优先级" required>
                <Select placeholder="选择优先级">
                  {Object.values(PRIORITY_LEVELS).map((priority) =>
                  <Select.Option key={priority.value} value={priority.value}>
                      <Tag color={priority.color}>{priority.label}</Tag>
                    </Select.Option>
                  )}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="联系方式">
                <Input placeholder="联系电话" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="问题描述" required>
            <TextArea rows={4} placeholder="请详细描述问题..." />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" onClick={() => {
                message.success('工单创建成功');
                setShowCreateModal(false);
                loadData();
              }}>
                提交
              </Button>
              <Button onClick={() => setShowCreateModal(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </motion.div>);

};

export default CustomerServiceDashboard;