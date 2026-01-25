/**
 * Opportunity Management Page - Sales opportunity management
 * Features: Opportunity list, creation, update, gate management
 */

import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Plus,
  Target,
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
  LayoutGrid,
  List } from
"lucide-react";
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
  DropdownMenuTrigger } from
"../components/ui";
import { cn } from "../lib/utils";
import { opportunityApi, customerApi, userApi, presaleApi } from "../services/api";

// 商机阶段配置
const stageConfig = {
  DISCOVERY: {
    label: "需求澄清",
    color: "bg-blue-500",
    textColor: "text-blue-400"
  },
  QUALIFIED: {
    label: "商机合格",
    color: "bg-emerald-500",
    textColor: "text-emerald-400"
  },
  PROPOSAL: {
    label: "方案/报价中",
    color: "bg-amber-500",
    textColor: "text-amber-400"
  },
  REVIEW: {
    label: "方案评审",
    color: "bg-pink-500",
    textColor: "text-pink-400"
  },
  NEGOTIATION: {
    label: "商务谈判",
    color: "bg-purple-500",
    textColor: "text-purple-400"
  },
  WON: { label: "赢单", color: "bg-green-500", textColor: "text-green-400" },
  LOST: { label: "丢单", color: "bg-red-500", textColor: "text-red-400" },
  ON_HOLD: {
    label: "暂停",
    color: "bg-slate-500",
    textColor: "text-slate-400"
  }
};

const formatDateTime = (dateStr) => {
  if (!dateStr) {return "-";}
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
};

const isGatePassed = (status) => {
  const normalized = String(status || "").toUpperCase();
  return normalized === "PASS" || normalized === "PASSED";
};

export default function OpportunityManagement() {
  const [opportunities, setOpportunities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [owners, setOwners] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stageUpdating, setStageUpdating] = useState({});
  const [detailEditing, setDetailEditing] = useState(false);
  const [detailSaving, setDetailSaving] = useState(false);
  const [detailForm, setDetailForm] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [stageFilter, setStageFilter] = useState("all");
  const [selectedOpp, setSelectedOpp] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [_showEditDialog, setShowEditDialog] = useState(false);
  const [showGateDialog, setShowGateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewTarget, setReviewTarget] = useState(null);
  const [viewMode, setViewMode] = useState("grid");
  const [ownerFilter, setOwnerFilter] = useState("all");
  const [customerFilter, setCustomerFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    customer_id: "",
    opp_name: "",
    project_type: "",
    equipment_type: "",
    stage: "DISCOVERY",
    est_amount: "",
    est_margin: "",
    budget_range: "",
    decision_chain: "",
    delivery_window: "",
    acceptance_basis: "",
    requirement: {
      product_object: "",
      ct_seconds: "",
      interface_desc: "",
      site_constraints: "",
      acceptance_criteria: ""
    }
  });

  const [gateData, setGateData] = useState({
    gate_status: "PASS",
    remark: ""
  });

  const [reviewForm, setReviewForm] = useState({
    title: "",
    description: "",
    urgency: "NORMAL",
    expected_date: ""
  });

  const loadOpportunities = async ({ silent = false } = {}) => {
    if (!silent) {
      setLoading(true);
    }
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        stage: stageFilter !== "all" ? stageFilter : undefined,
        owner_id: ownerFilter !== "all" ? ownerFilter : undefined,
        customer_id: customerFilter !== "all" ? customerFilter : undefined
      };
      const response = await opportunityApi.list(params);
      if (response.data && response.data.items) {
        setOpportunities(response.data.items);
        setTotal(response.data.total || 0);
      }
    } catch (error) {
      console.error("加载商机列表失败:", error);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const loadCustomers = async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 200 });
      if (response.data && response.data.items) {
        setCustomers(response.data.items);
      }
    } catch (error) {
      console.error("加载客户列表失败:", error);
    }
  };

  const loadOwners = async () => {
    try {
      const response = await userApi.list({ page: 1, page_size: 200 });
      // 使用统一响应格式处理
      const paginatedData = response.formatted || response.data;
      if (paginatedData?.items) {
        setOwners(paginatedData.items);
      }
    } catch (error) {
      console.error("加载负责人列表失败:", error);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [page, searchTerm, stageFilter, ownerFilter, customerFilter]);

  useEffect(() => {
    loadCustomers();
    loadOwners();
  }, []);

  const handleCreate = async () => {
    try {
      await opportunityApi.create(formData);
      setShowCreateDialog(false);
      resetForm();
      loadOpportunities();
    } catch (error) {
      console.error("创建商机失败:", error);
      alert("创建商机失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const _handleUpdate = async () => {
    if (!selectedOpp) {return;}
    try {
      await opportunityApi.update(selectedOpp.id, formData);
      setShowEditDialog(false);
      setSelectedOpp(null);
      loadOpportunities();
    } catch (error) {
      console.error("更新商机失败:", error);
      alert("更新商机失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleSubmitGate = async () => {
    if (!selectedOpp) {return;}
    try {
      await opportunityApi.submitGate(selectedOpp.id, gateData);
      setShowGateDialog(false);
      setSelectedOpp(null);
      loadOpportunities();
    } catch (error) {
      console.error("提交阶段门失败:", error);
      alert(
        "提交阶段门失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleEdit = (opp) => {
    setSelectedOpp(opp);
    setFormData({
      customer_id: opp.customer_id || "",
      opp_name: opp.opp_name || "",
      project_type: opp.project_type || "",
      equipment_type: opp.equipment_type || "",
      stage: opp.stage || "DISCOVERY",
      est_amount: opp.est_amount || "",
      est_margin: opp.est_margin || "",
      budget_range: opp.budget_range || "",
      decision_chain: opp.decision_chain || "",
      delivery_window: opp.delivery_window || "",
      acceptance_basis: opp.acceptance_basis || "",
      requirement: opp.requirement || {
        product_object: "",
        ct_seconds: "",
        interface_desc: "",
        site_constraints: "",
        acceptance_criteria: ""
      }
    });
    setShowEditDialog(true);
  };

  const handleStageChange = async (opp, newStage) => {
    if (!opp || opp.stage === newStage) {
      return;
    }
    const prevStage = opp.stage;
    setStageUpdating((prev) => ({ ...prev, [opp.id]: true }));
    try {
      const response = await opportunityApi.update(opp.id, { stage: newStage });
      const updated = response.data || { ...opp, stage: newStage };
      setOpportunities((prev) =>
        prev.map((item) => (item.id === opp.id ? { ...item, ...updated } : item))
      );
      if (selectedOpp?.id === opp.id) {
        setSelectedOpp((prev) => (prev ? { ...prev, ...updated } : prev));
      }
      await loadOpportunities({ silent: true });
    } catch (error) {
      console.error("更新商机阶段失败:", error);
      alert(
        "更新商机阶段失败: " + (error.response?.data?.detail || error.message)
      );
      setOpportunities((prev) =>
        prev.map((item) =>
          item.id === opp.id ? { ...item, stage: prevStage } : item
        )
      );
    } finally {
      setStageUpdating((prev) => {
        const next = { ...prev };
        delete next[opp.id];
        return next;
      });
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: "",
      opp_name: "",
      project_type: "",
      equipment_type: "",
      stage: "DISCOVERY",
      est_amount: "",
      est_margin: "",
      budget_range: "",
      decision_chain: "",
      delivery_window: "",
      acceptance_basis: "",
      requirement: {
        product_object: "",
        ct_seconds: "",
        interface_desc: "",
        site_constraints: "",
        acceptance_criteria: ""
      }
    });
  };

  const buildDetailForm = (opp) => ({
    opp_name: opp?.opp_name || "",
    stage: opp?.stage || "DISCOVERY",
    project_type: opp?.project_type || "",
    equipment_type: opp?.equipment_type || "",
    probability: opp?.probability ?? "",
    est_amount: opp?.est_amount ?? "",
    est_margin: opp?.est_margin ?? "",
    expected_close_date: opp?.expected_close_date ?
    String(opp.expected_close_date).slice(0, 10) :
    "",
    budget_range: opp?.budget_range || "",
    decision_chain: opp?.decision_chain || "",
    delivery_window: opp?.delivery_window || "",
    acceptance_basis: opp?.acceptance_basis || "",
    risk_level: opp?.risk_level || "",
    score: opp?.score ?? "",
    priority_score: opp?.priority_score ?? "",
    requirement_maturity: opp?.requirement_maturity ?? "",
    assessment_status: opp?.assessment_status || "",
    requirement: {
      product_object: opp?.requirement?.product_object || "",
      ct_seconds: opp?.requirement?.ct_seconds ?? "",
      interface_desc: opp?.requirement?.interface_desc || "",
      site_constraints: opp?.requirement?.site_constraints || "",
      acceptance_criteria: opp?.requirement?.acceptance_criteria || "",
      safety_requirement: opp?.requirement?.safety_requirement || "",
      attachments: opp?.requirement?.attachments || "",
      extra_json: opp?.requirement?.extra_json || ""
    }
  });

  useEffect(() => {
    if (selectedOpp) {
      setDetailForm(buildDetailForm(selectedOpp));
      setDetailEditing(false);
    }
  }, [selectedOpp]);

  const openReviewDialog = (opp) => {
    if (!isGatePassed(opp?.gate_status)) {
      alert("商机阶段门未通过，无法申请评审");
      return;
    }
    const title = opp?.opp_name ?
    `方案评审申请 - ${opp.opp_name}` :
    "方案评审申请";
    setReviewTarget(opp);
    setReviewForm({
      title,
      description: opp?.opp_code ?
      `商机编号：${opp.opp_code}` :
      "",
      urgency: "NORMAL",
      expected_date: ""
    });
    setShowReviewDialog(true);
  };

  const handleCreateReviewTicket = async () => {
    if (!reviewTarget) {
      return;
    }
    if (!reviewForm.title.trim()) {
      alert("请输入申请标题");
      return;
    }
    setReviewSubmitting(true);
    try {
      await presaleApi.tickets.create({
        title: reviewForm.title.trim(),
        ticket_type: "SOLUTION_REVIEW",
        urgency: reviewForm.urgency,
        description: reviewForm.description?.trim() || undefined,
        customer_id: reviewTarget.customer_id || undefined,
        customer_name: reviewTarget.customer_name || undefined,
        opportunity_id: reviewTarget.id,
        expected_date: reviewForm.expected_date || undefined
      });
      setShowReviewDialog(false);
      setReviewTarget(null);
      alert("方案评审已提交");
      navigate("/presales-tasks?type=review&status=reviewing");
    } catch (error) {
      console.error("提交方案评审失败:", error);
      alert(
        "提交方案评审失败: " +
        (error.response?.data?.detail || error.message)
      );
    } finally {
      setReviewSubmitting(false);
    }
  };

  // 查看详情
  const handleViewDetail = async (opp) => {
    try {
      const response = await opportunityApi.get(opp.id);
      if (response.data) {
        setSelectedOpp(response.data);
        setShowDetailDialog(true);
      }
    } catch (error) {
      console.error("加载商机详情失败:", error);
      setSelectedOpp(opp);
      setShowDetailDialog(true);
    }
  };

  const handleDetailSave = async () => {
    if (!selectedOpp || !detailForm) {return;}
    setDetailSaving(true);
    try {
      const requirementValues = detailForm.requirement || {};
      const requirementHasValue = Object.values(requirementValues).some(
        (value) => value !== "" && value !== null && value !== undefined
      );
      const requirementPayload =
        requirementHasValue || selectedOpp.requirement ? requirementValues : undefined;
      const payload = {
        opp_name: detailForm.opp_name,
        stage: detailForm.stage,
        project_type: detailForm.project_type,
        equipment_type: detailForm.equipment_type,
        probability: detailForm.probability,
        est_amount: detailForm.est_amount,
        est_margin: detailForm.est_margin,
        expected_close_date: detailForm.expected_close_date || null,
        budget_range: detailForm.budget_range,
        decision_chain: detailForm.decision_chain,
        delivery_window: detailForm.delivery_window,
        acceptance_basis: detailForm.acceptance_basis,
        risk_level: detailForm.risk_level,
        score: detailForm.score,
        priority_score: detailForm.priority_score,
        requirement_maturity: detailForm.requirement_maturity,
        assessment_status: detailForm.assessment_status,
        requirement: requirementPayload
      };
      const response = await opportunityApi.update(selectedOpp.id, payload);
      const updated = response.data || { ...selectedOpp, ...payload };
      setSelectedOpp(updated);
      setOpportunities((prev) =>
        prev.map((item) => (item.id === selectedOpp.id ? { ...item, ...updated } : item))
      );
      setDetailEditing(false);
      await loadOpportunities({ silent: true });
    } catch (error) {
      console.error("更新商机详情失败:", error);
      alert(
        "更新商机详情失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setDetailSaving(false);
    }
  };

  const stats = useMemo(() => {
    return {
      total: total,
      discovery: opportunities.filter((o) => o.stage === "DISCOVERY").length,
      proposal: opportunities.filter((o) => o.stage === "PROPOSAL").length,
      won: opportunities.filter((o) => o.stage === "WON").length,
      totalAmount: opportunities.reduce(
        (sum, o) => sum + (parseFloat(o.est_amount) || 0),
        0
      )
    };
  }, [opportunities, total]);

  const detailData = detailEditing && detailForm ? detailForm : selectedOpp;

  return (
    <div className="space-y-6 p-6">

      <PageHeader
        title="商机管理"
        description="管理销售商机，跟踪项目进展"
        action={
        <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建商机
        </Button>
        } />


      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总商机数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <Target className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">需求澄清</p>
                <p className="text-2xl font-bold text-white">
                  {stats.discovery}
                </p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">报价中</p>
                <p className="text-2xl font-bold text-white">
                  {stats.proposal}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">预估金额</p>
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
                placeholder="搜索商机编码、名称..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10" />

            </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  阶段:{" "}
                  {stageFilter === "all" ?
                  "全部" :
                  stageConfig[stageFilter]?.label}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setStageFilter("all")}>
                全部
              </DropdownMenuItem>
              {Object.entries(stageConfig).map(([key, config]) =>
                <DropdownMenuItem
                  key={key}
                  onClick={() => setStageFilter(key)}>

                    {config.label}
                </DropdownMenuItem>
                )}
            </DropdownMenuContent>
          </DropdownMenu>
          <div className="flex gap-2">
            <select
              value={customerFilter}
              onChange={(e) => setCustomerFilter(e.target.value)}
              className="px-3 py-1 border rounded text-sm bg-slate-900 text-slate-300"
            >
              <option value="all">客户: 全部</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.customer_name}
                </option>
              ))}
            </select>
            <select
              value={ownerFilter}
              onChange={(e) => setOwnerFilter(e.target.value)}
              className="px-3 py-1 border rounded text-sm bg-slate-900 text-slate-300"
            >
              <option value="all">负责人: 全部</option>
              {owners.map((owner) => (
                <option key={owner.id} value={owner.id}>
                  {owner.real_name || owner.username}
                </option>
              ))}
            </select>
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("list")}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
          </div>
        </CardContent>
      </Card>

      {/* 商机列表 */}
      {loading ?
      <div className="text-center py-12 text-slate-400">加载中...</div> :
      opportunities.length === 0 ?
      <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无商机数据</p>
          </CardContent>
      </Card> :

      (viewMode === "grid" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {opportunities.map((opp) =>
          <motion.div key={opp.id} whileHover={{ y: -4 }}>
                <Card className="h-full hover:border-blue-500 transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{opp.opp_code}</CardTitle>
                        <p className="text-sm text-slate-400 mt-1">
                          {opp.opp_name}
                        </p>
                      </div>
                      <Badge className={cn(stageConfig[opp.stage]?.color)}>
                        {stageConfig[opp.stage]?.label}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2 text-slate-300">
                        <span className="text-xs text-slate-400">阶段</span>
                        <select
                          value={opp.stage}
                          onChange={(e) => handleStageChange(opp, e.target.value)}
                          disabled={!!stageUpdating[opp.id]}
                          className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs text-white">

                          {Object.entries(stageConfig).map(([key, config]) =>
                          <option key={key} value={key}>
                              {config.label}
                          </option>
                          )}
                        </select>
                        {stageUpdating[opp.id] &&
                      <span className="text-xs text-slate-500">更新中...</span>
                      }
                      </div>
                      <div className="flex items-center gap-2 text-slate-300">
                        <Building2 className="h-4 w-4 text-slate-400" />
                        {opp.customer_name}
                      </div>
                      {opp.est_amount &&
                  <div className="flex items-center gap-2 text-slate-300">
                          <DollarSign className="h-4 w-4 text-slate-400" />
                          {parseFloat(opp.est_amount).toLocaleString()} 元
                  </div>
                  }
                      {opp.owner_name &&
                  <div className="flex items-center gap-2 text-slate-300">
                          <User className="h-4 w-4 text-slate-400" />
                          负责人: {opp.owner_name}
                  </div>
                  }
                    </div>
                    <div className="grid grid-cols-4 gap-2 mt-4">
                      <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewDetail(opp)}
                    className="w-full">

                        <Eye className="mr-2 h-4 w-4" />
                        详情
                      </Button>
                      <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(opp)}
                    className="w-full">

                        <Edit className="mr-2 h-4 w-4" />
                        编辑
                      </Button>
                      <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedOpp(opp);
                      setShowGateDialog(true);
                    }}
                    className="w-full">

                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        阶段门
                      </Button>
                      <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openReviewDialog(opp)}
                    className="w-full"
                    disabled={!isGatePassed(opp.gate_status)}
                    title={
                      isGatePassed(opp.gate_status) ?
                      "" :
                      "阶段门未通过，无法申请评审"
                    }>

                        <FileText className="mr-2 h-4 w-4" />
                        申请评审
                      </Button>
                    </div>
                  </CardContent>
                </Card>
          </motion.div>
          )}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="text-left p-4 text-slate-400 text-sm">商机</th>
                    <th className="text-left p-4 text-slate-400 text-sm">客户</th>
                    <th className="text-left p-4 text-slate-400 text-sm">阶段</th>
                    <th className="text-left p-4 text-slate-400 text-sm">负责人</th>
                    <th className="text-left p-4 text-slate-400 text-sm">预估金额</th>
                    <th className="text-left p-4 text-slate-400 text-sm">创建时间</th>
                    <th className="text-left p-4 text-slate-400 text-sm">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {opportunities.map((opp) => (
                    <tr
                      key={opp.id}
                      className="border-b border-slate-800 hover:bg-slate-800/50"
                    >
                      <td className="p-4">
                        <div>
                          <div className="text-white font-medium">{opp.opp_name}</div>
                          <div className="text-xs text-slate-500">{opp.opp_code}</div>
                        </div>
                      </td>
                      <td className="p-4 text-slate-300">{opp.customer_name || "-"}</td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <select
                            value={opp.stage}
                            onChange={(e) => handleStageChange(opp, e.target.value)}
                            disabled={!!stageUpdating[opp.id]}
                            className="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs text-white"
                          >
                            {Object.entries(stageConfig).map(([key, config]) => (
                              <option key={key} value={key}>
                                {config.label}
                              </option>
                            ))}
                          </select>
                          {stageUpdating[opp.id] && (
                            <span className="text-xs text-slate-500">更新中...</span>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-blue-400">{opp.owner_name || "-"}</td>
                      <td className="p-4 text-slate-300">
                        {opp.est_amount ? `${parseFloat(opp.est_amount).toLocaleString()} 元` : "-"}
                      </td>
                      <td className="p-4 text-slate-400 text-sm">
                        {formatDateTime(opp.created_at)}
                      </td>
                      <td className="p-4">
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(opp)}
                            className="h-8 w-8 p-0"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(opp)}
                            className="h-8 w-8 p-0"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedOpp(opp);
                              setShowGateDialog(true);
                            }}
                            className="h-8 w-8 p-0 text-emerald-400"
                          >
                            <CheckCircle2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openReviewDialog(opp)}
                            className="h-8 w-8 p-0 text-violet-400"
                            disabled={!isGatePassed(opp.gate_status)}
                            title={
                              isGatePassed(opp.gate_status) ?
                              "" :
                              "阶段门未通过，无法申请评审"
                            }
                          >
                            <FileText className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ))
      }

      {/* 分页 */}
      {total > pageSize &&
      <div className="flex justify-center gap-2">
          <Button
          variant="outline"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}>

            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
          variant="outline"
          disabled={page >= Math.ceil(total / pageSize)}
          onClick={() => setPage(page + 1)}>

            下一页
          </Button>
      </div>
      }

      {/* 创建商机对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>新建商机</DialogTitle>
            <DialogDescription>创建新的销售商机</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>客户 *</Label>
                <select
                  value={formData.customer_id}
                  onChange={(e) =>
                  setFormData({ ...formData, customer_id: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white">

                  <option value="">请选择客户</option>
                  {customers.map((customer) =>
                  <option key={customer.id} value={customer.id}>
                      {customer.customer_name}
                  </option>
                  )}
                </select>
              </div>
              <div>
                <Label>商机名称 *</Label>
                <Input
                  value={formData.opp_name}
                  onChange={(e) =>
                  setFormData({ ...formData, opp_name: e.target.value })
                  }
                  placeholder="请输入商机名称" />

              </div>
              <div>
                <Label>项目类型</Label>
                <Input
                  value={formData.project_type}
                  onChange={(e) =>
                  setFormData({ ...formData, project_type: e.target.value })
                  }
                  placeholder="单机/线体/改造" />

              </div>
              <div>
                <Label>设备类型</Label>
                <Input
                  value={formData.equipment_type}
                  onChange={(e) =>
                  setFormData({ ...formData, equipment_type: e.target.value })
                  }
                  placeholder="ICT/FCT/EOL" />

              </div>
              <div>
                <Label>阶段</Label>
                <select
                  value={formData.stage}
                  onChange={(e) =>
                  setFormData({ ...formData, stage: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white">

                  {Object.entries(stageConfig).map(([key, config]) =>
                  <option key={key} value={key}>
                      {config.label}
                  </option>
                  )}
                </select>
              </div>
              <div>
                <Label>预估金额</Label>
                <Input
                  type="number"
                  value={formData.est_amount}
                  onChange={(e) =>
                  setFormData({ ...formData, est_amount: e.target.value })
                  }
                  placeholder="请输入预估金额" />

              </div>
              <div>
                <Label>预估毛利率 (%)</Label>
                <Input
                  type="number"
                  value={formData.est_margin}
                  onChange={(e) =>
                  setFormData({ ...formData, est_margin: e.target.value })
                  }
                  placeholder="请输入预估毛利率" />

              </div>
              <div>
                <Label>预算范围</Label>
                <Input
                  value={formData.budget_range}
                  onChange={(e) =>
                  setFormData({ ...formData, budget_range: e.target.value })
                  }
                  placeholder="如: 80-120万" />

              </div>
            </div>
            <div>
              <Label>决策链</Label>
              <Textarea
                value={formData.decision_chain}
                onChange={(e) =>
                setFormData({ ...formData, decision_chain: e.target.value })
                }
                placeholder="请输入决策链信息"
                rows={2} />

            </div>
            <div>
              <Label>交付窗口</Label>
              <Input
                value={formData.delivery_window}
                onChange={(e) =>
                setFormData({ ...formData, delivery_window: e.target.value })
                }
                placeholder="如: 2026年Q2" />

            </div>
            <div>
              <Label>验收依据</Label>
              <Textarea
                value={formData.acceptance_basis}
                onChange={(e) =>
                setFormData({ ...formData, acceptance_basis: e.target.value })
                }
                placeholder="请输入验收依据"
                rows={2} />

            </div>
            <div className="border-t border-slate-700 pt-4">
              <h4 className="text-sm font-semibold mb-2">需求信息</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>产品对象</Label>
                  <Input
                    value={formData.requirement.product_object}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: {
                        ...formData.requirement,
                        product_object: e.target.value
                      }
                    })
                    }
                    placeholder="如: PCB板" />

                </div>
                <div>
                  <Label>节拍 (秒)</Label>
                  <Input
                    type="number"
                    value={formData.requirement.ct_seconds}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: {
                        ...formData.requirement,
                        ct_seconds: e.target.value
                      }
                    })
                    }
                    placeholder="如: 1" />

                </div>
                <div className="col-span-2">
                  <Label>接口/通信协议</Label>
                  <Textarea
                    value={formData.requirement.interface_desc}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: {
                        ...formData.requirement,
                        interface_desc: e.target.value
                      }
                    })
                    }
                    placeholder="如: RS232/以太网"
                    rows={2} />

                </div>
                <div className="col-span-2">
                  <Label>现场约束</Label>
                  <Textarea
                    value={formData.requirement.site_constraints}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: {
                        ...formData.requirement,
                        site_constraints: e.target.value
                      }
                    })
                    }
                    placeholder="请输入现场约束条件"
                    rows={2} />

                </div>
                <div className="col-span-2">
                  <Label>验收依据</Label>
                  <Textarea
                    value={formData.requirement.acceptance_criteria}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      requirement: {
                        ...formData.requirement,
                        acceptance_criteria: e.target.value
                      }
                    })
                    }
                    placeholder="如: 节拍≤1秒，良率≥99.5%"
                    rows={2} />

                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 阶段门对话框 */}
      <Dialog open={showGateDialog} onOpenChange={setShowGateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>提交阶段门</DialogTitle>
            <DialogDescription>提交商机阶段门审核</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>阶段门状态 *</Label>
              <select
                value={gateData.gate_status}
                onChange={(e) =>
                setGateData({ ...gateData, gate_status: e.target.value })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white">

                <option value="PASS">通过</option>
                <option value="REJECT">拒绝</option>
              </select>
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={gateData.remark}
                onChange={(e) =>
                setGateData({ ...gateData, remark: e.target.value })
                }
                placeholder="请输入备注"
                rows={3} />

            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitGate}>提交</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>商机详情</DialogTitle>
            <DialogDescription>查看商机详细信息和需求</DialogDescription>
          </DialogHeader>
          {selectedOpp &&
          <div className="space-y-6">
              {/* 基本信息 */}
              <div>
                <h3 className="text-lg font-semibold mb-4">基本信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">商机编码</Label>
                    <p className="text-white">{selectedOpp.opp_code}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">商机名称</Label>
                    {detailEditing ?
                    <Input
                      value={detailForm?.opp_name || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, opp_name: e.target.value })
                      } /> :
                    <p className="text-white">{detailData?.opp_name}</p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">客户</Label>
                    <p className="text-white">{selectedOpp.customer_name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">负责人</Label>
                    <p className="text-white">{selectedOpp.owner_name || "-"}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">阶段</Label>
                    {detailEditing ?
                    <select
                      value={detailForm?.stage || "DISCOVERY"}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, stage: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white">

                      {Object.entries(stageConfig).map(([key, config]) =>
                      <option key={key} value={key}>
                          {config.label}
                      </option>
                      )}
                    </select> :
                    <Badge
                      className={cn(
                        stageConfig[selectedOpp.stage]?.color,
                        "mt-1"
                      )}>

                      {stageConfig[selectedOpp.stage]?.label}
                    </Badge>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">项目类型</Label>
                    {detailEditing ?
                    <Input
                      value={detailForm?.project_type || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, project_type: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.project_type || "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">设备类型</Label>
                    {detailEditing ?
                    <Input
                      value={detailForm?.equipment_type || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, equipment_type: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.equipment_type || "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">预估金额</Label>
                    {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.est_amount ?? ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, est_amount: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.est_amount ?
                      parseFloat(detailData.est_amount).toLocaleString() +
                      " 元" :
                      "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">预估毛利率</Label>
                    {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.est_margin ?? ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, est_margin: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.est_margin ?
                      detailData.est_margin + "%" :
                      "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">预算范围</Label>
                    {detailEditing ?
                    <Input
                      value={detailForm?.budget_range || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, budget_range: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.budget_range || "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">交付窗口</Label>
                    {detailEditing ?
                    <Input
                      value={detailForm?.delivery_window || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, delivery_window: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.delivery_window || "-"}
                    </p>
                    }
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">决策链</Label>
                    {detailEditing ?
                    <Textarea
                      value={detailForm?.decision_chain || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, decision_chain: e.target.value })
                      }
                      rows={2} /> :
                    <p className="text-white mt-1">
                        {detailData?.decision_chain || "-"}
                    </p>
                    }
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">验收依据</Label>
                    {detailEditing ?
                    <Textarea
                      value={detailForm?.acceptance_basis || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, acceptance_basis: e.target.value })
                      }
                      rows={2} /> :
                    <p className="text-white mt-1">
                        {detailData?.acceptance_basis || "-"}
                    </p>
                    }
                  </div>
                </div>
              </div>

              {/* 扩展信息 */}
              <div>
                <h3 className="text-lg font-semibold mb-4">扩展信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">成交概率 (%)</Label>
                    {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.probability ?? ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, probability: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.probability ?? "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">预计成交日期</Label>
                    {detailEditing ?
                    <Input
                      type="date"
                      value={detailForm?.expected_close_date || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, expected_close_date: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.expected_close_date || "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">风险等级</Label>
                    {detailEditing ?
                    <select
                      value={detailForm?.risk_level || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, risk_level: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white">

                      <option value="">未设置</option>
                      <option value="LOW">低</option>
                      <option value="MEDIUM">中</option>
                      <option value="HIGH">高</option>
                    </select> :
                    <p className="text-white">
                        {detailData?.risk_level || "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">评分</Label>
                    {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.score ?? ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, score: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.score ?? "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">优先级得分</Label>
                    {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.priority_score ?? ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, priority_score: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.priority_score ?? "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">需求成熟度</Label>
                    {detailEditing ?
                    <Input
                      type="number"
                      value={detailForm?.requirement_maturity ?? ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, requirement_maturity: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.requirement_maturity ?? "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">技术评估状态</Label>
                    {detailEditing ?
                    <Input
                      value={detailForm?.assessment_status || ""}
                      onChange={(e) =>
                      setDetailForm({ ...detailForm, assessment_status: e.target.value })
                      } /> :
                    <p className="text-white">
                        {detailData?.assessment_status || "-"}
                    </p>
                    }
                  </div>
                  <div>
                    <Label className="text-slate-400">阶段门状态</Label>
                    <p className="text-white">
                      {selectedOpp.gate_status || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">阶段门通过时间</Label>
                    <p className="text-white">
                      {selectedOpp.gate_passed_at || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">最后修改人</Label>
                    <p className="text-white">
                      {selectedOpp.updated_by_name || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">更新时间</Label>
                    <p className="text-white">
                      {selectedOpp.updated_at || "-"}
                    </p>
                  </div>
                </div>
              </div>

              {/* 需求信息 */}
              {(detailEditing || selectedOpp.requirement) &&
            <div>
                  <h3 className="text-lg font-semibold mb-4">需求信息</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-slate-400">产品对象</Label>
                      {detailEditing ?
                  <Input
                    value={detailForm?.requirement?.product_object || ""}
                    onChange={(e) =>
                    setDetailForm({
                      ...detailForm,
                      requirement: {
                        ...detailForm.requirement,
                        product_object: e.target.value
                      }
                    })
                    } /> :
                  <p className="text-white">
                        {detailData?.requirement?.product_object || "-"}
                  </p>
                  }
                    </div>
                    <div>
                      <Label className="text-slate-400">节拍 (秒)</Label>
                      {detailEditing ?
                  <Input
                    type="number"
                    value={detailForm?.requirement?.ct_seconds ?? ""}
                    onChange={(e) =>
                    setDetailForm({
                      ...detailForm,
                      requirement: {
                        ...detailForm.requirement,
                        ct_seconds: e.target.value
                      }
                    })
                    } /> :
                  <p className="text-white">
                        {detailData?.requirement?.ct_seconds || "-"}
                  </p>
                  }
                    </div>
                    <div className="col-span-2">
                      <Label className="text-slate-400">接口/通信协议</Label>
                      {detailEditing ?
                  <Textarea
                    value={detailForm?.requirement?.interface_desc || ""}
                    onChange={(e) =>
                    setDetailForm({
                      ...detailForm,
                      requirement: {
                        ...detailForm.requirement,
                        interface_desc: e.target.value
                      }
                    })
                    }
                    rows={2} /> :
                  <p className="text-white mt-1">
                        {detailData?.requirement?.interface_desc || "-"}
                  </p>
                  }
                    </div>
                    <div className="col-span-2">
                      <Label className="text-slate-400">现场约束</Label>
                      {detailEditing ?
                  <Textarea
                    value={detailForm?.requirement?.site_constraints || ""}
                    onChange={(e) =>
                    setDetailForm({
                      ...detailForm,
                      requirement: {
                        ...detailForm.requirement,
                        site_constraints: e.target.value
                      }
                    })
                    }
                    rows={2} /> :
                  <p className="text-white mt-1">
                        {detailData?.requirement?.site_constraints || "-"}
                  </p>
                  }
                    </div>
                    <div className="col-span-2">
                      <Label className="text-slate-400">验收依据</Label>
                      {detailEditing ?
                  <Textarea
                    value={detailForm?.requirement?.acceptance_criteria || ""}
                    onChange={(e) =>
                    setDetailForm({
                      ...detailForm,
                      requirement: {
                        ...detailForm.requirement,
                        acceptance_criteria: e.target.value
                      }
                    })
                    }
                    rows={2} /> :
                  <p className="text-white mt-1">
                        {detailData?.requirement?.acceptance_criteria || "-"}
                  </p>
                  }
                    </div>
                    <div className="col-span-2">
                      <Label className="text-slate-400">安全要求</Label>
                      {detailEditing ?
                  <Textarea
                    value={detailForm?.requirement?.safety_requirement || ""}
                    onChange={(e) =>
                    setDetailForm({
                      ...detailForm,
                      requirement: {
                        ...detailForm.requirement,
                        safety_requirement: e.target.value
                      }
                    })
                    }
                    rows={2} /> :
                  <p className="text-white mt-1">
                        {detailData?.requirement?.safety_requirement || "-"}
                  </p>
                  }
                    </div>
                  </div>
            </div>
            }
          </div>
          }
          <DialogFooter>
            {detailEditing ? (
              <>
                <Button
                  variant="outline"
                  onClick={() => {
                    setDetailEditing(false);
                    setDetailForm(buildDetailForm(selectedOpp));
                  }}>
                  取消
                </Button>
                <Button onClick={handleDetailSave} disabled={detailSaving}>
                  {detailSaving ? "保存中..." : "保存"}
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="outline"
                  onClick={() => setShowDetailDialog(false)}>
                  关闭
                </Button>
                <Button onClick={() => setDetailEditing(true)}>编辑</Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 方案评审申请对话框 */}
      <Dialog open={showReviewDialog} onOpenChange={setShowReviewDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>申请方案评审</DialogTitle>
            <DialogDescription>
              提交后将进入售前技术支持部的方案评审列表
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>申请标题 *</Label>
              <Input
                value={reviewForm.title}
                onChange={(e) =>
                  setReviewForm({ ...reviewForm, title: e.target.value })
                }
                placeholder="请输入评审申请标题"
              />
            </div>
            <div>
              <Label>详细说明</Label>
              <Textarea
                value={reviewForm.description}
                onChange={(e) =>
                  setReviewForm({ ...reviewForm, description: e.target.value })
                }
                placeholder="请输入评审说明或背景信息"
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>紧急程度</Label>
                <select
                  value={reviewForm.urgency}
                  onChange={(e) =>
                    setReviewForm({ ...reviewForm, urgency: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                >
                  <option value="NORMAL">普通</option>
                  <option value="URGENT">紧急</option>
                  <option value="VERY_URGENT">非常紧急</option>
                </select>
              </div>
              <div>
                <Label>期望完成日期</Label>
                <Input
                  type="date"
                  value={reviewForm.expected_date}
                  onChange={(e) =>
                    setReviewForm({
                      ...reviewForm,
                      expected_date: e.target.value
                    })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowReviewDialog(false)}
              disabled={reviewSubmitting}
            >
              取消
            </Button>
            <Button onClick={handleCreateReviewTicket} disabled={reviewSubmitting}>
              {reviewSubmitting ? "提交中..." : "提交评审"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);}
