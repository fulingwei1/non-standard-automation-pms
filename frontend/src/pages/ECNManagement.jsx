/**
 * ECN Management Page - ECN管理页面
 * Features: ECN列表、详情、创建、评估、审批、执行、日志
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileEdit,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  GitBranch,
  User,
  Calendar,
  TrendingUp,
  FileText,
  Users,
  CheckSquare,
  History,
  ArrowRight,
  ArrowLeft,
  Play,
  Pause,
  X,
  RefreshCw,
  Download,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Checkbox } from "../components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { Textarea } from "../components/ui/textarea";
import { formatDate } from "../lib/utils";
import { ecnApi, projectApi, materialApi, purchaseApi } from "../services/api";

const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500" },
  SUBMITTED: { label: "已提交", color: "bg-blue-500" },
  EVALUATING: { label: "评估中", color: "bg-amber-500" },
  EVALUATED: { label: "评估完成", color: "bg-amber-600" },
  PENDING_APPROVAL: { label: "待审批", color: "bg-purple-500" },
  APPROVED: { label: "已批准", color: "bg-emerald-500" },
  REJECTED: { label: "已驳回", color: "bg-red-500" },
  EXECUTING: { label: "执行中", color: "bg-violet-500" },
  PENDING_VERIFY: { label: "待验证", color: "bg-indigo-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CLOSED: { label: "已关闭", color: "bg-gray-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};

const typeConfigs = {
  // 客户相关（3种）- 蓝色系
  CUSTOMER_REQUIREMENT: {
    label: "客户需求变更",
    color: "bg-blue-500",
    category: "客户相关",
  },
  CUSTOMER_SPEC: {
    label: "客户规格调整",
    color: "bg-blue-400",
    category: "客户相关",
  },
  CUSTOMER_FEEDBACK: {
    label: "客户现场反馈",
    color: "bg-blue-600",
    category: "客户相关",
  },

  // 设计变更（5种）- 青色系
  MECHANICAL_STRUCTURE: {
    label: "机械结构变更",
    color: "bg-cyan-500",
    category: "设计变更",
  },
  ELECTRICAL_SCHEME: {
    label: "电气方案变更",
    color: "bg-cyan-400",
    category: "设计变更",
  },
  SOFTWARE_FUNCTION: {
    label: "软件功能变更",
    color: "bg-cyan-600",
    category: "设计变更",
  },
  TECH_OPTIMIZATION: {
    label: "技术方案优化",
    color: "bg-teal-500",
    category: "设计变更",
  },
  DESIGN_FIX: {
    label: "设计缺陷修复",
    color: "bg-teal-600",
    category: "设计变更",
  },

  // 测试相关（4种）- 紫色系
  TEST_STANDARD: {
    label: "测试标准变更",
    color: "bg-purple-500",
    category: "测试相关",
  },
  TEST_FIXTURE: {
    label: "测试工装变更",
    color: "bg-purple-400",
    category: "测试相关",
  },
  CALIBRATION_SCHEME: {
    label: "校准方案变更",
    color: "bg-purple-600",
    category: "测试相关",
  },
  TEST_PROGRAM: {
    label: "测试程序变更",
    color: "bg-violet-500",
    category: "测试相关",
  },

  // 生产制造（4种）- 橙色系
  PROCESS_IMPROVEMENT: {
    label: "工艺改进",
    color: "bg-orange-500",
    category: "生产制造",
  },
  MATERIAL_SUBSTITUTE: {
    label: "物料替代",
    color: "bg-orange-400",
    category: "生产制造",
  },
  SUPPLIER_CHANGE: {
    label: "供应商变更",
    color: "bg-orange-600",
    category: "生产制造",
  },
  COST_OPTIMIZATION: {
    label: "成本优化",
    color: "bg-amber-500",
    category: "生产制造",
  },

  // 质量安全（3种）- 红色系
  QUALITY_ISSUE: {
    label: "质量问题整改",
    color: "bg-red-500",
    category: "质量安全",
  },
  SAFETY_COMPLIANCE: {
    label: "安全合规变更",
    color: "bg-red-600",
    category: "质量安全",
  },
  RELIABILITY_IMPROVEMENT: {
    label: "可靠性改进",
    color: "bg-rose-500",
    category: "质量安全",
  },

  // 项目管理（3种）- 绿色系
  SCHEDULE_ADJUSTMENT: {
    label: "进度调整",
    color: "bg-green-500",
    category: "项目管理",
  },
  DOCUMENT_UPDATE: {
    label: "文档更新",
    color: "bg-green-400",
    category: "项目管理",
  },
  DRAWING_CHANGE: {
    label: "图纸变更",
    color: "bg-emerald-500",
    category: "项目管理",
  },

  // 兼容旧版本
  DESIGN: { label: "设计变更", color: "bg-blue-500", category: "设计变更" },
  MATERIAL: { label: "物料变更", color: "bg-amber-500", category: "生产制造" },
  PROCESS: { label: "工艺变更", color: "bg-purple-500", category: "生产制造" },
  SPECIFICATION: {
    label: "规格变更",
    color: "bg-green-500",
    category: "项目管理",
  },
  SCHEDULE: { label: "计划变更", color: "bg-orange-500", category: "项目管理" },
  OTHER: { label: "其他", color: "bg-slate-500", category: "其他" },
};

const priorityConfigs = {
  URGENT: { label: "紧急", color: "bg-red-500" },
  HIGH: { label: "高", color: "bg-orange-500" },
  MEDIUM: { label: "中", color: "bg-amber-500" },
  LOW: { label: "低", color: "bg-blue-500" },
};

const evalResultConfigs = {
  APPROVED: { label: "通过", color: "bg-green-500" },
  CONDITIONAL: { label: "有条件通过", color: "bg-yellow-500" },
  REJECTED: { label: "不通过", color: "bg-red-500" },
};

const taskStatusConfigs = {
  PENDING: { label: "待开始", color: "bg-slate-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
};

export default function ECNManagement() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [ecns, setEcns] = useState([]);
  const [projects, setProjects] = useState([]);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedECN, setSelectedECN] = useState(null);
  const [activeTab, setActiveTab] = useState("info");

  // Batch operations
  const [selectedECNIds, setSelectedECNIds] = useState(new Set());
  const [showBatchDialog, setShowBatchDialog] = useState(false);
  const [batchOperation, setBatchOperation] = useState("");
  const [exporting, setExporting] = useState(false);

  // Detail data
  const [evaluations, setEvaluations] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [affectedMaterials, setAffectedMaterials] = useState([]);
  const [affectedOrders, setAffectedOrders] = useState([]);
  const [logs, setLogs] = useState([]);
  const [evaluationSummary, setEvaluationSummary] = useState(null);

  // Form state
  const [newECN, setNewECN] = useState({
    ecn_title: "",
    ecn_type: "CUSTOMER_REQUIREMENT",
    project_id: null,
    machine_id: null,
    priority: "MEDIUM",
    urgency: "NORMAL",
    change_reason: "",
    change_description: "",
    change_scope: "PARTIAL",
    source_type: "MANUAL",
  });

  // Evaluation form
  const [showEvaluationDialog, setShowEvaluationDialog] = useState(false);
  const [evaluationForm, setEvaluationForm] = useState({
    eval_dept: "",
    impact_analysis: "",
    cost_estimate: 0,
    schedule_estimate: 0,
    resource_requirement: "",
    risk_assessment: "",
    eval_result: "APPROVED",
    eval_opinion: "",
    conditions: "",
  });

  // Task form
  const [showTaskDialog, setShowTaskDialog] = useState(false);
  const [showBatchTaskDialog, setShowBatchTaskDialog] = useState(false);
  const [taskForm, setTaskForm] = useState({
    task_name: "",
    task_type: "",
    task_dept: "",
    task_description: "",
    deliverables: "",
    assignee_id: null,
    planned_start: "",
    planned_end: "",
  });
  const [batchTasks, setBatchTasks] = useState([
    {
      task_name: "",
      task_type: "",
      task_dept: "",
      task_description: "",
      deliverables: "",
      assignee_id: null,
      planned_start: "",
      planned_end: "",
    },
  ]);

  // Affected material form
  const [showMaterialDialog, setShowMaterialDialog] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [materialForm, setMaterialForm] = useState({
    material_id: null,
    bom_item_id: null,
    material_code: "",
    material_name: "",
    specification: "",
    change_type: "UPDATE",
    old_quantity: "",
    old_specification: "",
    old_supplier_id: null,
    new_quantity: "",
    new_specification: "",
    new_supplier_id: null,
    cost_impact: 0,
    remark: "",
  });

  // Affected order form
  const [showOrderDialog, setShowOrderDialog] = useState(false);
  const [editingOrder, setEditingOrder] = useState(null);
  const [orderForm, setOrderForm] = useState({
    order_type: "PURCHASE",
    order_id: null,
    order_no: "",
    impact_description: "",
    action_type: "",
    action_description: "",
  });

  // Materials and orders for selection
  const [materials, setMaterials] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);

  useEffect(() => {
    fetchProjects();
    fetchECNs();
  }, [filterProject, filterType, filterStatus, filterPriority, searchKeyword]);

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  const fetchECNs = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject && filterProject !== "all")
        params.project_id = filterProject;
      if (filterType && filterType !== "all") params.ecn_type = filterType;
      if (filterStatus && filterStatus !== "all") params.status = filterStatus;
      if (filterPriority && filterPriority !== "all")
        params.priority = filterPriority;
      if (searchKeyword) params.keyword = searchKeyword;
      const res = await ecnApi.list(params);
      const ecnList = res.data?.items || res.data || [];
      setEcns(ecnList);
    } catch (error) {
      console.error("Failed to fetch ECNs:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchECNDetail = async (ecnId) => {
    try {
      const res = await ecnApi.get(ecnId);
      setSelectedECN(res.data || res);

      // Fetch related data
      const [
        evalsRes,
        approvalsRes,
        tasksRes,
        materialsRes,
        ordersRes,
        logsRes,
        summaryRes,
      ] = await Promise.all([
        ecnApi.getEvaluations(ecnId).catch(() => ({ data: [] })),
        ecnApi.getApprovals(ecnId).catch(() => ({ data: [] })),
        ecnApi.getTasks(ecnId).catch(() => ({ data: [] })),
        ecnApi.getAffectedMaterials(ecnId).catch(() => ({ data: [] })),
        ecnApi.getAffectedOrders(ecnId).catch(() => ({ data: [] })),
        ecnApi.getLogs(ecnId).catch(() => ({ data: [] })),
        ecnApi.getEvaluationSummary(ecnId).catch(() => ({ data: null })),
      ]);

      setEvaluations(evalsRes.data || []);
      setApprovals(approvalsRes.data || []);
      setTasks(tasksRes.data || []);
      setAffectedMaterials(materialsRes.data || []);
      setAffectedOrders(ordersRes.data || []);
      setLogs(logsRes.data || []);
      setEvaluationSummary(summaryRes.data);
    } catch (error) {
      console.error("Failed to fetch ECN detail:", error);
    }
  };

  const handleViewDetail = (ecnId) => {
    navigate(`/ecns/${ecnId}`);
  };

  const handleCreateECN = async () => {
    if (!newECN.ecn_title) {
      alert("请填写ECN标题");
      return;
    }
    if (!newECN.change_reason) {
      alert("请填写变更原因");
      return;
    }
    if (!newECN.change_description) {
      alert("请填写变更描述");
      return;
    }
    try {
      await ecnApi.create(newECN);
      setShowCreateDialog(false);
      setNewECN({
        ecn_title: "",
        ecn_type: "CUSTOMER_REQUIREMENT",
        project_id: null,
        machine_id: null,
        priority: "MEDIUM",
        urgency: "NORMAL",
        change_reason: "",
        change_description: "",
        change_scope: "PARTIAL",
        source_type: "MANUAL",
      });
      fetchECNs();
    } catch (error) {
      console.error("Failed to create ECN:", error);
      alert("创建ECN失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleSubmit = async (ecnId) => {
    if (!confirm("确认提交此ECN？提交后将进入评估流程。")) return;
    try {
      await ecnApi.submit(ecnId, { remark: "" });
      fetchECNs();
      if (showDetailDialog) {
        await fetchECNDetail(ecnId);
      }
    } catch (error) {
      console.error("Failed to submit ECN:", error);
      alert("提交失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateEvaluation = async () => {
    if (!evaluationForm.eval_dept) {
      alert("请选择评估部门");
      return;
    }
    if (!evaluationForm.eval_result) {
      alert("请选择评估结论");
      return;
    }
    try {
      await ecnApi.createEvaluation(selectedECN.id, evaluationForm);
      setShowEvaluationDialog(false);
      setEvaluationForm({
        eval_dept: "",
        impact_analysis: "",
        cost_estimate: 0,
        schedule_estimate: 0,
        resource_requirement: "",
        risk_assessment: "",
        eval_result: "APPROVED",
        eval_opinion: "",
        conditions: "",
      });
      await fetchECNDetail(selectedECN.id);
    } catch (error) {
      console.error("Failed to create evaluation:", error);
      alert("创建评估失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleSubmitEvaluation = async (evalId) => {
    if (!confirm("确认提交此评估？提交后将无法修改。")) return;
    try {
      await ecnApi.submitEvaluation(evalId);
      await fetchECNDetail(selectedECN.id);
    } catch (error) {
      console.error("Failed to submit evaluation:", error);
      alert("提交评估失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleApprove = async (approvalId, comment = "") => {
    try {
      await ecnApi.approve(approvalId, comment);
      await fetchECNDetail(selectedECN.id);
    } catch (error) {
      console.error("Failed to approve:", error);
      alert("审批失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleReject = async (approvalId, reason) => {
    if (!reason) {
      reason = prompt("请输入驳回原因：");
      if (!reason) return;
    }
    try {
      await ecnApi.reject(approvalId, reason);
      await fetchECNDetail(selectedECN.id);
    } catch (error) {
      console.error("Failed to reject:", error);
      alert("驳回失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateTask = async () => {
    if (!taskForm.task_name) {
      alert("请填写任务名称");
      return;
    }
    try {
      await ecnApi.createTask(selectedECN.id, taskForm);
      setShowTaskDialog(false);
      setTaskForm({
        task_name: "",
        task_type: "",
        task_dept: "",
        task_description: "",
        deliverables: "",
        assignee_id: null,
        planned_start: "",
        planned_end: "",
      });
      await fetchECNDetail(selectedECN.id);
    } catch (error) {
      console.error("Failed to create task:", error);
      alert("创建任务失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdateTaskProgress = async (taskId, progress) => {
    try {
      await ecnApi.updateTaskProgress(taskId, { progress_pct: progress });
      await fetchECNDetail(selectedECN.id);
    } catch (error) {
      console.error("Failed to update task progress:", error);
      alert(
        "更新任务进度失败: " + (error.response?.data?.detail || error.message),
      );
    }
  };

  const handleCompleteTask = async (taskId) => {
    if (!confirm("确认完成任务？")) return;
    try {
      await ecnApi.completeTask(taskId, { completion_note: "任务已完成" });
      await fetchECNDetail(selectedECN.id);
    } catch (error) {
      console.error("Failed to complete task:", error);
      alert("完成任务失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const filteredECNs = useMemo(() => {
    return ecns.filter((ecn) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          ecn.ecn_no?.toLowerCase().includes(keyword) ||
          ecn.ecn_title?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [ecns, searchKeyword]);

  // 导出ECN列表
  const handleExport = () => {
    try {
      setExporting(true);
      const exportData = [
        [
          "ECN编号",
          "ECN标题",
          "项目",
          "类型",
          "状态",
          "优先级",
          "申请人",
          "申请时间",
          "成本影响",
          "工期影响",
        ],
        ...filteredECNs.map((ecn) => [
          ecn.ecn_no || "",
          ecn.ecn_title || "",
          ecn.project_name || "",
          typeConfigs[ecn.ecn_type]?.label || ecn.ecn_type || "",
          statusConfigs[ecn.status]?.label || ecn.status || "",
          priorityConfigs[ecn.priority]?.label || ecn.priority || "",
          ecn.applicant_name || "",
          ecn.applied_at
            ? new Date(ecn.applied_at).toLocaleDateString("zh-CN")
            : "",
          ecn.cost_impact ? `¥${ecn.cost_impact}` : "¥0",
          ecn.schedule_impact_days ? `${ecn.schedule_impact_days}天` : "0天",
        ]),
      ];

      const csvContent = exportData
        .map((row) => row.map((cell) => `"${cell}"`).join(","))
        .join("\n");

      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], {
        type: "text/csv;charset=utf-8;",
      });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute(
        "download",
        `ECN列表_${new Date().toISOString().split("T")[0]}.csv`,
      );
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("导出失败:", error);
      alert("导出失败: " + error.message);
    } finally {
      setExporting(false);
    }
  };

  // 批量操作
  const handleBatchOperation = async (operation) => {
    if (selectedECNIds.size === 0) {
      alert("请先选择ECN");
      return;
    }

    const ids = Array.from(selectedECNIds);
    let confirmMessage = "";
    let apiCall = null;

    switch (operation) {
      case "submit":
        confirmMessage = `确认要批量提交 ${ids.length} 个ECN吗？`;
        apiCall = async (id) => {
          // 需要先获取审批ID，这里简化处理，直接调用submit
          await ecnApi.submit(id, { remark: "批量提交" });
        };
        break;
      case "approve":
        confirmMessage = `确认要批量批准 ${ids.length} 个ECN吗？`;
        // 注意：approve需要approval_id，这里需要先获取审批记录
        apiCall = async (id) => {
          // 简化处理：这里需要根据实际API调整
          alert("批量批准功能需要先获取审批记录，请使用单个批准功能");
          throw new Error("批量批准需要审批ID");
        };
        break;
      case "close":
        confirmMessage = `确认要批量关闭 ${ids.length} 个ECN吗？`;
        apiCall = async (id) => {
          await ecnApi.close(id, { close_note: "批量关闭" });
        };
        break;
      default:
        alert("未知操作");
        return;
    }

    if (!confirm(confirmMessage)) return;

    try {
      const results = [];
      for (const id of ids) {
        try {
          await apiCall(id);
          results.push({ id, success: true });
        } catch (error) {
          results.push({
            id,
            success: false,
            error: error.response?.data?.detail || error.message,
          });
        }
      }

      const successCount = results.filter((r) => r.success).length;
      const failCount = results.filter((r) => !r.success).length;

      if (failCount > 0) {
        const failDetails = results
          .filter((r) => !r.success)
          .map((r) => `ECN ${r.id}: ${r.error}`)
          .join("\n");
        alert(
          `批量操作完成：成功 ${successCount} 个，失败 ${failCount} 个\n\n失败详情：\n${failDetails}`,
        );
      } else {
        alert(`批量操作完成：成功 ${successCount} 个`);
      }
      setSelectedECNIds(new Set());
      fetchECNs();
    } catch (error) {
      alert("批量操作失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 全选/取消全选
  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedECNIds(new Set(filteredECNs.map((ecn) => ecn.id)));
    } else {
      setSelectedECNIds(new Set());
    }
  };

  // 切换单个选择
  const handleToggleSelect = (ecnId) => {
    const newSelected = new Set(selectedECNIds);
    if (newSelected.has(ecnId)) {
      newSelected.delete(ecnId);
    } else {
      newSelected.add(ecnId);
    }
    setSelectedECNIds(newSelected);
  };

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="ECN管理"
        description="设计变更管理，支持创建、评估、审批、执行"
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索ECN编号、标题..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {projects.map((proj) => (
                  <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger>
                <SelectValue placeholder="选择优先级" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部优先级</SelectItem>
                {Object.entries(priorityConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Action Bar */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          {selectedECNIds.size > 0 && (
            <>
              <span className="text-sm text-slate-500">
                已选择 {selectedECNIds.size} 个ECN
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBatchOperation("submit")}
              >
                批量提交
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBatchOperation("close")}
              >
                批量关闭
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedECNIds(new Set())}
              >
                取消选择
              </Button>
            </>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleExport}
            disabled={exporting || filteredECNs.length === 0}
          >
            <Download className="w-4 h-4 mr-2" />
            {exporting ? "导出中..." : "导出列表"}
          </Button>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            新建ECN
          </Button>
        </div>
      </div>

      {/* ECN List */}
      <Card>
        <CardHeader>
          <CardTitle>ECN列表</CardTitle>
          <CardDescription>共 {filteredECNs.length} 个ECN</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredECNs.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无ECN</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={
                        selectedECNIds.size === filteredECNs.length &&
                        filteredECNs.length > 0
                      }
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead>ECN编号</TableHead>
                  <TableHead>ECN标题</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>优先级</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>申请人</TableHead>
                  <TableHead>申请时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredECNs.map((ecn) => (
                  <TableRow key={ecn.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedECNIds.has(ecn.id)}
                        onCheckedChange={() => handleToggleSelect(ecn.id)}
                      />
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {ecn.ecn_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {ecn.ecn_title}
                    </TableCell>
                    <TableCell>{ecn.project_name || "-"}</TableCell>
                    <TableCell>
                      <Badge
                        className={
                          typeConfigs[ecn.ecn_type]?.color || "bg-slate-500"
                        }
                      >
                        {typeConfigs[ecn.ecn_type]?.label || ecn.ecn_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          priorityConfigs[ecn.priority]?.color || "bg-slate-500"
                        }
                      >
                        {priorityConfigs[ecn.priority]?.label || ecn.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={
                          statusConfigs[ecn.status]?.color || "bg-slate-500"
                        }
                      >
                        {statusConfigs[ecn.status]?.label || ecn.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{ecn.applicant_name || "-"}</TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {ecn.applied_at ? formatDate(ecn.applied_at) : "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(ecn.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {ecn.status === "DRAFT" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleSubmit(ecn.id)}
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create ECN Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>新建ECN</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  ECN标题 *
                </label>
                <Input
                  value={newECN.ecn_title}
                  onChange={(e) =>
                    setNewECN({ ...newECN, ecn_title: e.target.value })
                  }
                  placeholder="请输入ECN标题"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    变更类型
                  </label>
                  <Select
                    value={newECN.ecn_type}
                    onValueChange={(val) =>
                      setNewECN({ ...newECN, ecn_type: val })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typeConfigs).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    优先级
                  </label>
                  <Select
                    value={newECN.priority}
                    onValueChange={(val) =>
                      setNewECN({ ...newECN, priority: val })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(priorityConfigs).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">项目</label>
                <Select
                  value={newECN.project_id?.toString() || "__none__"}
                  onValueChange={(val) =>
                    setNewECN({
                      ...newECN,
                      project_id:
                        val && val !== "__none__" ? parseInt(val) : null,
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {projects.map((proj) => (
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                        {proj.project_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  变更原因 *
                </label>
                <Textarea
                  value={newECN.change_reason}
                  onChange={(e) =>
                    setNewECN({ ...newECN, change_reason: e.target.value })
                  }
                  placeholder="填写变更原因"
                  rows={2}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  变更描述 *
                </label>
                <Textarea
                  value={newECN.change_description}
                  onChange={(e) =>
                    setNewECN({ ...newECN, change_description: e.target.value })
                  }
                  placeholder="详细描述变更内容..."
                  rows={4}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreateECN}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ECN Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>
                {selectedECN?.ecn_title} - {selectedECN?.ecn_no}
              </span>
              {selectedECN && (
                <Badge className={statusConfigs[selectedECN.status]?.color}>
                  {statusConfigs[selectedECN.status]?.label}
                </Badge>
              )}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedECN && (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-7">
                  <TabsTrigger value="info">基本信息</TabsTrigger>
                  <TabsTrigger value="evaluations">评估</TabsTrigger>
                  <TabsTrigger value="approvals">审批</TabsTrigger>
                  <TabsTrigger value="tasks">执行任务</TabsTrigger>
                  <TabsTrigger value="affected">影响分析</TabsTrigger>
                  <TabsTrigger value="integration">模块集成</TabsTrigger>
                  <TabsTrigger value="logs">变更日志</TabsTrigger>
                </TabsList>

                {/* 基本信息 */}
                <TabsContent value="info" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-500 mb-1">ECN编号</div>
                      <div className="font-mono">{selectedECN.ecn_no}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">状态</div>
                      <Badge
                        className={statusConfigs[selectedECN.status]?.color}
                      >
                        {statusConfigs[selectedECN.status]?.label}
                      </Badge>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">项目</div>
                      <div>{selectedECN.project_name || "-"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        变更类型
                      </div>
                      <Badge
                        className={typeConfigs[selectedECN.ecn_type]?.color}
                      >
                        {typeConfigs[selectedECN.ecn_type]?.label}
                      </Badge>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">优先级</div>
                      <Badge
                        className={priorityConfigs[selectedECN.priority]?.color}
                      >
                        {priorityConfigs[selectedECN.priority]?.label}
                      </Badge>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">申请人</div>
                      <div>{selectedECN.applicant_name || "-"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        申请时间
                      </div>
                      <div>
                        {selectedECN.applied_at
                          ? formatDate(selectedECN.applied_at)
                          : "-"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        成本影响
                      </div>
                      <div>¥{selectedECN.cost_impact || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        工期影响
                      </div>
                      <div>{selectedECN.schedule_impact_days || 0} 天</div>
                    </div>
                  </div>
                  {selectedECN.change_reason && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        变更原因
                      </div>
                      <div className="p-3 bg-slate-50 rounded-lg">
                        {selectedECN.change_reason}
                      </div>
                    </div>
                  )}
                  {selectedECN.change_description && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        变更描述
                      </div>
                      <div className="p-3 bg-slate-50 rounded-lg whitespace-pre-wrap">
                        {selectedECN.change_description}
                      </div>
                    </div>
                  )}
                  {selectedECN.approval_note && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">
                        审批意见
                      </div>
                      <div className="p-3 bg-slate-50 rounded-lg">
                        {selectedECN.approval_note}
                      </div>
                    </div>
                  )}
                  {selectedECN.status === "DRAFT" && (
                    <div className="flex justify-end gap-2 pt-4">
                      <Button onClick={() => handleSubmit(selectedECN.id)}>
                        <CheckCircle2 className="w-4 h-4 mr-2" />
                        提交ECN
                      </Button>
                    </div>
                  )}
                </TabsContent>

                {/* 评估管理 */}
                <TabsContent value="evaluations" className="space-y-4">
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-slate-500">
                      {evaluationSummary && (
                        <div className="space-y-1">
                          <div>
                            总成本影响: ¥
                            {evaluationSummary.total_cost_impact || 0}
                          </div>
                          <div>
                            最大工期影响:{" "}
                            {evaluationSummary.max_schedule_impact || 0} 天
                          </div>
                          <div>
                            评估完成度: {evaluationSummary.completion_rate || 0}
                            %
                          </div>
                        </div>
                      )}
                    </div>
                    {selectedECN.status === "SUBMITTED" ||
                    selectedECN.status === "EVALUATING" ? (
                      <Button onClick={() => setShowEvaluationDialog(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        创建评估
                      </Button>
                    ) : null}
                  </div>
                  {evaluations.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">
                      暂无评估记录
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {evaluations.map((evaluation) => (
                        <Card key={evaluation.id}>
                          <CardHeader>
                            <div className="flex justify-between items-center">
                              <CardTitle className="text-base">
                                {evaluation.eval_dept}
                              </CardTitle>
                              <div className="flex items-center gap-2">
                                <Badge
                                  className={
                                    evalResultConfigs[evaluation.eval_result]
                                      ?.color || "bg-slate-500"
                                  }
                                >
                                  {evalResultConfigs[evaluation.eval_result]
                                    ?.label || evaluation.eval_result}
                                </Badge>
                                <Badge
                                  className={
                                    evaluation.status === "SUBMITTED"
                                      ? "bg-green-500"
                                      : "bg-amber-500"
                                  }
                                >
                                  {evaluation.status === "SUBMITTED"
                                    ? "已提交"
                                    : "草稿"}
                                </Badge>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-2 text-sm">
                              <div>
                                <span className="text-slate-500">评估人:</span>{" "}
                                {evaluation.evaluator_name || "-"}
                              </div>
                              {evaluation.cost_estimate > 0 && (
                                <div>
                                  <span className="text-slate-500">
                                    成本估算:
                                  </span>{" "}
                                  ¥{evaluation.cost_estimate}
                                </div>
                              )}
                              {evaluation.schedule_estimate > 0 && (
                                <div>
                                  <span className="text-slate-500">
                                    工期估算:
                                  </span>{" "}
                                  {evaluation.schedule_estimate} 天
                                </div>
                              )}
                              {evaluation.impact_analysis && (
                                <div>
                                  <div className="text-slate-500 mb-1">
                                    影响分析:
                                  </div>
                                  <div className="p-2 bg-slate-50 rounded">
                                    {evaluation.impact_analysis}
                                  </div>
                                </div>
                              )}
                              {evaluation.eval_opinion && (
                                <div>
                                  <div className="text-slate-500 mb-1">
                                    评估意见:
                                  </div>
                                  <div className="p-2 bg-slate-50 rounded">
                                    {evaluation.eval_opinion}
                                  </div>
                                </div>
                              )}
                              {evaluation.status === "DRAFT" && (
                                <div className="flex justify-end pt-2">
                                  <Button
                                    size="sm"
                                    onClick={() =>
                                      handleSubmitEvaluation(evaluation.id)
                                    }
                                  >
                                    提交评估
                                  </Button>
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </TabsContent>

                {/* 审批流程可视化 */}
                <TabsContent value="approvals" className="space-y-4">
                  {approvals.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">
                      暂无审批记录
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {approvals.map((approval, index) => (
                        <div
                          key={approval.id}
                          className="flex items-start gap-4"
                        >
                          <div className="flex flex-col items-center">
                            <div
                              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                                approval.status === "COMPLETED" &&
                                approval.approval_result === "APPROVED"
                                  ? "bg-green-500"
                                  : approval.status === "COMPLETED" &&
                                      approval.approval_result === "REJECTED"
                                    ? "bg-red-500"
                                    : approval.status === "PENDING"
                                      ? "bg-blue-500"
                                      : "bg-slate-300"
                              } text-white font-bold`}
                            >
                              {index + 1}
                            </div>
                            {index < approvals.length - 1 && (
                              <div
                                className={`w-0.5 h-12 ${
                                  approval.status === "COMPLETED"
                                    ? "bg-green-500"
                                    : "bg-slate-300"
                                }`}
                              />
                            )}
                          </div>
                          <Card className="flex-1">
                            <CardHeader>
                              <div className="flex justify-between items-center">
                                <CardTitle className="text-base">
                                  第{approval.approval_level}级审批 -{" "}
                                  {approval.approval_role}
                                </CardTitle>
                                <Badge
                                  className={
                                    approval.status === "COMPLETED" &&
                                    approval.approval_result === "APPROVED"
                                      ? "bg-green-500"
                                      : approval.status === "COMPLETED" &&
                                          approval.approval_result ===
                                            "REJECTED"
                                        ? "bg-red-500"
                                        : approval.status === "PENDING"
                                          ? "bg-blue-500"
                                          : "bg-slate-500"
                                  }
                                >
                                  {approval.status === "COMPLETED" &&
                                  approval.approval_result === "APPROVED"
                                    ? "已通过"
                                    : approval.status === "COMPLETED" &&
                                        approval.approval_result === "REJECTED"
                                      ? "已驳回"
                                      : approval.status === "PENDING"
                                        ? "待审批"
                                        : approval.status}
                                </Badge>
                              </div>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2 text-sm">
                                <div>
                                  <span className="text-slate-500">
                                    审批人:
                                  </span>{" "}
                                  {approval.approver_name || "待分配"}
                                </div>
                                {approval.approved_at && (
                                  <div>
                                    <span className="text-slate-500">
                                      审批时间:
                                    </span>{" "}
                                    {formatDate(approval.approved_at)}
                                  </div>
                                )}
                                {approval.approval_opinion && (
                                  <div>
                                    <div className="text-slate-500 mb-1">
                                      审批意见:
                                    </div>
                                    <div className="p-2 bg-slate-50 rounded">
                                      {approval.approval_opinion}
                                    </div>
                                  </div>
                                )}
                                {approval.status === "PENDING" && (
                                  <div className="flex justify-end gap-2 pt-2">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => {
                                        const reason =
                                          prompt("请输入驳回原因：");
                                        if (reason)
                                          handleReject(approval.id, reason);
                                      }}
                                    >
                                      驳回
                                    </Button>
                                    <Button
                                      size="sm"
                                      onClick={() => {
                                        const comment =
                                          prompt("请输入审批意见（可选）：") ||
                                          "";
                                        handleApprove(approval.id, comment);
                                      }}
                                    >
                                      通过
                                    </Button>
                                  </div>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>

                {/* 执行任务看板 */}
                <TabsContent value="tasks" className="space-y-4">
                  <div className="flex justify-end gap-2">
                    {selectedECN.status === "APPROVED" ||
                    selectedECN.status === "EXECUTING" ? (
                      <>
                        <Button
                          variant="outline"
                          onClick={() => setShowBatchTaskDialog(true)}
                        >
                          <Layers className="w-4 h-4 mr-2" />
                          批量创建任务
                        </Button>
                        <Button onClick={() => setShowTaskDialog(true)}>
                          <Plus className="w-4 h-4 mr-2" />
                          创建任务
                        </Button>
                      </>
                    ) : null}
                  </div>
                  {tasks.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">
                      暂无执行任务
                    </div>
                  ) : (
                    <div className="grid grid-cols-3 gap-4">
                      {["PENDING", "IN_PROGRESS", "COMPLETED"].map((status) => {
                        const statusTasks = tasks.filter(
                          (t) => t.status === status,
                        );
                        return (
                          <Card key={status}>
                            <CardHeader>
                              <CardTitle className="text-sm">
                                {taskStatusConfigs[status]?.label || status}
                                <Badge className="ml-2">
                                  {statusTasks.length}
                                </Badge>
                              </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                              {statusTasks.map((task) => (
                                <Card key={task.id} className="p-3">
                                  <div className="space-y-2">
                                    <div className="font-medium text-sm">
                                      {task.task_name}
                                    </div>
                                    <div className="text-xs text-slate-500">
                                      {task.task_dept && (
                                        <div>部门: {task.task_dept}</div>
                                      )}
                                      {task.assignee_name && (
                                        <div>负责人: {task.assignee_name}</div>
                                      )}
                                      {task.planned_start && (
                                        <div>
                                          计划: {formatDate(task.planned_start)}{" "}
                                          -{" "}
                                          {task.planned_end
                                            ? formatDate(task.planned_end)
                                            : ""}
                                        </div>
                                      )}
                                    </div>
                                    {task.status === "IN_PROGRESS" && (
                                      <div className="space-y-1">
                                        <div className="text-xs text-slate-500">
                                          进度: {task.progress_pct || 0}%
                                        </div>
                                        <div className="flex gap-1">
                                          <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={task.progress_pct || 0}
                                            onChange={(e) =>
                                              handleUpdateTaskProgress(
                                                task.id,
                                                parseInt(e.target.value),
                                              )
                                            }
                                            className="flex-1"
                                          />
                                        </div>
                                      </div>
                                    )}
                                    {task.status === "IN_PROGRESS" && (
                                      <Button
                                        size="sm"
                                        className="w-full mt-2"
                                        onClick={() =>
                                          handleCompleteTask(task.id)
                                        }
                                      >
                                        完成任务
                                      </Button>
                                    )}
                                  </div>
                                </Card>
                              ))}
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </TabsContent>

                {/* 影响分析 */}
                <TabsContent value="affected" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <div className="flex justify-between items-center">
                          <CardTitle className="text-base">
                            受影响物料
                          </CardTitle>
                          {(selectedECN.status === "DRAFT" ||
                            selectedECN.status === "SUBMITTED" ||
                            selectedECN.status === "EVALUATING") && (
                            <Button size="sm" onClick={handleAddMaterial}>
                              <Plus className="w-4 h-4 mr-2" />
                              添加物料
                            </Button>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent>
                        {affectedMaterials.length === 0 ? (
                          <div className="text-center py-4 text-slate-400 text-sm">
                            暂无受影响物料
                          </div>
                        ) : (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>物料编码</TableHead>
                                <TableHead>物料名称</TableHead>
                                <TableHead>变更类型</TableHead>
                                <TableHead>成本影响</TableHead>
                                <TableHead className="text-right">
                                  操作
                                </TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {affectedMaterials.map((mat) => (
                                <TableRow key={mat.id}>
                                  <TableCell className="font-mono text-sm">
                                    {mat.material_code}
                                  </TableCell>
                                  <TableCell>{mat.material_name}</TableCell>
                                  <TableCell>
                                    <Badge className="bg-blue-500">
                                      {mat.change_type}
                                    </Badge>
                                  </TableCell>
                                  <TableCell>¥{mat.cost_impact || 0}</TableCell>
                                  <TableCell className="text-right">
                                    <div className="flex items-center justify-end gap-2">
                                      {(selectedECN.status === "DRAFT" ||
                                        selectedECN.status === "SUBMITTED" ||
                                        selectedECN.status ===
                                          "EVALUATING") && (
                                        <>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() =>
                                              handleEditMaterial(mat)
                                            }
                                          >
                                            <FileEdit className="w-4 h-4" />
                                          </Button>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() =>
                                              handleDeleteMaterial(mat.id)
                                            }
                                          >
                                            <X className="w-4 h-4" />
                                          </Button>
                                        </>
                                      )}
                                    </div>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <div className="flex justify-between items-center">
                          <CardTitle className="text-base">
                            受影响订单
                          </CardTitle>
                          {(selectedECN.status === "DRAFT" ||
                            selectedECN.status === "SUBMITTED" ||
                            selectedECN.status === "EVALUATING") && (
                            <Button size="sm" onClick={handleAddOrder}>
                              <Plus className="w-4 h-4 mr-2" />
                              添加订单
                            </Button>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent>
                        {affectedOrders.length === 0 ? (
                          <div className="text-center py-4 text-slate-400 text-sm">
                            暂无受影响订单
                          </div>
                        ) : (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>订单类型</TableHead>
                                <TableHead>订单号</TableHead>
                                <TableHead>处理方式</TableHead>
                                <TableHead>状态</TableHead>
                                <TableHead className="text-right">
                                  操作
                                </TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {affectedOrders.map((order) => (
                                <TableRow key={order.id}>
                                  <TableCell>{order.order_type}</TableCell>
                                  <TableCell className="font-mono text-sm">
                                    {order.order_no}
                                  </TableCell>
                                  <TableCell>
                                    {order.action_type || "-"}
                                  </TableCell>
                                  <TableCell>
                                    <Badge
                                      className={
                                        order.status === "PROCESSED"
                                          ? "bg-green-500"
                                          : "bg-amber-500"
                                      }
                                    >
                                      {order.status === "PROCESSED"
                                        ? "已处理"
                                        : "待处理"}
                                    </Badge>
                                  </TableCell>
                                  <TableCell className="text-right">
                                    <div className="flex items-center justify-end gap-2">
                                      {(selectedECN.status === "DRAFT" ||
                                        selectedECN.status === "SUBMITTED" ||
                                        selectedECN.status ===
                                          "EVALUATING") && (
                                        <>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() =>
                                              handleEditOrder(order)
                                            }
                                          >
                                            <FileEdit className="w-4 h-4" />
                                          </Button>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() =>
                                              handleDeleteOrder(order.id)
                                            }
                                          >
                                            <X className="w-4 h-4" />
                                          </Button>
                                        </>
                                      )}
                                    </div>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                {/* 模块集成 */}
                <TabsContent value="integration" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* BOM同步 */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">BOM同步</CardTitle>
                        <CardDescription>将ECN变更同步到BOM</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <div className="text-sm text-slate-500">同步状态</div>
                          <Badge className="bg-slate-500">未同步</Badge>
                        </div>
                        <Button
                          className="w-full"
                          onClick={async () => {
                            if (!confirm("确认同步ECN变更到BOM？")) return;
                            try {
                              await ecnApi.syncToBom(selectedECN.id);
                              alert("BOM同步成功");
                              await fetchECNDetail(selectedECN.id);
                            } catch (error) {
                              console.error("Failed to sync to BOM:", error);
                              alert(
                                "BOM同步失败: " +
                                  (error.response?.data?.detail ||
                                    error.message),
                              );
                            }
                          }}
                          disabled={
                            selectedECN.status !== "APPROVED" &&
                            selectedECN.status !== "EXECUTING"
                          }
                        >
                          <RefreshCw className="w-4 h-4 mr-2" />
                          同步到BOM
                        </Button>
                        <div className="text-xs text-slate-400">
                          {selectedECN.status !== "APPROVED" &&
                            selectedECN.status !== "EXECUTING" &&
                            "仅已审批或执行中的ECN可以同步"}
                        </div>
                      </CardContent>
                    </Card>

                    {/* 项目同步 */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">项目同步</CardTitle>
                        <CardDescription>将ECN变更同步到项目</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <div className="text-sm text-slate-500">同步状态</div>
                          <Badge className="bg-slate-500">未同步</Badge>
                        </div>
                        <Button
                          className="w-full"
                          onClick={async () => {
                            if (!confirm("确认同步ECN变更到项目？")) return;
                            try {
                              await ecnApi.syncToProject(selectedECN.id);
                              alert("项目同步成功");
                              await fetchECNDetail(selectedECN.id);
                            } catch (error) {
                              console.error(
                                "Failed to sync to project:",
                                error,
                              );
                              alert(
                                "项目同步失败: " +
                                  (error.response?.data?.detail ||
                                    error.message),
                              );
                            }
                          }}
                          disabled={
                            selectedECN.status !== "APPROVED" &&
                            selectedECN.status !== "EXECUTING"
                          }
                        >
                          <RefreshCw className="w-4 h-4 mr-2" />
                          同步到项目
                        </Button>
                        <div className="text-xs text-slate-400">
                          {selectedECN.status !== "APPROVED" &&
                            selectedECN.status !== "EXECUTING" &&
                            "仅已审批或执行中的ECN可以同步"}
                        </div>
                      </CardContent>
                    </Card>

                    {/* 采购同步 */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">采购同步</CardTitle>
                        <CardDescription>将ECN变更同步到采购</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <div className="text-sm text-slate-500">同步状态</div>
                          <Badge className="bg-slate-500">未同步</Badge>
                        </div>
                        <Button
                          className="w-full"
                          onClick={async () => {
                            if (!confirm("确认同步ECN变更到采购？")) return;
                            try {
                              await ecnApi.syncToPurchase(selectedECN.id);
                              alert("采购同步成功");
                              await fetchECNDetail(selectedECN.id);
                            } catch (error) {
                              console.error(
                                "Failed to sync to purchase:",
                                error,
                              );
                              alert(
                                "采购同步失败: " +
                                  (error.response?.data?.detail ||
                                    error.message),
                              );
                            }
                          }}
                          disabled={
                            selectedECN.status !== "APPROVED" &&
                            selectedECN.status !== "EXECUTING"
                          }
                        >
                          <RefreshCw className="w-4 h-4 mr-2" />
                          同步到采购
                        </Button>
                        <div className="text-xs text-slate-400">
                          {selectedECN.status !== "APPROVED" &&
                            selectedECN.status !== "EXECUTING" &&
                            "仅已审批或执行中的ECN可以同步"}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* 同步历史记录 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">同步历史记录</CardTitle>
                      <CardDescription>
                        查看ECN同步到各模块的历史记录
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-center py-4 text-slate-400 text-sm">
                        暂无同步历史记录
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                {/* 变更日志 */}
                <TabsContent value="logs" className="space-y-4">
                  {logs.length === 0 ? (
                    <div className="text-center py-8 text-slate-400">
                      暂无日志记录
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {logs.map((log, index) => (
                        <div
                          key={log.id || index}
                          className="flex items-start gap-4 p-3 bg-slate-50 rounded-lg"
                        >
                          <div className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-500 mt-2" />
                          <div className="flex-1">
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-medium">
                                  {log.log_action || log.action}
                                </div>
                                {log.old_status && log.new_status && (
                                  <div className="text-sm text-slate-500 mt-1">
                                    状态变更:{" "}
                                    {statusConfigs[log.old_status]?.label ||
                                      log.old_status}{" "}
                                    →{" "}
                                    {statusConfigs[log.new_status]?.label ||
                                      log.new_status}
                                  </div>
                                )}
                                {log.log_content && (
                                  <div className="text-sm text-slate-600 mt-1">
                                    {log.log_content}
                                  </div>
                                )}
                              </div>
                              <div className="text-xs text-slate-400">
                                {log.created_at
                                  ? formatDate(log.created_at)
                                  : "-"}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            )}
          </DialogBody>
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

      {/* Create Evaluation Dialog */}
      <Dialog
        open={showEvaluationDialog}
        onOpenChange={setShowEvaluationDialog}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建评估</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  评估部门 *
                </label>
                <Input
                  value={evaluationForm.eval_dept}
                  onChange={(e) =>
                    setEvaluationForm({
                      ...evaluationForm,
                      eval_dept: e.target.value,
                    })
                  }
                  placeholder="如：机械部、电气部、采购部等"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    成本估算
                  </label>
                  <Input
                    type="number"
                    value={evaluationForm.cost_estimate}
                    onChange={(e) =>
                      setEvaluationForm({
                        ...evaluationForm,
                        cost_estimate: parseFloat(e.target.value) || 0,
                      })
                    }
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    工期估算（天）
                  </label>
                  <Input
                    type="number"
                    value={evaluationForm.schedule_estimate}
                    onChange={(e) =>
                      setEvaluationForm({
                        ...evaluationForm,
                        schedule_estimate: parseInt(e.target.value) || 0,
                      })
                    }
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  影响分析
                </label>
                <Textarea
                  value={evaluationForm.impact_analysis}
                  onChange={(e) =>
                    setEvaluationForm({
                      ...evaluationForm,
                      impact_analysis: e.target.value,
                    })
                  }
                  rows={3}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  资源需求
                </label>
                <Textarea
                  value={evaluationForm.resource_requirement}
                  onChange={(e) =>
                    setEvaluationForm({
                      ...evaluationForm,
                      resource_requirement: e.target.value,
                    })
                  }
                  rows={2}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  风险评估
                </label>
                <Textarea
                  value={evaluationForm.risk_assessment}
                  onChange={(e) =>
                    setEvaluationForm({
                      ...evaluationForm,
                      risk_assessment: e.target.value,
                    })
                  }
                  rows={2}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  评估结论 *
                </label>
                <Select
                  value={evaluationForm.eval_result}
                  onValueChange={(val) =>
                    setEvaluationForm({ ...evaluationForm, eval_result: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="APPROVED">通过</SelectItem>
                    <SelectItem value="CONDITIONAL">有条件通过</SelectItem>
                    <SelectItem value="REJECTED">不通过</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  评估意见
                </label>
                <Textarea
                  value={evaluationForm.eval_opinion}
                  onChange={(e) =>
                    setEvaluationForm({
                      ...evaluationForm,
                      eval_opinion: e.target.value,
                    })
                  }
                  rows={2}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  附加条件
                </label>
                <Textarea
                  value={evaluationForm.conditions}
                  onChange={(e) =>
                    setEvaluationForm({
                      ...evaluationForm,
                      conditions: e.target.value,
                    })
                  }
                  rows={2}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowEvaluationDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreateEvaluation}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Task Dialog */}
      <Dialog open={showTaskDialog} onOpenChange={setShowTaskDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建执行任务</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  任务名称 *
                </label>
                <Input
                  value={taskForm.task_name}
                  onChange={(e) =>
                    setTaskForm({ ...taskForm, task_name: e.target.value })
                  }
                  placeholder="如：更新BOM中的物料型号"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    任务类型
                  </label>
                  <Input
                    value={taskForm.task_type}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, task_type: e.target.value })
                    }
                    placeholder="如：BOM_UPDATE"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    责任部门
                  </label>
                  <Input
                    value={taskForm.task_dept}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, task_dept: e.target.value })
                    }
                    placeholder="如：机械部"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  任务描述
                </label>
                <Textarea
                  value={taskForm.task_description}
                  onChange={(e) =>
                    setTaskForm({
                      ...taskForm,
                      task_description: e.target.value,
                    })
                  }
                  rows={3}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  交付物要求
                </label>
                <Textarea
                  value={taskForm.deliverables}
                  onChange={(e) =>
                    setTaskForm({ ...taskForm, deliverables: e.target.value })
                  }
                  rows={2}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划开始日期
                  </label>
                  <Input
                    type="date"
                    value={taskForm.planned_start}
                    onChange={(e) =>
                      setTaskForm({
                        ...taskForm,
                        planned_start: e.target.value,
                      })
                    }
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划结束日期
                  </label>
                  <Input
                    type="date"
                    value={taskForm.planned_end}
                    onChange={(e) =>
                      setTaskForm({ ...taskForm, planned_end: e.target.value })
                    }
                  />
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTaskDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateTask}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Affected Material Dialog */}
      <Dialog open={showMaterialDialog} onOpenChange={setShowMaterialDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingMaterial ? "编辑受影响物料" : "添加受影响物料"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  选择物料
                </label>
                <Select
                  value={$?.toString() || "__none__"}
                  onValueChange={(val) => handleMaterialSelect(parseInt(val))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择物料（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__empty__">手动输入</SelectItem>
                    {materials.map((mat) => (
                      <SelectItem key={mat.id} value={mat.id.toString()}>
                        {mat.material_code} - {mat.material_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    物料编码 *
                  </label>
                  <Input
                    value={materialForm.material_code}
                    onChange={(e) =>
                      setMaterialForm({
                        ...materialForm,
                        material_code: e.target.value,
                      })
                    }
                    placeholder="物料编码"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    物料名称 *
                  </label>
                  <Input
                    value={materialForm.material_name}
                    onChange={(e) =>
                      setMaterialForm({
                        ...materialForm,
                        material_name: e.target.value,
                      })
                    }
                    placeholder="物料名称"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  规格型号
                </label>
                <Input
                  value={materialForm.specification}
                  onChange={(e) =>
                    setMaterialForm({
                      ...materialForm,
                      specification: e.target.value,
                    })
                  }
                  placeholder="规格型号"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  变更类型 *
                </label>
                <Select
                  value={materialForm.change_type}
                  onValueChange={(val) =>
                    setMaterialForm({ ...materialForm, change_type: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ADD">新增</SelectItem>
                    <SelectItem value="UPDATE">更新</SelectItem>
                    <SelectItem value="DELETE">删除</SelectItem>
                    <SelectItem value="REPLACE">替换</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {(materialForm.change_type === "UPDATE" ||
                materialForm.change_type === "REPLACE") && (
                <>
                  <div className="border-t pt-4">
                    <div className="text-sm font-medium mb-3">变更前信息</div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">
                          原数量
                        </label>
                        <Input
                          type="number"
                          value={materialForm.old_quantity}
                          onChange={(e) =>
                            setMaterialForm({
                              ...materialForm,
                              old_quantity: e.target.value,
                            })
                          }
                          placeholder="原数量"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">
                          原规格
                        </label>
                        <Input
                          value={materialForm.old_specification}
                          onChange={(e) =>
                            setMaterialForm({
                              ...materialForm,
                              old_specification: e.target.value,
                            })
                          }
                          placeholder="原规格型号"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="border-t pt-4">
                    <div className="text-sm font-medium mb-3">变更后信息</div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium mb-2 block">
                          新数量
                        </label>
                        <Input
                          type="number"
                          value={materialForm.new_quantity}
                          onChange={(e) =>
                            setMaterialForm({
                              ...materialForm,
                              new_quantity: e.target.value,
                            })
                          }
                          placeholder="新数量"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-2 block">
                          新规格
                        </label>
                        <Input
                          value={materialForm.new_specification}
                          onChange={(e) =>
                            setMaterialForm({
                              ...materialForm,
                              new_specification: e.target.value,
                            })
                          }
                          placeholder="新规格型号"
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  成本影响
                </label>
                <Input
                  type="number"
                  value={materialForm.cost_impact}
                  onChange={(e) =>
                    setMaterialForm({
                      ...materialForm,
                      cost_impact: parseFloat(e.target.value) || 0,
                    })
                  }
                  placeholder="成本影响金额"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">备注</label>
                <Textarea
                  value={materialForm.remark}
                  onChange={(e) =>
                    setMaterialForm({ ...materialForm, remark: e.target.value })
                  }
                  rows={2}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowMaterialDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleSaveMaterial}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Affected Order Dialog */}
      <Dialog open={showOrderDialog} onOpenChange={setShowOrderDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {editingOrder ? "编辑受影响订单" : "添加受影响订单"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  订单类型 *
                </label>
                <Select
                  value={orderForm.order_type}
                  onValueChange={(val) =>
                    setOrderForm({
                      ...orderForm,
                      order_type: val,
                      order_id: null,
                      order_no: "",
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PURCHASE">采购订单</SelectItem>
                    <SelectItem value="OUTSOURCING">外协订单</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  选择订单
                </label>
                <Select
                  value={$?.toString() || "__none__"}
                  onValueChange={(val) => {
                    const order = purchaseOrders.find(
                      (o) => o.id === parseInt(val),
                    );
                    if (order) {
                      setOrderForm({
                        ...orderForm,
                        order_id: order.id,
                        order_no: order.order_no || order.po_no || "",
                      });
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择订单（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__empty__">手动输入</SelectItem>
                    {purchaseOrders
                      .filter(
                        (o) =>
                          orderForm.order_type === "PURCHASE" ||
                          o.order_type === orderForm.order_type,
                      )
                      .map((order) => (
                        <SelectItem key={order.id} value={order.id.toString()}>
                          {order.order_no || order.po_no} -{" "}
                          {order.supplier_name || ""}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  订单号 *
                </label>
                <Input
                  value={orderForm.order_no}
                  onChange={(e) =>
                    setOrderForm({ ...orderForm, order_no: e.target.value })
                  }
                  placeholder="订单号"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  影响描述
                </label>
                <Textarea
                  value={orderForm.impact_description}
                  onChange={(e) =>
                    setOrderForm({
                      ...orderForm,
                      impact_description: e.target.value,
                    })
                  }
                  rows={3}
                  placeholder="描述ECN对此订单的影响"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  处理方式
                </label>
                <Select
                  value={orderForm.action_type}
                  onValueChange={(val) =>
                    setOrderForm({ ...orderForm, action_type: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择处理方式" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    <SelectItem value="CANCEL">取消订单</SelectItem>
                    <SelectItem value="MODIFY">修改订单</SelectItem>
                    <SelectItem value="DELAY">延期交付</SelectItem>
                    <SelectItem value="REPLACE">替换物料</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  处理说明
                </label>
                <Textarea
                  value={orderForm.action_description}
                  onChange={(e) =>
                    setOrderForm({
                      ...orderForm,
                      action_description: e.target.value,
                    })
                  }
                  rows={2}
                  placeholder="详细说明处理方式"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowOrderDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveOrder}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
