/**
 * Contract Management Page (Refactored)
 * Features: Contract list, creation, signing, project generation (重构版本)
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Plus,
  FileCheck,
  DollarSign,
  Calendar,
  User,
  Building2,
  CheckCircle2,
  XCircle,
  Clock,
  Edit,
  Eye,
  FileText,
  Briefcase,
  X,
  Layers,
  Download,
  Upload,
  AlertTriangle,
  MoreHorizontal,
  TrendingUp,
  Users,
  Settings } from
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
  Upload as AntUpload,
  message,
  Spin,
  Tabs,
  Progress,
  Timeline,
  InputNumber,
  Rate } from
"antd";

// 导入拆分后的组件
import {
  ContractOverview,
  ContractList,
  ContractEditor,
  SignatureManager,
  PaymentTracker } from
'../components/contract-management';

import {
  CONTRACT_TYPES,
  CONTRACT_STATUS,
  SIGNATURE_STATUS,
  PAYMENT_TERMS,
  RISK_LEVELS,
  APPROVAL_LEVELS,
  CONTRACT_TEMPLATES,
  DOCUMENT_TYPES,
  NOTIFICATION_EVENTS,
  TABLE_CONFIG,
  DEFAULT_FILTERS,
  CHART_COLORS } from
'@/lib/constants/contractManagement';

// 导入 API service
import { getContracts, deleteContract } from '../services/contractService';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const ContractManagement = () => {
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, setSearchText] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSignatureModal, setShowSignatureModal] = useState(false);
  const [editingContract, setEditingContract] = useState(null);

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getContracts();
      // 确保 contracts 是数组
      const items = data?.items || data;
      setContracts(Array.isArray(items) ? items : []);
      setLoading(false);
    } catch (_error) {
      message.error('加载合同数据失败');
      setContracts([]);
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredContracts = useMemo(() => {
    return (contracts || []).filter((contract) => {
      const matchesSearch = !searchText ||
      contract.title.toLowerCase().includes(searchText.toLowerCase()) ||
      contract.clientName?.toLowerCase().includes(searchText.toLowerCase());

      const matchesType = !filters.type || contract.type === filters.type;
      const matchesStatus = !filters.status || contract.status === filters.status;
      const matchesSignature = !filters.signatureStatus || contract.signatureStatus === filters.signatureStatus;
      const matchesRisk = !filters.riskLevel || contract.riskLevel === filters.riskLevel;

      return matchesSearch && matchesType && matchesStatus && matchesSignature && matchesRisk;
    });
  }, [contracts, searchText, filters]);

  // 事件处理
  const handleCreateContract = () => {
    setShowCreateModal(true);
  };

  const handleEditContract = (contract) => {
    setEditingContract(contract);
    setShowCreateModal(true);
  };

  const handleDeleteContract = async (contractId) => {
    try {
      setLoading(true);
      await deleteContract(contractId);
      setContracts((contracts || []).filter((c) => c.id !== contractId));
      message.success('删除成功');
    } catch (_error) {
      message.error('删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSignContract = (contract) => {
    setSelectedContract(contract);
    setShowSignatureModal(true);
  };

  const handleExportContract = (format) => {
    message.success(`正在导出${format}格式合同...`);
  };

  const handleCreateProject = (contract) => {
    message.success(`正在为合同 ${contract.title} 创建项目...`);
  };

  // 表格列配置
  const _contractColumns = [
  {
    title: '合同信息',
    key: 'info',
    render: (_, record) =>
    <div>
          <div className="font-semibold cursor-pointer hover:text-primary transition-colors">
            {record.title}
          </div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-2">
            <Tag size="small">{CONTRACT_TYPES[record.type?.toUpperCase()]?.label}</Tag>
            <span>{record.clientName}</span>
          </div>
    </div>

  },
  {
    title: '状态',
    key: 'status',
    render: (_, record) =>
    <div>
          <Tag color={CONTRACT_STATUS[record.status?.toUpperCase()]?.color}>
            {CONTRACT_STATUS[record.status?.toUpperCase()]?.label}
          </Tag>
          <div className="mt-1">
            <Tag
          size="small"
          color={SIGNATURE_STATUS[record.signatureStatus?.toUpperCase()]?.color}>

              {SIGNATURE_STATUS[record.signatureStatus?.toUpperCase()]?.label}
            </Tag>
          </div>
    </div>

  },
  {
    title: '合同金额',
    dataIndex: 'value',
    key: 'value',
    render: (value) =>
    <span className="font-semibold text-emerald-400">
          ¥{value?.toLocaleString()}
    </span>

  },
  {
    title: '签署信息',
    key: 'signing',
    render: (_, record) =>
    <div className="text-xs space-y-1">
          <div className="flex items-center gap-1">
            <Calendar size={12} /> 签署: {record.signingDate || '-'}
          </div>
          <div className="flex items-center gap-1">
            <Clock size={12} /> 到期: {record.expiryDate}
          </div>
          {record.signingDeadline &&
      <div className="flex items-center gap-1 text-red-400">
              <AlertTriangle size={12} /> 期限: {record.signingDeadline}
      </div>
      }
    </div>

  },
  {
    title: '风险评估',
    dataIndex: 'riskLevel',
    key: 'riskLevel',
    render: (riskLevel) => {
      const config = RISK_LEVELS[riskLevel?.toUpperCase()];
      return (
        <Tag color={config?.color}>
            {config?.label}
        </Tag>);

    }
  },
  {
    title: '操作',
    key: 'actions',
    render: (_, record) =>
    <Space>
          <Button
        type="link"
        icon={<Eye size={16} />}
        onClick={() => setSelectedContract(record)}>

            查看
          </Button>
          <Button
        type="link"
        icon={<Edit size={16} />}
        onClick={() => handleEditContract(record)}>

            编辑
          </Button>
          {record.signatureStatus === 'pending' &&
      <Button
        type="link"
        icon={<FileCheck size={16} />}
        onClick={() => handleSignContract(record)}>

              签署
      </Button>
      }
          {record.status === 'signed' &&
      <Button
        type="link"
        icon={<Layers size={16} />}
        onClick={() => handleCreateProject(record)}>

              创建项目
      </Button>
      }
          <Dropdown
        overlay={
        <Menu>
                <Menu.Item onClick={() => handleExportContract('PDF')}>
                  <FileText size={14} /> 导出PDF
                </Menu.Item>
                <Menu.Item onClick={() => handleExportContract('Word')}>
                  <FileText size={14} /> 导出Word
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item
            danger
            onClick={() => handleDeleteContract(record.id)}>

                  <XCircle size={14} /> 删除合同
                </Menu.Item>
        </Menu>
        }>

            <Button type="link" icon={<MoreHorizontal size={16} />}>
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
      className="contract-management-container space-y-6">

      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-1 text-white">
            <FileCheck className="inline-block mr-2" />
            合同管理
          </Title>
          <Text className="text-slate-400">
            合同创建、签署、项目生成和管理
          </Text>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<Plus size={16} />}
            onClick={handleCreateContract}>

            创建合同
          </Button>
          <Button
            icon={<Upload size={16} />}>

            批量导入
          </Button>
          <Button
            icon={<Download size={16} />}>

            导出报表
          </Button>
        </Space>
      </div>

      {/* 搜索和过滤器 */}
      <Card className="bg-surface-1/50 border-border">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Input
              placeholder="搜索合同标题、客户名称..."
              prefix={<Search size={16} />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear />

          </Col>
          <Col xs={24} md={12}>
            <Space>
              <Select
                placeholder="合同类型"
                value={filters.type}
                onChange={(value) => setFilters({ ...filters, type: value })}
                style={{ width: 150 }}
                allowClear>

                {Object.values(CONTRACT_TYPES).map((type) =>
                <Select.Option key={type.value} value={type.value}>
                    {type.icon} {type.label}
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="状态"
                value={filters.status}
                onChange={(value) => setFilters({ ...filters, status: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(CONTRACT_STATUS).map((status) =>
                <Select.Option key={status.value} value={status.value}>
                    <Tag color={status.color}>{status.label}</Tag>
                </Select.Option>
                )}
              </Select>
              <Select
                placeholder="签署状态"
                value={filters.signatureStatus}
                onChange={(value) => setFilters({ ...filters, signatureStatus: value })}
                style={{ width: 120 }}
                allowClear>

                {Object.values(SIGNATURE_STATUS).map((status) =>
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
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        className="contract-tabs"
        items={[
          {
            key: 'overview',
            label: (
              <span>
                <TrendingUp size={16} />
                概览分析
              </span>
            ),
            children: (
              <ContractOverview
                data={contracts}
                loading={loading}
                onNavigate={(type, value) => {
                  setActiveTab('contracts');
                  if (type === 'status') {setFilters({ ...filters, status: value });}
                  if (type === 'risks') {setFilters({ ...filters, riskLevel: 'high' });}
                }} />
            )
          },
          {
            key: 'contracts',
            label: (
              <span>
                <FileText size={16} />
                合同列表 ({filteredContracts.length})
              </span>
            ),
            children: (
              <ContractList
                contracts={filteredContracts}
                loading={loading}
                onEdit={handleEditContract}
                onDelete={handleDeleteContract}
                onSign={handleSignContract}
                onCreateProject={handleCreateProject} />
            )
          },
          {
            key: 'editor',
            label: (
              <span>
                <Edit size={16} />
                合同编辑
              </span>
            ),
            children: (
              <ContractEditor
                contract={editingContract}
                onSave={() => {
                  setShowCreateModal(false);
                  setEditingContract(null);
                  loadData();
                }}
                onCancel={() => {
                  setShowCreateModal(false);
                  setEditingContract(null);
                }} />
            )
          },
          {
            key: 'signature',
            label: (
              <span>
                <FileCheck size={16} />
                签署管理
              </span>
            ),
            children: (
              <SignatureManager
                contracts={contracts}
                loading={loading}
                onRefresh={loadData} />
            )
          },
          {
            key: 'payment',
            label: (
              <span>
                <DollarSign size={16} />
                付款跟踪
              </span>
            ),
            children: (
              <PaymentTracker
                contracts={contracts}
                loading={loading} />
            )
          }
        ]} />

      {/* 合同创建/编辑模态框 */}
      <Modal
        title={editingContract ? '编辑合同' : '创建合同'}
        open={showCreateModal}
        onCancel={() => {
          setShowCreateModal(false);
          setEditingContract(null);
        }}
        footer={null}
        width={1000}>

        <ContractEditor
          contract={editingContract}
          onSave={() => {
            setShowCreateModal(false);
            setEditingContract(null);
            loadData();
          }}
          onCancel={() => {
            setShowCreateModal(false);
            setEditingContract(null);
          }} />

      </Modal>

      {/* 签署模态框 */}
      <Modal
        title="合同签署"
        open={showSignatureModal}
        onCancel={() => {
          setShowSignatureModal(false);
          setSelectedContract(null);
        }}
        footer={null}
        width={800}>

        {selectedContract &&
        <SignatureManager
          contracts={[selectedContract]}
          onSignComplete={() => {
            setShowSignatureModal(false);
            setSelectedContract(null);
            loadData();
          }} />

        }
      </Modal>
    </motion.div>);

};

export default ContractManagement;
