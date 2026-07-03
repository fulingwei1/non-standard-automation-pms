/**
 * Contract Management Page (Refactored)
 * Features: Contract list, creation, signing, PMO initiation handoff (重构版本)
 */

import { useState, useEffect, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Search,
  Plus,
  FileCheck,
  DollarSign,
  Calendar,
  XCircle,
  Clock,
  Edit,
  Eye,
  FileText,
  Layers,
  AlertTriangle,
  MoreHorizontal,
  TrendingUp } from
"lucide-react";

import {
  Card,
  Button,
  Input,
  Select,
  DatePicker,
  Modal,
  Space,
  Tag,
  Row,
  Col,
  Typography,
  Dropdown,
  Menu,
  message,
  Tabs } from
"antd";

// 导入拆分后的组件
import {
  ContractOverview,
  ContractList,
  ContractEditor,
  SignatureManager,
  PaymentTracker } from
'../components/contract-management';
import ContractApproval from './ContractApproval';
import { usePermission } from '../hooks/usePermission';

import {
  CONTRACT_TYPES,
  CONTRACT_STATUS,
  SIGNATURE_STATUS,
  RISK_LEVELS,
  DEFAULT_FILTERS } from
'@/lib/constants/contractManagement';

// 导入 API service
import {
  getContracts,
  deleteContract,
} from '../services/contractService';
import { paymentPlanApi, pmoApi, receivableApi } from '../services/api';
import { pickExistingInitiationByContractNo } from '../utils/pmoInitiations';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const getResponsePayload = (response) => response?.data?.data ?? response?.data ?? response ?? {};

const CONTRACT_TAB_KEYS = new Set(['overview', 'contracts', 'editor', 'signature', 'payment', 'approval']);

function getContractTabFromSearch(search, canApproveContracts = false) {
  const tab = new URLSearchParams(search).get('tab');
  if (tab === 'approval' && canApproveContracts) {
    return tab;
  }
  if (tab && CONTRACT_TAB_KEYS.has(tab) && tab !== 'approval') {
    return tab;
  }
  return 'contracts';
}

const getPaginatedPayload = (response) => {
  const payload = getResponsePayload(response);
  if (Array.isArray(payload)) {
    return { items: payload, total: payload.length };
  }
  if (payload && Array.isArray(payload.items)) {
    return {
      items: payload.items,
      total: Number(payload.total ?? payload.items.length),
    };
  }
  return { items: [], total: 0 };
};

const findExistingInitiationByContractNo = async (contractNo) => {
  if (!contractNo) {
    return null;
  }

  const response = await pmoApi.initiations.list({
    contract_no: String(contractNo),
    page: 1,
    page_size: 20,
  });
  const payload = getPaginatedPayload(response);
  return pickExistingInitiationByContractNo(payload.items, contractNo);
};

const emptyContractOperations = {
  paymentPlanCount: 0,
  invoiceCount: 0,
  unpaidAmount: 0,
  overdueCount: 0,
  overdueAmount: 0,
  collectionRate: 0,
};

const CONTRACT_OPERATION_LOOKUP_LIMIT = 10;

const toNumber = (value) => Number(value || 0);

const ContractManagement = () => {
  const location = useLocation();
  const initialParams = new URLSearchParams(location.search);
  const navigate = useNavigate();
  const { hasPermission, isLoading: permissionsLoading } = usePermission();
  const canApproveContracts = hasPermission('contract:approve');
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [contracts, setContracts] = useState([]);
  const [overviewData, setOverviewData] = useState({ contracts: [], total: 0 });
  const [selectedContract, setSelectedContract] = useState(null);
  const [activeTab, setActiveTab] = useState(
    getContractTabFromSearch(location.search, canApproveContracts),
  );
  const [filters, setFilters] = useState({
    ...DEFAULT_FILTERS,
    customerId: initialParams.get("customer_id") || null,
    startDate: initialParams.get("start_date") || null,
    endDate: initialParams.get("end_date") || null,
  });
  const [searchText, setSearchText] = useState(initialParams.get("keyword") || '');  // 搜索框初始化为空字符串
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSignatureModal, setShowSignatureModal] = useState(false);
  const [editingContract, setEditingContract] = useState(null);
  const [messageApi, messageContextHolder] = message.useMessage();

  // 数据加载
  useEffect(() => {
    loadData();
  }, [activeTab, filters]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (!permissionsLoading) {
      setActiveTab(getContractTabFromSearch(location.search, canApproveContracts));
    }
    setSearchText(params.get("keyword") || "");
    setFilters((prev) => ({
      ...prev,
      customerId: params.get("customer_id") || null,
      startDate: params.get("start_date") || null,
      endDate: params.get("end_date") || null,
    }));
  }, [location.search, canApproveContracts, permissionsLoading]);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getContracts();
      // 后端返回分页格式：{ items: [...], total: N }
      const items = data?.items || data?.data?.items || data;
      const contractsData = Array.isArray(items) ? items : [];

      // 转换后端数据格式为前端期望的格式
      const baseContracts = contractsData.map((c) => {
        // 金额字段：后端可能返回 total_amount 或 contract_amount
        // Decimal 类型会被序列化为字符串或数字
        let rawAmount = c.total_amount ?? c.contract_amount ?? c.amount ?? 0;

        // 处理可能的 Decimal 对象、字符串或数字
        let numericAmount = 0;
        if (rawAmount === null || rawAmount === undefined) {
          numericAmount = 0;
        } else if (typeof rawAmount === 'number') {
          numericAmount = rawAmount;
        } else if (typeof rawAmount === 'string') {
          numericAmount = parseFloat(rawAmount) || 0;
        } else if (typeof rawAmount === 'object' && rawAmount !== null) {
          // 处理 Decimal 对象
          numericAmount = parseFloat(rawAmount.toString()) || 0;
        }

        const normalizedStatus = (c.status || 'draft').toLowerCase();
        const isSigned = ['signed', 'executing', 'completed'].includes(normalizedStatus);

        return {
          id: c.id,
          title: c.contract_name || c.contract_code || `合同-${c.id}`,
          contract_no: c.contract_code,
          contract_name: c.contract_name,
          client_name: c.customer_name,
          clientName: c.customer_name,
          value: numericAmount,
          amount: numericAmount,
          status: normalizedStatus,
          type: c.contract_type || 'sales',
          signatureStatus: isSigned ? 'signed' : 'pending',
          riskLevel: 'normal',
          created_at: c.created_at,
          signing_date: c.signing_date,
          customer_id: c.customer_id,
          project_id: c.project_id,
          project_code: c.project_code,
          contract_id: c.id,
          operations: emptyContractOperations,
        };
      });

      const shouldLoadOperations = activeTab === 'contracts';
      const transformedContracts = shouldLoadOperations
        ? await (async () => {
          const operationTargets = baseContracts.slice(0, CONTRACT_OPERATION_LOOKUP_LIMIT);
          const operationEntries = await Promise.all(
            operationTargets.map(async (contract) => [
              contract.id,
              await loadContractOperations(contract.id),
            ])
          );
          const operationsByContractId = new Map(operationEntries);
          return baseContracts.map((contract) => ({
            ...contract,
            operations: operationsByContractId.get(contract.id) || emptyContractOperations,
          }));
        })()
        : baseContracts;

      setContracts(transformedContracts);

      // 同时保存完整数据供概览组件使用
      setOverviewData({
        contracts: transformedContracts,
        total: data?.total || data?.data?.total || transformedContracts.length,
        page: data?.page || data?.data?.page || 1
      });

      setLoading(false);
    } catch (_error) {
      console.error('加载合同数据失败:', _error);
      messageApi.error('加载合同数据失败');
      setContracts([]);
      setLoading(false);
    }
  };

  const loadContractOperations = async (contractId) => {
    try {
      const [receivableSummaryResponse, paymentPlansResponse] = await Promise.all([
        receivableApi.getSummary({ contract_id: contractId }),
        paymentPlanApi.list({ contract_id: contractId, page_size: 100 }),
      ]);

      const summary = getResponsePayload(receivableSummaryResponse);
      const paymentPlans = getPaginatedPayload(paymentPlansResponse);

      return {
        paymentPlanCount: paymentPlans.total || paymentPlans.items.length,
        invoiceCount: toNumber(summary.invoice_count),
        unpaidAmount: toNumber(summary.unpaid_amount),
        overdueCount: toNumber(summary.overdue_count),
        overdueAmount: toNumber(summary.overdue_amount),
        collectionRate: toNumber(summary.collection_rate),
      };
    } catch (error) {
      console.warn('加载合同运营状态失败:', contractId, error);
      return emptyContractOperations;
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
      const matchesCustomer = !filters.customerId || String(contract.customer_id || '') === String(filters.customerId);
      const createdAt = contract.signing_date || contract.created_at;
      const matchesStartDate = !filters.startDate || !createdAt || String(createdAt).slice(0, 10) >= filters.startDate;
      const matchesEndDate = !filters.endDate || !createdAt || String(createdAt).slice(0, 10) <= filters.endDate;

      return matchesSearch && matchesType && matchesStatus && matchesSignature && matchesRisk && matchesCustomer && matchesStartDate && matchesEndDate;
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
      messageApi.success('删除成功');
    } catch (_error) {
      messageApi.error('删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSignContract = (contract) => {
    setSelectedContract(contract);
    setShowSignatureModal(true);
  };

  const handleExportContract = (format) => {
    messageApi.success(`正在导出${format}格式合同...`);
  };

  const handleCreateProject = async (contract) => {
    const contractCode = contract.contract_no || contract.contract_code || contract.id || contract.contract_id;
    const today = new Date().toISOString().slice(0, 10);
    const projectName = contract.title || contract.contract_name || '销售项目';
    const contractAmount = contract.value || contract.amount || undefined;

    try {
      setLoading(true);
      const existingInitiation = await findExistingInitiationByContractNo(contractCode);
      if (existingInitiation?.id) {
        messageApi.success('已存在立项申请，正在打开立项详情');
        navigate(`/pmo/initiations/${existingInitiation.id}`);
        return;
      }

      const response = await pmoApi.initiations.create({
        project_name: projectName,
        project_type: 'NEW',
        customer_name: contract.clientName || contract.client_name || contract.customer_name || '',
        contract_no: String(contractCode),
        contract_amount: contractAmount,
        required_start_date: today,
        requirement_summary: `由合同 ${contractCode} 发起立项`,
      });

      const initiation = response?.formatted || response?.data?.data || response?.data || {};
      const initiationId = initiation.id;
      messageApi.success('立项申请已创建，正在打开立项详情');
      await loadData();
      navigate(initiationId ? `/pmo/initiations/${initiationId}` : '/pmo/initiations');
    } catch (error) {
      const detail = error?.response?.data?.detail || error?.response?.data?.message || error.message;
      messageApi.error(`发起立项失败: ${detail}`);
    } finally {
      setLoading(false);
    }
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
          {!record.project_id &&
          record.signatureStatus === 'signed' &&
          ['signed', 'executing', 'completed'].includes(record.status) &&
      <Button
        type="link"
        icon={<Layers size={16} />}
        onClick={() => handleCreateProject(record)}>

              发起立项
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
      {messageContextHolder}

      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="!mb-1 text-white">
            <FileCheck className="inline-block mr-2" />
            合同管理
          </Title>
          <Text className="text-slate-400">
            合同创建、签署、立项移交和管理
          </Text>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<Plus size={16} />}
            onClick={handleCreateContract}>

            创建合同
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
                data={overviewData}
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
          },
          ...(canApproveContracts
            ? [
              {
                key: 'approval',
                label: (
                  <span>
                    <FileCheck size={16} />
                    合同审批
                  </span>
                ),
                children: <ContractApproval />,
              },
            ]
            : [])
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
