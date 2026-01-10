/**
 * Contract Management Page - Sales contract management
 * Features: Contract list, creation, signing, project generation
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
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Label,
  Textarea,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui";
import { cn, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  contractApi,
  opportunityApi,
  customerApi,
  salesTemplateApi,
} from "../services/api";

// 合同状态配置
const statusConfig = {
  DRAFT: {
    label: "草拟中",
    color: "bg-slate-500",
    textColor: "text-slate-400",
  },
  IN_REVIEW: {
    label: "审批中",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  SIGNED: {
    label: "已签订",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  ACTIVE: { label: "执行中", color: "bg-blue-500", textColor: "text-blue-400" },
  CLOSED: {
    label: "已结案",
    color: "bg-slate-600",
    textColor: "text-slate-500",
  },
  CANCELLED: { label: "取消", color: "bg-red-500", textColor: "text-red-400" },
};

export default function ContractManagement() {
  const [contracts, setContracts] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedContract, setSelectedContract] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showSignDialog, setShowSignDialog] = useState(false);
  const [showProjectDialog, setShowProjectDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [formData, setFormData] = useState({
    opportunity_id: "",
    customer_id: "",
    contract_amount: "",
    status: "DRAFT",
    payment_terms_summary: "",
    acceptance_summary: "",
    deliverables: [],
  });

  const [signData, setSignData] = useState({
    signed_date: new Date().toISOString().split("T")[0],
    remark: "",
  });

  const [projectData, setProjectData] = useState({
    project_code: "",
    project_name: "",
    pm_id: "",
    planned_start_date: "",
    planned_end_date: "",
  });

  const [newDeliverable, setNewDeliverable] = useState({
    deliverable_name: "",
    deliverable_type: "",
    required_for_payment: true,
    template_ref: "",
  });
  const [contractTemplates, setContractTemplates] = useState([]);
  const [contractTemplatePreview, setContractTemplatePreview] = useState(null);
  const [selectedContractTemplateId, setSelectedContractTemplateId] =
    useState("");
  const [
    selectedContractTemplateVersionId,
    setSelectedContractTemplateVersionId,
  ] = useState("");
  const [contractTemplateLoading, setContractTemplateLoading] = useState(false);

  const loadContracts = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      };
      const response = await contractApi.list(params);
      if (response.data && response.data.items) {
        setContracts(response.data.items);
        setTotal(response.data.total || 0);
      }
    } catch (error) {
      console.error("加载合同列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadOpportunities = async () => {
    try {
      const response = await opportunityApi.list({ page: 1, page_size: 100 });
      if (response.data && response.data.items) {
        setOpportunities(response.data.items);
      }
    } catch (error) {
      console.error("加载商机列表失败:", error);
    }
  };

  const loadCustomers = async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 100 });
      if (response.data && response.data.items) {
        setCustomers(response.data.items);
      }
    } catch (error) {
      console.error("加载客户列表失败:", error);
    }
  };

  const loadContractTemplates = async () => {
    try {
      const response = await salesTemplateApi.listContractTemplates({
        page: 1,
        page_size: 100,
      });
      if (response.data && response.data.items) {
        setContractTemplates(response.data.items);
      } else if (response.items) {
        setContractTemplates(response.items);
      }
    } catch (error) {
      console.error("加载合同模板失败:", error);
    }
  };

  const handleApplyContractTemplate = async (templateId, versionId) => {
    if (!templateId) return;
    setContractTemplateLoading(true);
    try {
      const params = versionId ? { template_version_id: versionId } : undefined;
      const response = await salesTemplateApi.applyContractTemplate(
        templateId,
        params,
      );
      const preview = response.data || response;
      setContractTemplatePreview(preview);
      setFormData((prev) => ({
        ...prev,
        payment_terms_summary: preview?.version?.clause_sections
          ? JSON.stringify(preview.version.clause_sections, null, 2)
          : prev.payment_terms_summary,
        acceptance_summary: preview?.version?.approval_flow
          ? JSON.stringify(preview.version.approval_flow, null, 2)
          : prev.acceptance_summary,
      }));
    } catch (error) {
      console.error("应用合同模板失败:", error);
      alert(
        "应用合同模板失败: " + (error.response?.data?.detail || error.message),
      );
    } finally {
      setContractTemplateLoading(false);
    }
  };

  const handleContractTemplateSelection = (value) => {
    setSelectedContractTemplateId(value);
    const template = contractTemplates.find((t) => String(t.id) === value);
    const defaultVersion = template?.versions?.[0];
    const versionId = defaultVersion ? String(defaultVersion.id) : "";
    setSelectedContractTemplateVersionId(versionId);
    if (template) {
      handleApplyContractTemplate(template.id, defaultVersion?.id);
    } else {
      setContractTemplatePreview(null);
    }
  };

  const handleContractTemplateVersionSelection = (value) => {
    setSelectedContractTemplateVersionId(value);
    const template = contractTemplates.find(
      (t) => String(t.id) === selectedContractTemplateId,
    );
    const version = template?.versions?.find((v) => String(v.id) === value);
    if (template && version) {
      handleApplyContractTemplate(template.id, version.id);
    }
  };

  const renderContractDiffSummary = (diff) => {
    if (!diff) {
      return <div className="text-sm text-slate-500">无差异</div>;
    }
    const sections = [
      { key: "clause_sections", label: "条款结构" },
      { key: "sections", label: "正文" },
    ];
    const hasChanges = sections.some(({ key }) => {
      const block = diff[key];
      return (
        block &&
        (block.added?.length || 0) +
          (block.removed?.length || 0) +
          (block.changed?.length || 0) >
          0
      );
    });
    if (!hasChanges) {
      return <div className="text-sm text-slate-500">与上一版本一致</div>;
    }
    return (
      <div className="space-y-1 text-xs">
        {sections.map(({ key, label }) => {
          const block = diff[key];
          if (!block) return null;
          const changes =
            (block.added?.length || 0) +
            (block.removed?.length || 0) +
            (block.changed?.length || 0);
          if (!changes) return null;
          return (
            <div key={key} className="bg-slate-800 rounded px-2 py-1">
              <div className="text-slate-300">{label}</div>
              <div className="text-slate-400">
                +{block.added?.length || 0} / -{block.removed?.length || 0} / Δ
                {block.changed?.length || 0}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  useEffect(() => {
    loadContracts();
  }, [page, searchTerm, statusFilter]);

  useEffect(() => {
    loadOpportunities();
    loadCustomers();
    loadContractTemplates();
  }, []);

  useEffect(() => {
    if (!showCreateDialog) {
      setContractTemplatePreview(null);
      setSelectedContractTemplateId("");
      setSelectedContractTemplateVersionId("");
    }
  }, [showCreateDialog]);

  const handleCreate = async () => {
    try {
      await contractApi.create(formData);
      setShowCreateDialog(false);
      resetForm();
      loadContracts();
    } catch (error) {
      console.error("创建合同失败:", error);
      alert("创建合同失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleSign = async () => {
    if (!selectedContract) return;
    try {
      await contractApi.sign(selectedContract.id, signData);
      setShowSignDialog(false);
      setSelectedContract(null);
      loadContracts();
    } catch (error) {
      console.error("合同签订失败:", error);
      alert("合同签订失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateProject = async () => {
    if (!selectedContract) return;
    try {
      const response = await contractApi.createProject(
        selectedContract.id,
        projectData,
      );
      setShowProjectDialog(false);
      setSelectedContract(null);
      alert("项目创建成功！项目ID: " + (response.data?.data?.project_id || ""));
      loadContracts();
    } catch (error) {
      console.error("创建项目失败:", error);
      alert("创建项目失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const addDeliverable = () => {
    if (!newDeliverable.deliverable_name) {
      alert("请输入交付物名称");
      return;
    }
    setFormData({
      ...formData,
      deliverables: [...formData.deliverables, { ...newDeliverable }],
    });
    setNewDeliverable({
      deliverable_name: "",
      deliverable_type: "",
      required_for_payment: true,
      template_ref: "",
    });
  };

  const removeDeliverable = (index) => {
    const newDeliverables = formData.deliverables.filter((_, i) => i !== index);
    setFormData({
      ...formData,
      deliverables: newDeliverables,
    });
  };

  const resetForm = () => {
    setFormData({
      opportunity_id: "",
      customer_id: "",
      contract_amount: "",
      status: "DRAFT",
      payment_terms_summary: "",
      acceptance_summary: "",
      deliverables: [],
    });
  };

  // 查看详情
  const handleViewDetail = async (contract) => {
    try {
      const response = await contractApi.get(contract.id);
      if (response.data) {
        setSelectedContract(response.data);
        setShowDetailDialog(true);
      }
    } catch (error) {
      console.error("加载合同详情失败:", error);
      setSelectedContract(contract);
      setShowDetailDialog(true);
    }
  };

  // 编辑合同
  const handleEditClick = (contract) => {
    setSelectedContract(contract);
    setFormData({
      opportunity_id: contract.opportunity_id || "",
      customer_id: contract.customer_id || "",
      contract_amount: contract.contract_amount || "",
      status: contract.status || "DRAFT",
      payment_terms_summary: contract.payment_terms_summary || "",
      acceptance_summary: contract.acceptance_summary || "",
      deliverables: contract.deliverables || [],
    });
    setShowEditDialog(true);
  };

  const stats = useMemo(() => {
    return {
      total: total,
      draft: contracts.filter((c) => c.status === "DRAFT").length,
      signed: contracts.filter((c) => c.status === "SIGNED").length,
      active: contracts.filter((c) => c.status === "ACTIVE").length,
      totalAmount: contracts.reduce(
        (sum, c) => sum + (parseFloat(c.contract_amount) || 0),
        0,
      ),
    };
  }, [contracts, total]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <PageHeader
        title="合同管理"
        description="管理销售合同，支持合同签订和项目生成"
        action={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建合同
          </Button>
        }
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总合同数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <FileCheck className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">草稿</p>
                <p className="text-2xl font-bold text-white">{stats.draft}</p>
              </div>
              <Clock className="h-8 w-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已签订</p>
                <p className="text-2xl font-bold text-white">{stats.signed}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">合同总额</p>
                <p className="text-2xl font-bold text-white">
                  {(stats.totalAmount / 10000).toFixed(1)}万
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选栏 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索合同编码..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  状态:{" "}
                  {statusFilter === "all"
                    ? "全部"
                    : statusConfig[statusFilter]?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setStatusFilter("all")}>
                  全部
                </DropdownMenuItem>
                {Object.entries(statusConfig).map(([key, config]) => (
                  <DropdownMenuItem
                    key={key}
                    onClick={() => setStatusFilter(key)}
                  >
                    {config.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>

      {/* 合同列表 */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : contracts.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无合同数据</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {contracts.map((contract) => (
            <motion.div
              key={contract.id}
              variants={fadeIn}
              whileHover={{ y: -4 }}
            >
              <Card className="h-full hover:border-blue-500 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">
                        {contract.contract_code}
                      </CardTitle>
                      <p className="text-sm text-slate-400 mt-1">
                        {contract.opportunity_code}
                      </p>
                    </div>
                    <Badge className={cn(statusConfig[contract.status]?.color)}>
                      {statusConfig[contract.status]?.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-300">
                      <Building2 className="h-4 w-4 text-slate-400" />
                      {contract.customer_name}
                    </div>
                    {contract.contract_amount && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <DollarSign className="h-4 w-4 text-slate-400" />
                        {parseFloat(
                          contract.contract_amount,
                        ).toLocaleString()}{" "}
                        元
                      </div>
                    )}
                    {contract.signed_date && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        签订日期: {contract.signed_date}
                      </div>
                    )}
                    {contract.project_code && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <Briefcase className="h-4 w-4 text-slate-400" />
                        项目: {contract.project_code}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewDetail(contract)}
                      className="flex-1"
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      详情
                    </Button>
                    {contract.status === "DRAFT" && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditClick(contract)}
                          className="flex-1"
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          编辑
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedContract(contract);
                            setShowSignDialog(true);
                          }}
                          className="flex-1"
                        >
                          <CheckCircle2 className="mr-2 h-4 w-4" />
                          签订
                        </Button>
                      </>
                    )}
                    {contract.status === "SIGNED" && !contract.project_id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedContract(contract);
                          setShowProjectDialog(true);
                        }}
                        className="flex-1"
                      >
                        <Briefcase className="mr-2 h-4 w-4" />
                        生成项目
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(total / pageSize)}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 创建合同对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>新建合同</DialogTitle>
            <DialogDescription>创建新的销售合同</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>商机 *</Label>
                <select
                  value={formData.opportunity_id}
                  onChange={(e) =>
                    setFormData({ ...formData, opportunity_id: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="">请选择商机</option>
                  {opportunities.map((opp) => (
                    <option key={opp.id} value={opp.id}>
                      {opp.opp_code} - {opp.opp_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>客户 *</Label>
                <select
                  value={formData.customer_id}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_id: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="">请选择客户</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.customer_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>合同金额</Label>
                <Input
                  type="number"
                  value={formData.contract_amount}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      contract_amount: e.target.value,
                    })
                  }
                  placeholder="请输入合同金额"
                />
              </div>
              <div>
                <Label>状态</Label>
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  {Object.entries(statusConfig).map(([key, config]) => (
                    <option key={key} value={key}>
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="border border-slate-700 rounded-md p-4 bg-slate-900 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="font-semibold">合同模板联动</Label>
                  <p className="text-xs text-slate-400">
                    引用模板快速补齐条款与审批信息，并查看版本差异
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open("/sales/templates", "_blank")}
                >
                  <Layers className="w-4 h-4 mr-1" />
                  模板中心
                </Button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <Label>合同模板</Label>
                  <select
                    value={selectedContractTemplateId}
                    onChange={(e) =>
                      handleContractTemplateSelection(e.target.value)
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                  >
                    <option value="">不使用模板</option>
                    {contractTemplates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.template_name}
                      </option>
                    ))}
                  </select>
                </div>
                {selectedContractTemplateId && (
                  <div>
                    <Label>模板版本</Label>
                    <select
                      value={selectedContractTemplateVersionId}
                      onChange={(e) =>
                        handleContractTemplateVersionSelection(e.target.value)
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                    >
                      {(
                        contractTemplates.find(
                          (t) => String(t.id) === selectedContractTemplateId,
                        )?.versions || []
                      ).map((version) => (
                        <option key={version.id} value={version.id}>
                          {version.version_no} · {version.status}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              {contractTemplateLoading && (
                <p className="text-xs text-slate-400">模板应用中...</p>
              )}
              {contractTemplatePreview?.version_diff && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div>
                    <div className="text-slate-400 mb-1">版本差异</div>
                    {renderContractDiffSummary(
                      contractTemplatePreview.version_diff,
                    )}
                  </div>
                  <div>
                    <div className="text-slate-400 mb-1">审批 / 发布记录</div>
                    <div className="space-y-1">
                      {(contractTemplatePreview.approval_history || [])
                        .slice(0, 4)
                        .map((record) => (
                          <div
                            key={record.version_id}
                            className="flex items-center justify-between bg-slate-800 rounded px-2 py-1"
                          >
                            <span>{record.version_no}</span>
                            <span className="text-slate-400">
                              {record.status}{" "}
                              {record.published_at
                                ? formatDate(record.published_at)
                                : ""}
                            </span>
                          </div>
                        ))}
                      {(contractTemplatePreview.approval_history || [])
                        .length === 0 && (
                        <div className="text-slate-500">暂无记录</div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div>
              <Label>付款条款摘要</Label>
              <Textarea
                value={formData.payment_terms_summary}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    payment_terms_summary: e.target.value,
                  })
                }
                placeholder="如: 预付款30%，发货款40%，验收款20%，质保款10%"
                rows={2}
              />
            </div>
            <div>
              <Label>验收摘要</Label>
              <Textarea
                value={formData.acceptance_summary}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    acceptance_summary: e.target.value,
                  })
                }
                placeholder="请输入验收摘要"
                rows={2}
              />
            </div>
            <div className="border-t border-slate-700 pt-4">
              <div className="flex items-center justify-between mb-2">
                <Label>交付物清单</Label>
                <Button variant="outline" size="sm" onClick={addDeliverable}>
                  <Plus className="mr-2 h-4 w-4" />
                  添加交付物
                </Button>
              </div>
              <div className="space-y-2 mb-2">
                <div className="grid grid-cols-5 gap-2">
                  <Input
                    placeholder="交付物名称"
                    value={newDeliverable.deliverable_name}
                    onChange={(e) =>
                      setNewDeliverable({
                        ...newDeliverable,
                        deliverable_name: e.target.value,
                      })
                    }
                  />
                  <Input
                    placeholder="类型"
                    value={newDeliverable.deliverable_type}
                    onChange={(e) =>
                      setNewDeliverable({
                        ...newDeliverable,
                        deliverable_type: e.target.value,
                      })
                    }
                  />
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={newDeliverable.required_for_payment}
                      onChange={(e) =>
                        setNewDeliverable({
                          ...newDeliverable,
                          required_for_payment: e.target.checked,
                        })
                      }
                      className="w-4 h-4"
                    />
                    <Label className="text-xs">付款必需</Label>
                  </div>
                  <Input
                    placeholder="模板引用"
                    value={newDeliverable.template_ref}
                    onChange={(e) =>
                      setNewDeliverable({
                        ...newDeliverable,
                        template_ref: e.target.value,
                      })
                    }
                  />
                </div>
              </div>
              {formData.deliverables.length > 0 && (
                <div className="space-y-1">
                  {formData.deliverables.map((deliverable, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-2 p-2 bg-slate-800 rounded text-sm"
                    >
                      <span className="flex-1">
                        {deliverable.deliverable_name}
                      </span>
                      <span className="text-slate-400">
                        {deliverable.deliverable_type}
                      </span>
                      {deliverable.required_for_payment && (
                        <Badge className="bg-amber-500">付款必需</Badge>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeDeliverable(index)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 合同签订对话框 */}
      <Dialog open={showSignDialog} onOpenChange={setShowSignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>合同签订</DialogTitle>
            <DialogDescription>确认合同签订信息</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>签订日期 *</Label>
              <Input
                type="date"
                value={signData.signed_date}
                onChange={(e) =>
                  setSignData({ ...signData, signed_date: e.target.value })
                }
              />
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={signData.remark}
                onChange={(e) =>
                  setSignData({ ...signData, remark: e.target.value })
                }
                placeholder="请输入备注"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSignDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSign}>确认签订</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 生成项目对话框 */}
      <Dialog open={showProjectDialog} onOpenChange={setShowProjectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>合同生成项目</DialogTitle>
            <DialogDescription>基于合同创建新项目</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>项目编码 *</Label>
              <Input
                value={projectData.project_code}
                onChange={(e) =>
                  setProjectData({
                    ...projectData,
                    project_code: e.target.value,
                  })
                }
                placeholder="如: PJ250115001"
              />
            </div>
            <div>
              <Label>项目名称 *</Label>
              <Input
                value={projectData.project_name}
                onChange={(e) =>
                  setProjectData({
                    ...projectData,
                    project_name: e.target.value,
                  })
                }
                placeholder="请输入项目名称"
              />
            </div>
            <div>
              <Label>项目经理ID</Label>
              <Input
                type="number"
                value={projectData.pm_id}
                onChange={(e) =>
                  setProjectData({ ...projectData, pm_id: e.target.value })
                }
                placeholder="请输入项目经理ID"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>计划开始日期</Label>
                <Input
                  type="date"
                  value={projectData.planned_start_date}
                  onChange={(e) =>
                    setProjectData({
                      ...projectData,
                      planned_start_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>计划结束日期</Label>
                <Input
                  type="date"
                  value={projectData.planned_end_date}
                  onChange={(e) =>
                    setProjectData({
                      ...projectData,
                      planned_end_date: e.target.value,
                    })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowProjectDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreateProject}>创建项目</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑合同对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>编辑合同</DialogTitle>
            <DialogDescription>更新合同信息</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>商机 *</Label>
                <select
                  value={formData.opportunity_id}
                  onChange={(e) =>
                    setFormData({ ...formData, opportunity_id: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="">请选择商机</option>
                  {opportunities.map((opp) => (
                    <option key={opp.id} value={opp.id}>
                      {opp.opp_code} - {opp.opp_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>客户 *</Label>
                <select
                  value={formData.customer_id}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_id: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="">请选择客户</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.customer_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>合同金额</Label>
                <Input
                  type="number"
                  value={formData.contract_amount}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      contract_amount: e.target.value,
                    })
                  }
                  placeholder="请输入合同金额"
                />
              </div>
              <div>
                <Label>状态</Label>
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  {Object.entries(statusConfig).map(([key, config]) => (
                    <option key={key} value={key}>
                      {config.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <Label>付款条款摘要</Label>
              <Textarea
                value={formData.payment_terms_summary}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    payment_terms_summary: e.target.value,
                  })
                }
                placeholder="如: 预付款30%，发货款40%，验收款20%，质保款10%"
                rows={2}
              />
            </div>
            <div>
              <Label>验收摘要</Label>
              <Textarea
                value={formData.acceptance_summary}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    acceptance_summary: e.target.value,
                  })
                }
                placeholder="请输入验收摘要"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button
              onClick={async () => {
                if (!selectedContract) return;
                try {
                  await contractApi.update(selectedContract.id, formData);
                  setShowEditDialog(false);
                  setSelectedContract(null);
                  loadContracts();
                } catch (error) {
                  console.error("更新合同失败:", error);
                  alert(
                    "更新合同失败: " +
                      (error.response?.data?.detail || error.message),
                  );
                }
              }}
            >
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>合同详情</DialogTitle>
            <DialogDescription>查看合同详细信息</DialogDescription>
          </DialogHeader>
          {selectedContract && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">基本信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">合同编码</Label>
                    <p className="text-white">
                      {selectedContract.contract_code}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">状态</Label>
                    <Badge
                      className={cn(
                        statusConfig[selectedContract.status]?.color,
                        "mt-1",
                      )}
                    >
                      {statusConfig[selectedContract.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-slate-400">客户</Label>
                    <p className="text-white">
                      {selectedContract.customer_name}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">商机</Label>
                    <p className="text-white">
                      {selectedContract.opportunity_code}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">合同金额</Label>
                    <p className="text-white">
                      {selectedContract.contract_amount
                        ? parseFloat(
                            selectedContract.contract_amount,
                          ).toLocaleString() + " 元"
                        : "-"}
                    </p>
                  </div>
                  {selectedContract.signed_date && (
                    <div>
                      <Label className="text-slate-400">签订日期</Label>
                      <p className="text-white">
                        {selectedContract.signed_date}
                      </p>
                    </div>
                  )}
                  {selectedContract.project_code && (
                    <div>
                      <Label className="text-slate-400">关联项目</Label>
                      <p className="text-white">
                        {selectedContract.project_code}
                      </p>
                    </div>
                  )}
                  <div className="col-span-2">
                    <Label className="text-slate-400">付款条款摘要</Label>
                    <p className="text-white mt-1">
                      {selectedContract.payment_terms_summary || "-"}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">验收摘要</Label>
                    <p className="text-white mt-1">
                      {selectedContract.acceptance_summary || "-"}
                    </p>
                  </div>
                </div>
              </div>

              {/* 交付物清单 */}
              {selectedContract.deliverables &&
                selectedContract.deliverables.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">交付物清单</h3>
                    <div className="space-y-2">
                      {selectedContract.deliverables.map(
                        (deliverable, index) => (
                          <Card key={index}>
                            <CardContent className="p-3">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-white font-medium">
                                    {deliverable.deliverable_name}
                                  </p>
                                  <p className="text-sm text-slate-400">
                                    {deliverable.deliverable_type}
                                  </p>
                                </div>
                                {deliverable.required_for_payment && (
                                  <Badge className="bg-amber-500">
                                    付款必需
                                  </Badge>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        ),
                      )}
                    </div>
                  </div>
                )}
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}
            >
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
