/**
 * Approval Center (Refactored)
 * 审批中心页面 (重构版本)
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ClipboardCheck,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  Filter,
  FileText,
  Package,
  DollarSign,
  Users,
  Wrench,
  ChevronRight,
  MessageSquare,
  Eye,
  Check,
  X,
  RotateCcw,
  Plus,
  RefreshCw,
  Download,
  Settings
} from "lucide-react";

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
  Modal,
  Form,
  Radio,
  Checkbox,
  message
} from "antd";

// 导入拆分后的组件
import {
  ApprovalOverview,
  ApprovalList,
  ApprovalWorkflow,
  ApprovalStatistics,
  ApprovalRules
} from '../components/approval-center';

import {
  APPROVAL_TYPES,
  APPROVAL_STATUS,
  APPROVAL_PRIORITY,
  APPROVAL_ROLES,
  WORKFLOW_STEPS,
  APPROVAL_RULES,
  NOTIFICATION_TYPES,
  ACTION_TYPES,
  DOCUMENT_TYPES,
  TABLE_CONFIG,
  CHART_COLORS,
  DEFAULT_FILTERS,
  BATCH_ACTIONS,
  APPROVAL_LIMITS
} from '../components/approval-center/approvalCenterConstants';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const ApprovalCenter = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [approvals, setApprovals] = useState([]);
  const [selectedApprovals, setSelectedApprovals] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, setSearchText] = useState('');
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState(null);

  // 模拟数据
  const mockData = {
    approvals: [
      {
        id: 1,
        title: '服务器采购申请',
        type: 'purchase',
        status: 'pending',
        priority: 'high',
        amount: 50000,
        initiator: '张三',
        initiatorRole: '技术经理',
        currentStep: 'review',
        approver: '李四',
        approverRole: '部门总监',
        createdAt: '2024-01-18 09:30:00',
        updatedAt: '2024-01-18 10:15:00',
        deadline: '2024-01-20 18:00:00',
        description: '采购2台高性能服务器用于扩展云计算资源',
        documents: [
          { type: 'quotation', name: '报价单.pdf', url: '/files/quotation.pdf' },
          { type: 'technical_spec', name: '技术规格.pdf', url: '/files/spec.pdf' }
        ],
        comments: [
          { author: '张三', content: '已添加技术规格文档', time: '2024-01-18 09:45' },
          { author: '李四', content: '已审核，提交总监审批', time: '2024-01-18 10:15' }
        ]
      },
      // 更多模拟数据...
    ],
    metrics: {
      avgProcessingTime: 48,
      overdueRate: 8.5,
      satisfactionRate: 92.3
    },
    trend: {
      direction: 'up',
      percentage: 8.5
    }
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
        setApprovals(mockData.approvals);
        setLoading(false);
      }, 1000);
    } catch (error) {
      message.error('加载审批数据失败');
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredApprovals = useMemo(() => {
    return approvals.filter(approval => {
      const matchesSearch = !searchText || 
        approval.title.toLowerCase().includes(searchText.toLowerCase()) ||
        approval.initiator?.toLowerCase().includes(searchText.toLowerCase());

      const matchesType = !filters.type || approval.type === filters.type;
      const matchesStatus = !filters.status || approval.status === filters.status;
      const matchesPriority = !filters.priority || approval.priority === filters.priority;

      return matchesSearch && matchesType && matchesStatus && matchesPriority;
    });
  }, [approvals, searchText, filters]);

  // 事件处理
  const handleBatchAction = (action) => {
    if (selectedApprovals.length === 0) {
      message.warning('请先选择要操作的审批项');
      return;
    }

    Modal.confirm({
      title: '批量操作确认',
      content: `确认要对选中的 ${selectedApprovals.length} 项进行${action}操作吗？`,
      onOk: () => {
        executeBatchAction(action);
      }
    });
  };

  const executeBatchAction = async (action) => {
    try {
      setLoading(true);
      // 模拟批量操作API调用
      setTimeout(() => {
        message.success(`批量${action}操作成功`);
        setSelectedApprovals([]);
        setShowBatchModal(false);
        loadData();
        setLoading(false);
      }, 1000);
    } catch (error) {
      message.error('批量操作失败');
      setLoading(false);
    }
  };

  const handleApprovalAction = async (approvalId, action, comment = '') => {
    try {
      setLoading(true);
      // 模拟审批操作API调用
      setTimeout(() => {
        const approvalText = action === 'approve' ? '通过' : 
                           action === 'reject' ? '拒绝' : 
                           action === 'return' ? '退回' : '转发';
        message.success(`审批${approvalText}成功`);
        loadData();
        setLoading(false);
      }, 1000);
    } catch (error) {
      message.error('操作失败');
      setLoading(false);
    }
  };

  const handleExport = (format) => {
    message.success(`正在导出${format}格式报告...`);
  };

  // 表格列配置
  const approvalColumns = [
    {
      title: '审批信息',
      key: 'info',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 'bold', cursor: 'pointer' }}>
            <FileText size={16} style={{ marginRight: 8 }} />
            {record.title}
          </div>
          <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
            <Users size={12} /> {record.initiator} · ¥{record.amount?.toLocaleString()}
          </div>
        </div>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type) => {
        const config = APPROVAL_TYPES[type?.toUpperCase()];
        return (
          <Tag color={config?.color}>
            {config?.icon} {config?.label}
          </Tag>
        );
      }
    },
    {
      title: '状态',
      key: 'status',
      render: (_, record) => (
        <div>
          <Tag color={APPROVAL_STATUS[record.status?.toUpperCase()]?.color}>
            {APPROVAL_STATUS[record.status?.toUpperCase()]?.label}
          </Tag>
          <div style={{ fontSize: 11, color: '#666', marginTop: 4 }}>
            {WORKFLOW_STEPS[record.currentStep?.toUpperCase()]?.label}
          </div>
        </div>
      )
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => {
        const config = APPROVAL_PRIORITY[priority?.toUpperCase()];
        return (
          <Tag color={config?.color}>
            {config?.label}
          </Tag>
        );
      }
    },
    {
      title: '当前审批人',
      key: 'approver',
      render: (_, record) => (
        <div>
          <div>{record.approver}</div>
          <div style={{ fontSize: 11, color: '#666' }}>
            {APPROVAL_ROLES[record.approverRole?.toUpperCase()]?.label}
          </div>
        </div>
      )
    },
    {
      title: '时间信息',
      key: 'time',
      render: (_, record) => (
        <div>
          <div style={{ fontSize: 12 }}>
            <Clock size={12} /> 创建: {record.createdAt}
          </div>
          <div style={{ fontSize: 12, color: '#ff4d4f' }}>
            <AlertCircle size={12} /> 截止: {record.deadline}
          </div>
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<Eye size={16} />}
            onClick={() => {
              setSelectedApproval(record);
              setShowDetailModal(true);
            }}
          >
            查看
          </Button>
          {record.status === 'pending' && (
            <>
              <Button 
                type="link" 
                icon={<Check size={16} />}
                onClick={() => handleApprovalAction(record.id, 'approve')}
              >
                通过
              </Button>
              <Button 
                type="link" 
                danger
                icon={<X size={16} />}
                onClick={() => handleApprovalAction(record.id, 'reject')}
              >
                拒绝
              </Button>
            </>
          )}
        </Space>
      )
    }
  ];

  const tabItems = [
    {
      key: 'overview',
      tab: (
        <span>
          <ClipboardCheck size={16} />
          概览分析
        </span>
      ),
      content: <ApprovalOverview data={mockData} loading={loading} onNavigate={setActiveTab} />
    },
    {
      key: 'my-approvals',
      tab: (
        <span>
          <Users size={16} />
          我的审批 ({filteredApprovals.filter(a => a.status === 'pending').length})
        </span>
      ),
      content: <ApprovalList approvals={filteredApprovals.filter(a => a.status === 'pending')} loading={loading} />
    },
    {
      key: 'submitted',
      tab: (
        <span>
          <FileText size={16} />
          我提交的 ({filteredApprovals.filter(a => a.initiator === '当前用户').length})
        </span>
      ),
      content: <ApprovalList approvals={filteredApprovals.filter(a => a.initiator === '当前用户')} loading={loading} />
    },
    {
      key: 'workflow',
      tab: (
        <span>
          <Wrench size={16} />
          流程管理
        </span>
      ),
      content: <ApprovalWorkflow loading={loading} />
    },
    {
      key: 'statistics',
      tab: (
        <span>
          <Package size={16} />
          统计分析
        </span>
      ),
      content: <ApprovalStatistics data={mockData} loading={loading} />
    },
    {
      key: 'rules',
      tab: (
        <span>
          <Settings size={16} />
          审批规则
        </span>
      ),
      content: <ApprovalRules loading={loading} />
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="approval-center-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}
    >
      {/* 页面头部 */}
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="header-content" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              <ClipboardCheck className="inline-block mr-2" />
              审批中心
            </Title>
            <Text type="secondary">
              各类业务申请的统一审批管理平台
            </Text>
          </div>
          <Space>
            <Button 
              type="primary" 
              icon={<Plus size={16} />}
              onClick={() => setActiveTab('workflow')}
            >
              发起申请
            </Button>
            <Button 
              icon={<RefreshCw size={16} />}
              onClick={loadData}
            >
              刷新
            </Button>
            <Button 
              icon={<Download size={16} />}
            >
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
              placeholder="搜索审批标题、发起人..."
              prefix={<Search size={16} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Select
                placeholder="审批类型"
                value={filters.type}
                onChange={(value) => setFilters({ ...filters, type: value })}
                style={{ width: 120 }}
                allowClear
              >
                {Object.values(APPROVAL_TYPES).map(type => (
                  <Select.Option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                  </Select.Option>
                ))}
              </Select>
              <Select
                placeholder="状态"
                value={filters.status}
                onChange={(value) => setFilters({ ...filters, status: value })}
                style={{ width: 100 }}
                allowClear
              >
                {Object.values(APPROVAL_STATUS).map(status => (
                  <Select.Option key={status.value} value={status.value}>
                    <Tag color={status.color}>{status.label}</Tag>
                  </Select.Option>
                ))}
              </Select>
              <Select
                placeholder="优先级"
                value={filters.priority}
                onChange={(value) => setFilters({ ...filters, priority: value })}
                style={{ width: 100 }}
                allowClear
              >
                {Object.values(APPROVAL_PRIORITY).map(priority => (
                  <Select.Option key={priority.value} value={priority.value}>
                    <Tag color={priority.color}>{priority.label}</Tag>
                  </Select.Option>
                ))}
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
        >
          {tabItems.map(item => (
            <TabPane key={item.key} tab={item.tab}>
              {item.content}
            </TabPane>
          ))}
        </Tabs>
      </Card>

      {/* 审批详情模态框 */}
      <Modal
        title="审批详情"
        visible={showDetailModal}
        onCancel={() => {
          setShowDetailModal(false);
          setSelectedApproval(null);
        }}
        footer={null}
        width={800}
      >
        {selectedApproval && (
          <div>
            <Title level={4}>{selectedApproval.title}</Title>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic title="金额" value={selectedApproval.amount} prefix="¥" />
              </Col>
              <Col span={8}>
                <Statistic title="优先级" value={APPROVAL_PRIORITY[selectedApproval.priority?.toUpperCase()]?.label} />
              </Col>
              <Col span={8}>
                <Statistic title="状态" value={APPROVAL_STATUS[selectedApproval.status?.toUpperCase()]?.label} />
              </Col>
            </Row>
            <Divider />
            <div style={{ marginBottom: 16 }}>
              <Text strong>申请描述：</Text>
              <div style={{ marginTop: 8, padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
                {selectedApproval.description}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </motion.div>
  );
};

export default ApprovalCenter;
