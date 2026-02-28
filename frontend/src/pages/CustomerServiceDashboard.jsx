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
'../lib/constants/service';

import { serviceApi } from '@/services/api/service';

const { Title, Text, Paragraph } = Typography;
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

  // 仪表盘聚合数据
  const [overviewData, setOverviewData] = useState({
    tickets: [], fieldServices: [], warrantyProjects: [],
    metrics: { avgResponseTime: 0, avgSatisfaction: 0, slaAchievement: 0, firstContactResolution: 0 },
    activities: [],
  });

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ticketsRes, recordsRes, dashRes] = await Promise.all([
        serviceApi.tickets.list({ status: filters.status, priority: filters.priority, service_type: filters.serviceType }),
        serviceApi.records.list(),
        serviceApi.dashboardStatistics().catch(() => ({ data: {} })),
      ]);
      const ticketList = (ticketsRes.data?.items || ticketsRes.data?.items || ticketsRes.data || []).map((t) => ({
        id: t.id,
        title: t.title || t.subject || '',
        customerName: t.customer_name || t.customerName || '',
        description: t.description || '',
        serviceType: t.service_type || t.serviceType || '',
        status: t.status || '',
        priority: t.priority || '',
        engineer: t.engineer || t.assigned_to || '',
        createdAt: t.created_at || t.createdAt || '',
        updatedAt: t.updated_at || t.updatedAt || '',
        responseTime: t.response_time ?? t.responseTime ?? 0,
        resolvedDate: t.resolved_at || t.resolvedDate || null,
        satisfaction: t.satisfaction ?? null,
      }));
      setTickets(ticketList);

      const recordList = (recordsRes.data?.items || recordsRes.data?.items || recordsRes.data || []).map((r) => ({
        id: r.id,
        ticketId: r.ticket_id || r.ticketId,
        title: r.title || r.subject || '',
        customerName: r.customer_name || r.customerName || '',
        location: r.location || r.address || '',
        servicePhase: r.service_phase || r.servicePhase || '',
        scheduledDate: r.scheduled_date || r.scheduledDate || '',
        engineer: r.engineer || r.assigned_to || '',
        status: r.status || '',
        description: r.description || '',
      }));
      setFieldServices(recordList);

      const db = dashRes.data || {};
      const warrantyList = db.warranty_projects || db.warrantyProjects || [];
      setWarrantyProjects((warrantyList || []).map((w) => ({
        id: w.id,
        projectName: w.project_name || w.projectName || '',
        customerName: w.customer_name || w.customerName || '',
        warrantyType: w.warranty_type || w.warrantyType || 'standard',
        startDate: w.start_date || w.startDate || '',
        endDate: w.end_date || w.endDate || '',
        status: w.status || 'active',
        remainingDays: w.remaining_days ?? w.remainingDays ?? 0,
        totalClaims: w.total_claims ?? w.totalClaims ?? 0,
        resolvedClaims: w.resolved_claims ?? w.resolvedClaims ?? 0,
      })));

      setOverviewData({
        tickets: ticketList,
        fieldServices: recordList,
        warrantyProjects: warrantyList,
        metrics: {
          avgResponseTime: db.avg_response_time ?? db.avgResponseTime ?? 0,
          avgSatisfaction: db.avg_satisfaction ?? db.avgSatisfaction ?? 0,
          slaAchievement: db.sla_achievement ?? db.slaAchievement ?? 0,
          firstContactResolution: db.first_contact_resolution ?? db.firstContactResolution ?? 0,
        },
        activities: db.activities || db.recent_activities || [],
      });
    } catch (_error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredTickets = useMemo(() => {
    return (tickets || []).filter((ticket) => {
      const searchLower = (searchText || "").toLowerCase();
    const matchesSearch = !searchText ||
      (ticket.title || "").toLowerCase().includes(searchLower) ||
      (ticket.customerName || "").toLowerCase().includes(searchLower);

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
      await serviceApi.tickets.close(ticketId, { resolution: 'resolved' });
      setTickets((tickets || []).map((t) =>
        t.id === ticketId ?
        { ...t, status: 'resolved', resolvedDate: new Date().toISOString().split('T')[0] } :
        t
      ));
      message.success('工单已标记为解决');
    } catch (_error) {
      message.error('操作失败');
    } finally {
      setLoading(false);
    }
  };

  const handleEscalateTicket = async (ticket) => {
    message.success(`工单 ${ticket.title} 已升级处理`);
  };

  const handleAssignTicket = async (ticket, engineer) => {
    try {
      setLoading(true);
      await serviceApi.tickets.assign(ticket.id, { engineer });
      setTickets((tickets || []).map((t) =>
        t.id === ticket.id ? { ...t, engineer, status: 'in_progress' } : t
      ));
      message.success('工单分配成功');
    } catch (_error) {
      message.error('分配失败');
    } finally {
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
        style={{ marginBottom: '24px' }}
        items={[
          {
            key: 'overview',
            label: (
              <span>
                <BarChart3 size={16} />
                概览分析
              </span>
            ),
            children: (
              <ServiceOverview
                data={overviewData}
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
                }}
              />
            ),
          },
          {
            key: 'tickets',
            label: (
              <span>
                <FileText size={16} />
                工单管理 ({filteredTickets.length})
              </span>
            ),
            children: (
              <TicketManager
                tickets={filteredTickets}
                loading={loading}
                onEdit={handleEditTicket}
                onResolve={handleResolveTicket}
                onEscalate={handleEscalateTicket}
              />
            ),
          },
          {
            key: 'field-service',
            label: (
              <span>
                <Car size={16} />
                现场服务 ({fieldServices.length})
              </span>
            ),
            children: (
              <FieldServiceManager
                services={fieldServices}
                loading={loading}
                onRefresh={loadData}
              />
            ),
          },
          {
            key: 'warranty',
            label: (
              <span>
                <Shield size={16} />
                质保管理 ({warrantyProjects.length})
              </span>
            ),
            children: (
              <WarrantyManager
                projects={warrantyProjects}
                loading={loading}
              />
            ),
          },
          {
            key: 'satisfaction',
            label: (
              <span>
                <Star size={16} />
                满意度跟踪
              </span>
            ),
            children: (
              <SatisfactionTracker
                tickets={tickets}
                loading={loading}
              />
            ),
          },
        ]}
      />

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