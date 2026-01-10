import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileText,
  ArrowLeft,
  Edit,
  Trash2,
  Send,
  CheckCircle2,
  XCircle,
  Clock,
  Calendar,
  Building2,
  DollarSign,
  Package,
  User,
  MessageSquare,
  Loader2,
  ShoppingCart,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Label } from "../components/ui/label";
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
import { Textarea } from "../components/ui/textarea";
import { cn } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import { purchaseApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { LoadingCard } from "../components/common";
import { ErrorMessage } from "../components/common";
import { EmptyState } from "../components/common";

// 状态配置
const STATUS_CONFIG = {
  DRAFT: { label: "草稿", color: "bg-gray-500", icon: FileText },
  SUBMITTED: { label: "待审批", color: "bg-blue-500", icon: Clock },
  APPROVED: { label: "已审批", color: "bg-emerald-500", icon: CheckCircle2 },
  REJECTED: { label: "已驳回", color: "bg-red-500", icon: XCircle },
  CLOSED: { label: "已关闭", color: "bg-slate-500", icon: Package },
};

export default function PurchaseRequestDetail() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [request, setRequest] = useState(null);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [approveData, setApproveData] = useState({ approved: true, note: "" });
  const [generating, setGenerating] = useState(false);

  // Check if demo account  // Load request data
  useEffect(() => {
    const loadRequest = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await purchaseApi.requests.get(id);
        const data = res.data?.data || res.data;
        setRequest(data);
      } catch (err) {
        console.error("Failed to load request:", err);
        setError(err.response?.data?.detail || "加载失败");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      loadRequest();
    }
  }, [id]);

  const handleEdit = () => {
    navigate(`/purchase-requests/${id}/edit`);
  };

  const handleDelete = async () => {
    if (!confirm(`确定要删除采购申请 ${request?.request_no} 吗？`)) {
      return;
    }

    try {
      await purchaseApi.requests.delete(id);
      toast.success("采购申请已删除");
      navigate("/purchase-requests");
    } catch (err) {
      console.error("Failed to delete request:", err);
      toast.error(err.response?.data?.detail || "删除失败");
    }
  };

  const handleSubmit = async () => {
    if (request.status !== "DRAFT") {
      toast.error("只有草稿状态的申请才能提交");
      return;
    }

    try {
      await purchaseApi.requests.submit(id);
      toast.success("采购申请已提交，等待审批");
      // Reload request
      const res = await purchaseApi.requests.get(id);
      setRequest(res.data?.data || res.data);
    } catch (err) {
      console.error("Failed to submit request:", err);
      toast.error(err.response?.data?.detail || "提交失败");
    }
  };

  const handleGenerateOrders = async () => {
    if (!id) return;
    try {
      setGenerating(true);
      await purchaseApi.requests.generateOrders(id);
      toast.success("已生成采购订单");
      const res = await purchaseApi.requests.get(id);
      setRequest(res.data?.data || res.data);
    } catch (err) {
      console.error("Failed to generate orders:", err);
      toast.error(err.response?.data?.detail || "生成采购订单失败");
    } finally {
      setGenerating(false);
    }
  };

  const handleApprove = async (approved, note) => {
    if (request.status !== "SUBMITTED") {
      toast.error("只有待审批状态的申请才能审批");
      return;
    }

    try {
      await purchaseApi.requests.approve(id, {
        approved,
        approval_note: note,
      });
      toast.success(approved ? "采购申请已审批通过" : "采购申请已驳回");
      setShowApproveDialog(false);
      // Reload request
      const res = await purchaseApi.requests.get(id);
      setRequest(res.data?.data || res.data);
    } catch (err) {
      console.error("Failed to approve request:", err);
      toast.error(err.response?.data?.detail || "审批失败");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <LoadingCard />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage
            message={error}
            onRetry={() => window.location.reload()}
          />
        </div>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <EmptyState
            icon={FileText}
            title="采购申请不存在"
            description="该采购申请可能已被删除"
          />
        </div>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[request.status] || STATUS_CONFIG.DRAFT;
  const StatusIcon = statusConfig.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="采购申请详情"
          description={request.request_no}
          actions={
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => navigate("/purchase-requests")}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
              {request.status === "DRAFT" && (
                <>
                  <Button variant="outline" onClick={handleEdit}>
                    <Edit className="w-4 h-4 mr-2" />
                    编辑
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleDelete}
                    className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    删除
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    提交审批
                  </Button>
                </>
              )}
              {request.status === "SUBMITTED" && (
                <Button
                  onClick={() => setShowApproveDialog(true)}
                  className="bg-emerald-600 hover:bg-emerald-700"
                >
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  审批
                </Button>
              )}
              {request.status === "APPROVED" && !request.auto_po_created && (
                <Button
                  variant="outline"
                  onClick={handleGenerateOrders}
                  disabled={generating}
                  className="border-amber-400/40 text-amber-300 hover:bg-amber-500/10"
                >
                  {generating ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <ShoppingCart className="w-4 h-4 mr-2" />
                  )}
                  {generating ? "生成中..." : "生成采购订单"}
                </Button>
              )}
            </div>
          }
        />

        <motion.div
          variants={fadeIn}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-slate-200">基本信息</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge className={cn(statusConfig.color)}>
                      <StatusIcon className="w-3 h-3 mr-1" />
                      {statusConfig.label}
                    </Badge>
                    {request.auto_po_created && (
                      <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30">
                        已生成采购订单
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">申请单号</Label>
                    <p className="text-slate-200 font-mono">
                      {request.request_no}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">申请类型</Label>
                    <p className="text-slate-200">
                      {request.request_type === "URGENT" ? (
                        <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                          紧急
                        </Badge>
                      ) : (
                        <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                          普通
                        </Badge>
                      )}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">所属项目</Label>
                    <p className="text-slate-200">
                      {request.project_name || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">设备</Label>
                    <p className="text-slate-200">
                      {request.machine_name || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">供应商</Label>
                    <p className="text-slate-200">
                      {request.supplier_name || "未指定"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">需求日期</Label>
                    <p className="text-slate-200">
                      {request.required_date || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-400">申请人</Label>
                    <p className="text-slate-200">
                      {request.requester_name || "-"}
                    </p>
                  </div>
                  {request.submitted_at && (
                    <div>
                      <Label className="text-slate-400">提交时间</Label>
                      <p className="text-slate-200">
                        {new Date(request.submitted_at).toLocaleString("zh-CN")}
                      </p>
                    </div>
                  )}
                  {request.approved_at && (
                    <div>
                      <Label className="text-slate-400">审批时间</Label>
                      <p className="text-slate-200">
                        {new Date(request.approved_at).toLocaleString("zh-CN")}
                      </p>
                    </div>
                  )}
                </div>
                {request.request_reason && (
                  <div>
                    <Label className="text-slate-400">申请原因</Label>
                    <p className="text-slate-200 whitespace-pre-wrap">
                      {request.request_reason}
                    </p>
                  </div>
                )}
                {request.approval_note && (
                  <div>
                    <Label className="text-slate-400">审批意见</Label>
                    <p className="text-slate-200 whitespace-pre-wrap">
                      {request.approval_note}
                    </p>
                  </div>
                )}
                {request.remark && (
                  <div>
                    <Label className="text-slate-400">备注</Label>
                    <p className="text-slate-200 whitespace-pre-wrap">
                      {request.remark}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Items */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">物料明细</CardTitle>
              </CardHeader>
              <CardContent>
                {!request.items || request.items.length === 0 ? (
                  <EmptyState
                    icon={Package}
                    title="暂无物料明细"
                    description="该申请单没有物料明细"
                  />
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-400">序号</TableHead>
                          <TableHead className="text-slate-400">
                            物料编码
                          </TableHead>
                          <TableHead className="text-slate-400">
                            物料名称
                          </TableHead>
                          <TableHead className="text-slate-400">规格</TableHead>
                          <TableHead className="text-slate-400">单位</TableHead>
                          <TableHead className="text-slate-400 text-right">
                            数量
                          </TableHead>
                          <TableHead className="text-slate-400 text-right">
                            单价
                          </TableHead>
                          <TableHead className="text-slate-400 text-right">
                            金额
                          </TableHead>
                          <TableHead className="text-slate-400">
                            需求日期
                          </TableHead>
                          <TableHead className="text-slate-400 text-right">
                            已采购
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {request.items.map((item, index) => (
                          <TableRow
                            key={item.id || index}
                            className="border-slate-700"
                          >
                            <TableCell className="text-slate-300">
                              {index + 1}
                            </TableCell>
                            <TableCell className="text-slate-300 font-mono text-xs">
                              {item.material_code}
                            </TableCell>
                            <TableCell className="text-slate-300">
                              {item.material_name}
                            </TableCell>
                            <TableCell className="text-slate-400 text-sm">
                              {item.specification || "-"}
                            </TableCell>
                            <TableCell className="text-slate-300">
                              {item.unit}
                            </TableCell>
                            <TableCell className="text-slate-300 text-right">
                              {item.quantity}
                            </TableCell>
                            <TableCell className="text-slate-300 text-right">
                              ¥{item.unit_price?.toFixed(2)}
                            </TableCell>
                            <TableCell className="text-slate-200 text-right font-medium">
                              ¥{item.amount?.toFixed(2)}
                            </TableCell>
                            <TableCell className="text-slate-400 text-sm">
                              {item.required_date || "-"}
                            </TableCell>
                            <TableCell className="text-slate-300 text-right">
                              {item.ordered_qty > 0 ? (
                                <Badge className="bg-emerald-500/20 text-emerald-400">
                                  {item.ordered_qty}
                                </Badge>
                              ) : (
                                <span className="text-slate-500">0</span>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Summary */}
            <Card className="bg-slate-800/50 border-slate-700/50 sticky top-6">
              <CardHeader>
                <CardTitle className="text-slate-200">汇总信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-slate-400">物料数量</Label>
                  <p className="text-2xl font-bold text-slate-200">
                    {request.items?.length || 0}
                  </p>
                </div>
                <div>
                  <Label className="text-slate-400">总金额</Label>
                  <p className="text-2xl font-bold text-emerald-400">
                    ¥{request.total_amount?.toFixed(2) || "0.00"}
                  </p>
                </div>
                <div className="pt-4 border-t border-slate-700">
                  <Label className="text-slate-400">创建时间</Label>
                  <p className="text-slate-300 text-sm">
                    {new Date(request.created_at).toLocaleString("zh-CN")}
                  </p>
                </div>
                {request.updated_at && (
                  <div>
                    <Label className="text-slate-400">更新时间</Label>
                    <p className="text-slate-300 text-sm">
                      {new Date(request.updated_at).toLocaleString("zh-CN")}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Order Generation */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">采购订单生成</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-sm">自动下单状态</span>
                  <Badge
                    className={
                      request.auto_po_created
                        ? "bg-emerald-500/20 text-emerald-300"
                        : "bg-slate-700/60 text-slate-200"
                    }
                  >
                    {request.auto_po_created ? "已生成" : "待生成"}
                  </Badge>
                </div>
                {request.generated_orders &&
                request.generated_orders.length > 0 ? (
                  <div className="space-y-3">
                    {request.generated_orders.map((order) => (
                      <div
                        key={order.id}
                        className="p-3 rounded-lg border border-slate-700 bg-slate-900/40"
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-slate-100 font-mono text-sm">
                            {order.order_no}
                          </p>
                          <Badge className="bg-slate-700/60 text-slate-200 text-[10px]">
                            {order.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-400 mt-2">
                          含税金额 ¥
                          {parseFloat(
                            order.amount_with_tax || order.total_amount || 0,
                          ).toFixed(2)}
                        </p>
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-full mt-3"
                          onClick={() =>
                            navigate(`/purchase-orders/${order.id}`)
                          }
                        >
                          查看采购订单
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-slate-500 text-sm">
                    暂无生成的采购订单
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </motion.div>

        {/* Approve Dialog */}
        <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
          <DialogContent className="bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">审批采购申请</DialogTitle>
            </DialogHeader>
            <DialogBody>
              <div className="space-y-4">
                <div>
                  <Label className="text-slate-400">申请单号</Label>
                  <p className="text-slate-200">{request.request_no}</p>
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
                    rows={4}
                  />
                </div>
              </div>
            </DialogBody>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  handleApprove(false, approveData.note);
                }}
                className="border-red-500 text-red-400 hover:bg-red-500/10"
              >
                驳回
              </Button>
              <Button
                onClick={() => {
                  handleApprove(true, approveData.note);
                }}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                审批通过
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
