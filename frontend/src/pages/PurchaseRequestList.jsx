import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Plus,
  Search,
  Filter,
  Eye,
  Edit3,
  Trash2,
  CheckCircle2,
  Clock,
  XCircle,
  Send,
  Calendar,
  Building2,
  DollarSign,
  Package,
  AlertTriangle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody } from
"../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { purchaseApi, projectApi, materialApi as _materialApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { LoadingCard } from "../components/common";
import { EmptyState } from "../components/common";
import { ErrorMessage } from "../components/common";

// 状态配置
import { confirmAction } from "@/lib/confirmAction";
const STATUS_CONFIG = {
  DRAFT: { label: "草稿", color: "bg-gray-500", icon: FileText },
  SUBMITTED: { label: "待审批", color: "bg-blue-500", icon: Clock },
  APPROVED: { label: "已审批", color: "bg-emerald-500", icon: CheckCircle2 },
  REJECTED: { label: "已驳回", color: "bg-red-500", icon: XCircle },
  CLOSED: { label: "已关闭", color: "bg-slate-500", icon: Package }
};

function PurchaseRequestCard({
  request,
  onView,
  onEdit,
  onDelete,
  onSubmit,
  onApprove
}) {
  const statusConfig = STATUS_CONFIG[request.status] || STATUS_CONFIG.DRAFT;
  const StatusIcon = statusConfig.icon;

  return (
    <motion.div
      variants={fadeIn}
      className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 hover:border-slate-600 transition-colors">

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-slate-200">
              {request.request_no}
            </h3>
            <Badge className={cn("text-xs", statusConfig.color)}>
              <StatusIcon className="w-3 h-3 mr-1" />
              {statusConfig.label}
            </Badge>
            {request.request_type === "URGENT" &&
            <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs">
                紧急
            </Badge>
            }
            {request.auto_po_created &&
            <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30 text-xs">
                已生成采购订单
            </Badge>
            }
          </div>
          <p className="text-xs text-slate-400">
            {request.project_name}
            {request.machine_name && ` / ${request.machine_name}`}
          </p>
          {request.supplier_name &&
          <p className="text-xs text-slate-500 mt-1">
              供应商：{request.supplier_name}
          </p>
          }
        </div>
      </div>

      {/* Info */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <DollarSign className="w-3.5 h-3.5" />
          <span>
            总金额：¥{request.total_amount?.toLocaleString() || "0.00"}
          </span>
        </div>
        {request.required_date &&
        <div className="flex items-center gap-2 text-xs text-slate-400">
            <Calendar className="w-3.5 h-3.5" />
            <span>需求日期：{request.required_date}</span>
        </div>
        }
        {request.request_reason &&
        <p className="text-xs text-slate-400 line-clamp-2">
            {request.request_reason}
        </p>
        }
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-border/50">
        <span className="text-xs text-slate-500">
          申请人：{request.requester_name || "未知"}
        </span>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={() => onView(request)}
            title="查看详情">

            <Eye className="w-3.5 h-3.5" />
          </Button>
          {request.status === "DRAFT" && onEdit &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={() => onEdit(request)}
            title="编辑">

              <Edit3 className="w-3.5 h-3.5" />
          </Button>
          }
          {request.status === "DRAFT" && onDelete &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={() => onDelete(request)}
            title="删除">

              <Trash2 className="w-3.5 h-3.5" />
          </Button>
          }
          {request.status === "DRAFT" && onSubmit &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-blue-400"
            onClick={() => onSubmit(request)}
            title="提交">

              <Send className="w-3.5 h-3.5" />
          </Button>
          }
          {request.status === "SUBMITTED" && onApprove &&
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-emerald-400"
            onClick={async () => {
              if (await confirmAction("确定要审批通过此申请吗？")) {
                onApprove(request, true, "");
              }
            }}
            title="审批通过">

              <CheckCircle2 className="w-3.5 h-3.5" />
          </Button>
          }
        </div>
      </div>
    </motion.div>);

}

export default function PurchaseRequestList() {
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [projectFilter, setProjectFilter] = useState("all");
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [selectedRequestForApprove, setSelectedRequestForApprove] =
  useState(null);
  const [approveData, setApproveData] = useState({ approved: true, note: "" });

  // Projects for filter
  const [projects, setProjects] = useState([]);

  // Load projects
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const res = await projectApi.list({ page_size: 1000 });
        setProjects(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load projects:", err);
      }
    };
    loadProjects();
  }, []);

  // Load requests
  const loadRequests = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100
      };

      if (searchQuery) {
        params.keyword = searchQuery;
      }

      if (statusFilter !== "all") {
        params.status = statusFilter;
      }

      if (projectFilter !== "all") {
        params.project_id = parseInt(projectFilter);
      }

      const res = await purchaseApi.requests.list(params);
      const data = res.data?.data || res.data;

      if (data?.items) {
        setRequests(data.items);
      } else if (Array.isArray(data)) {
        setRequests(data);
      } else {
        setRequests([]);
      }
    } catch (err) {
      console.error("Failed to load purchase requests:", err);
      setError(err.response?.data?.detail || err.message || "加载采购申请失败");
    } finally {
      setLoading(false);
    }
  }, [searchQuery, statusFilter, projectFilter]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  // Filter requests
  const filteredRequests = useMemo(() => {
    if (!Array.isArray(requests)) {return [];}
    return (requests || []).filter((req) => {
      if (
      searchQuery &&
      !req.request_no?.toLowerCase().includes(searchQuery.toLowerCase()))
      {
        return false;
      }
      if (statusFilter !== "all" && req.status !== statusFilter) {
        return false;
      }
      if (
      projectFilter !== "all" &&
      req.project_id !== parseInt(projectFilter))
      {
        return false;
      }
      return true;
    });
  }, [requests, searchQuery, statusFilter, projectFilter]);

  // Stats
  const stats = useMemo(() => {
    if (!Array.isArray(requests))
    {return { total: 0, draft: 0, submitted: 0, approved: 0, rejected: 0 };}
    return {
      total: requests.length,
      draft: (requests || []).filter((r) => r.status === "DRAFT").length,
      submitted: (requests || []).filter((r) => r.status === "SUBMITTED").length,
      approved: (requests || []).filter((r) => r.status === "APPROVED").length,
      rejected: (requests || []).filter((r) => r.status === "REJECTED").length
    };
  }, [requests]);

  const handleView = (request) => {
    navigate(`/purchase-requests/${request.id}`);
  };

  const handleEdit = (request) => {
    navigate(`/purchase-requests/${request.id}/edit`);
  };

  const handleDelete = async (request) => {
    if (!await confirmAction(`确定要删除采购申请 ${request.request_no} 吗？`)) {
      return;
    }

    try {
      await purchaseApi.requests.delete(request.id);
      toast.success("采购申请已删除");
      loadRequests();
    } catch (err) {
      console.error("Failed to delete request:", err);
      toast.error(err.response?.data?.detail || "删除失败");
    }
  };

  const handleSubmit = async (request) => {
    if (request.status !== "DRAFT") {
      toast.error("只有草稿状态的申请才能提交");
      return;
    }

    try {
      await purchaseApi.requests.submit(request.id);
      toast.success("采购申请已提交，等待审批");
      loadRequests();
    } catch (err) {
      console.error("Failed to submit request:", err);
      toast.error(err.response?.data?.detail || "提交失败");
    }
  };

  const handleApprove = async (request, approved, note) => {
    if (request.status !== "SUBMITTED") {
      toast.error("只有待审批状态的申请才能审批");
      return;
    }

    try {
      await purchaseApi.requests.approve(request.id, {
        approved,
        approval_note: note
      });
      toast.success(approved ? "采购申请已审批通过" : "采购申请已驳回");
      loadRequests();
      setShowApproveDialog(false);
    } catch (err) {
      console.error("Failed to approve request:", err);
      toast.error(err.response?.data?.detail || "审批失败");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="采购申请管理"
          description="管理项目采购申请，提交审批流程"
          actions={
          <Button
            onClick={() => navigate("/purchase-requests/new")}
            className="bg-blue-600 hover:bg-blue-700">

              <Plus className="w-4 h-4 mr-2" />
              新建申请
          </Button>
          } />


        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">总数</div>
              <div className="text-2xl font-bold text-slate-200">
                {stats.total}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">草稿</div>
              <div className="text-2xl font-bold text-gray-400">
                {stats.draft}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">待审批</div>
              <div className="text-2xl font-bold text-blue-400">
                {stats.submitted}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已审批</div>
              <div className="text-2xl font-bold text-emerald-400">
                {stats.approved}
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已驳回</div>
              <div className="text-2xl font-bold text-red-400">
                {stats.rejected}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <Input
                  placeholder="搜索申请单号..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  icon={Search}
                  className="bg-slate-900/50 border-slate-700" />

              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-[180px] bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="状态筛选" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="DRAFT">草稿</SelectItem>
                  <SelectItem value="SUBMITTED">待审批</SelectItem>
                  <SelectItem value="APPROVED">已审批</SelectItem>
                  <SelectItem value="REJECTED">已驳回</SelectItem>
                </SelectContent>
              </Select>
              <Select value={projectFilter} onValueChange={setProjectFilter}>
                <SelectTrigger className="w-full md:w-[180px] bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="项目筛选" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部项目</SelectItem>
                  {(projects || []).map((project) =>
                  <SelectItem key={project.id} value={String(project.id)}>
                      {project.project_name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && <ErrorMessage message={error} onRetry={loadRequests} />}

        {/* Loading */}
        {loading && <LoadingCard />}

        {/* Requests List */}
        {!loading && !error &&
        <>
            {filteredRequests.length === 0 ?
          <EmptyState
            icon={FileText}
            title="暂无采购申请"
            description="点击上方按钮创建新的采购申请" /> :


          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

                <AnimatePresence>
                  {(filteredRequests || []).map((request) =>
              <PurchaseRequestCard
                key={request.id}
                request={request}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onSubmit={handleSubmit}
                onApprove={(req) => {
                  setSelectedRequestForApprove(req);
                  setApproveData({ approved: true, note: "" });
                  setShowApproveDialog(true);
                }} />

              )}
                </AnimatePresence>
          </motion.div>
          }
        </>
        }

        {/* Approve Dialog */}
        {selectedRequestForApprove &&
        <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
            <DialogContent className="bg-slate-900 border-slate-700">
              <DialogHeader>
                <DialogTitle className="text-slate-200">
                  审批采购申请
                </DialogTitle>
              </DialogHeader>
              <DialogBody>
                <div className="space-y-4">
                  <div>
                    <Label className="text-slate-400">申请单号</Label>
                    <p className="text-slate-200">
                      {selectedRequestForApprove.request_no}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">审批意见</Label>
                    <Textarea
                    value={approveData.note}
                    onChange={(e) =>
                    setApproveData({ ...approveData, note: e.target.value })
                    }
                    placeholder="请输入审批意见..."
                    className="bg-slate-800 border-slate-700 text-slate-200"
                    rows={4} />

                  </div>
                </div>
              </DialogBody>
              <DialogFooter>
                <Button
                variant="outline"
                onClick={() => {
                  handleApprove(
                    selectedRequestForApprove,
                    false,
                    approveData.note
                  );
                }}
                className="border-red-500 text-red-400 hover:bg-red-500/10">

                  驳回
                </Button>
                <Button
                onClick={() => {
                  handleApprove(
                    selectedRequestForApprove,
                    true,
                    approveData.note
                  );
                }}
                className="bg-emerald-600 hover:bg-emerald-700">

                  审批通过
                </Button>
              </DialogFooter>
            </DialogContent>
        </Dialog>
        }
      </div>
    </div>);

}
