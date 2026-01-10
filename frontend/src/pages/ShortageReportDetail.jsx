/**
 * Shortage Report Detail - 缺料上报详情页
 * 显示缺料上报的详细信息，支持确认、处理、解决等操作
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Package,
  AlertTriangle,
  CheckCircle2,
  Clock,
  User,
  Calendar,
  MapPin,
  FileText,
  RefreshCw,
  XCircle,
  Edit,
  Truck,
  ArrowRightLeft,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Input,
  Label,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui";
import { cn, formatDate } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import { shortageApi } from "../services/api";

const statusConfigs = {
  REPORTED: { label: "已上报", color: "bg-blue-500", icon: Clock },
  CONFIRMED: { label: "已确认", color: "bg-amber-500", icon: CheckCircle2 },
  HANDLING: { label: "处理中", color: "bg-purple-500", icon: RefreshCw },
  RESOLVED: { label: "已解决", color: "bg-emerald-500", icon: CheckCircle2 },
  REJECTED: { label: "已驳回", color: "bg-red-500", icon: XCircle },
};

const urgentLevelConfigs = {
  NORMAL: {
    label: "普通",
    color: "text-slate-400",
    bgColor: "bg-slate-500/10",
  },
  URGENT: {
    label: "紧急",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
  },
  CRITICAL: { label: "特急", color: "text-red-400", bgColor: "bg-red-500/10" },
};

export default function ShortageReportDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showHandleDialog, setShowHandleDialog] = useState(false);
  const [handleData, setHandleData] = useState({
    solution_type: "ARRIVAL",
    solution_note: "",
  });
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  useEffect(() => {
    loadReport();
  }, [id]);

  const loadReport = async () => {
    setLoading(true);
    try {
      const res = await shortageApi.reports.get(id);
      setReport(res.data);
    } catch (error) {
      console.error("加载缺料上报详情失败", error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!confirm("确认要确认此缺料上报吗？")) return;
    setActionLoading(true);
    try {
      await shortageApi.reports.confirm(id);
      await loadReport();
    } catch (error) {
      console.error("确认失败", error);
      alert("确认失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleHandle = async () => {
    if (!handleData.solution_note.trim()) {
      alert("请输入处理说明");
      return;
    }

    setActionLoading(true);
    try {
      await shortageApi.reports.handle(id, handleData);
      await loadReport();
      setShowHandleDialog(false);
      setHandleData({ solution_type: "ARRIVAL", solution_note: "" });
      alert("处理成功！");
    } catch (error) {
      console.error("处理失败", error);
      alert("处理失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!confirm("确认要标记此缺料上报为已解决吗？")) return;
    setActionLoading(true);
    try {
      await shortageApi.reports.resolve(id);
      await loadReport();
    } catch (error) {
      console.error("解决失败", error);
      alert("解决失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateArrival = () => {
    navigate("/shortage/arrivals/new", {
      state: {
        shortage_report_id: id,
        project_id: report.project_id,
        material_id: report.material_id,
      },
    });
  };

  const handleCreateSubstitution = () => {
    navigate("/shortage/substitutions/new", {
      state: {
        shortage_report_id: id,
        project_id: report.project_id,
        material_id: report.material_id,
      },
    });
  };

  const handleCreateTransfer = () => {
    navigate("/shortage/transfers/new", {
      state: {
        shortage_report_id: id,
        project_id: report.project_id,
        material_id: report.material_id,
      },
    });
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      alert("请输入驳回原因");
      return;
    }

    setActionLoading(true);
    try {
      await shortageApi.reports.reject(id, rejectReason);
      await loadReport();
      setShowRejectDialog(false);
      setRejectReason("");
      alert("驳回成功！");
    } catch (error) {
      console.error("驳回失败", error);
      alert("驳回失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <XCircle className="h-12 w-12 text-muted-foreground" />
        <div className="text-muted-foreground">缺料上报不存在</div>
        <Button variant="outline" onClick={() => navigate("/shortage")}>
          返回列表
        </Button>
      </div>
    );
  }

  const status = statusConfigs[report.status] || statusConfigs.REPORTED;
  const urgent =
    urgentLevelConfigs[report.urgent_level] || urgentLevelConfigs.NORMAL;
  const StatusIcon = status.icon;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/shortage")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader
          title={`缺料上报 - ${report.report_no}`}
          description="查看缺料上报的详细信息和处理进度"
        />
      </div>

      <motion.div
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-6 lg:grid-cols-3"
      >
        {/* 主要信息 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>基本信息</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(urgent.bgColor, urgent.color)}
                  >
                    {urgent.label}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={cn(status.color, "text-white")}
                  >
                    <StatusIcon className="h-3 w-3 mr-1" />
                    {status.label}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">上报单号</div>
                  <div className="font-medium">{report.report_no}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">项目名称</div>
                  <div className="font-medium">
                    {report.project_name || "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">机台名称</div>
                  <div className="font-medium">
                    {report.machine_name || "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">上报时间</div>
                  <div className="font-medium">
                    {formatDate(report.report_time)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">上报地点</div>
                  <div className="font-medium">
                    {report.report_location || "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">上报人</div>
                  <div className="font-medium">
                    {report.reporter_name || "-"}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 物料信息 */}
          <Card>
            <CardHeader>
              <CardTitle>物料信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">物料编码</div>
                  <div className="font-medium">{report.material_code}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">物料名称</div>
                  <div className="font-medium">{report.material_name}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">需求数量</div>
                  <div className="font-medium">{report.required_qty}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">缺料数量</div>
                  <div className="font-medium text-red-400">
                    {report.shortage_qty}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 处理信息 */}
          {(report.confirmed_at ||
            report.handler_id ||
            report.resolved_at ||
            report.solution_type) && (
            <Card>
              <CardHeader>
                <CardTitle>处理信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {report.confirmed_at && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      确认时间
                    </div>
                    <div className="font-medium">
                      {formatDate(report.confirmed_at)}
                    </div>
                  </div>
                )}
                {report.handler_id && (
                  <div>
                    <div className="text-sm text-muted-foreground">处理人</div>
                    <div className="font-medium">
                      {report.handler_name || "-"}
                    </div>
                  </div>
                )}
                {report.solution_type && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      解决方案类型
                    </div>
                    <div className="font-medium">{report.solution_type}</div>
                  </div>
                )}
                {report.solution_note && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      解决方案说明
                    </div>
                    <div className="font-medium">{report.solution_note}</div>
                  </div>
                )}
                {report.resolved_at && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      解决时间
                    </div>
                    <div className="font-medium">
                      {formatDate(report.resolved_at)}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 备注 */}
          {report.remark && (
            <Card>
              <CardHeader>
                <CardTitle>备注</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm whitespace-pre-wrap">
                  {report.remark}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 操作面板 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>操作</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {report.status === "REPORTED" && (
                <>
                  <Button
                    className="w-full"
                    onClick={handleConfirm}
                    disabled={actionLoading}
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    确认上报
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={() => setShowRejectDialog(true)}
                    disabled={actionLoading}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    驳回上报
                  </Button>
                </>
              )}
              {report.status === "CONFIRMED" && (
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => setShowHandleDialog(true)}
                  disabled={actionLoading}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  开始处理
                </Button>
              )}
              {report.status === "HANDLING" && (
                <Button
                  className="w-full"
                  onClick={handleResolve}
                  disabled={actionLoading}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  标记已解决
                </Button>
              )}
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate("/shortage")}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回列表
              </Button>
            </CardContent>
          </Card>

          {/* 快速操作 */}
          {(report.status === "CONFIRMED" || report.status === "HANDLING") && (
            <Card>
              <CardHeader>
                <CardTitle>快速操作</CardTitle>
                <CardDescription>创建关联的处理方案</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleCreateArrival}
                >
                  <Truck className="h-4 w-4 mr-2" />
                  创建到货跟踪
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleCreateSubstitution}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  创建物料替代
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleCreateTransfer}
                >
                  <ArrowRightLeft className="h-4 w-4 mr-2" />
                  创建物料调拨
                </Button>
              </CardContent>
            </Card>
          )}

          {/* 状态时间线 */}
          <Card>
            <CardHeader>
              <CardTitle>状态时间线</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div
                    className={cn(
                      "rounded-full p-2",
                      status.color,
                      "bg-opacity-10",
                    )}
                  >
                    <Clock className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">已上报</div>
                    <div className="text-sm text-muted-foreground">
                      {formatDate(report.report_time)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      上报人：{report.reporter_name}
                    </div>
                  </div>
                </div>
                {report.confirmed_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-amber-500/10 text-amber-400">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">已确认</div>
                      <div className="text-sm text-muted-foreground">
                        {formatDate(report.confirmed_at)}
                      </div>
                    </div>
                  </div>
                )}
                {report.handler_id && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-purple-500/10 text-purple-400">
                      <RefreshCw className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">处理中</div>
                      <div className="text-sm text-muted-foreground">
                        处理人：{report.handler_name}
                      </div>
                    </div>
                  </div>
                )}
                {report.resolved_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-emerald-500/10 text-emerald-400">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">已解决</div>
                      <div className="text-sm text-muted-foreground">
                        {formatDate(report.resolved_at)}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.div>

      {/* 处理对话框 */}
      <Dialog open={showHandleDialog} onOpenChange={setShowHandleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>开始处理缺料上报</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <Label htmlFor="solution_type">解决方案类型</Label>
              <Select
                value={handleData.solution_type}
                onValueChange={(value) =>
                  setHandleData((prev) => ({ ...prev, solution_type: value }))
                }
              >
                <SelectTrigger id="solution_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ARRIVAL">到货跟踪</SelectItem>
                  <SelectItem value="SUBSTITUTION">物料替代</SelectItem>
                  <SelectItem value="TRANSFER">物料调拨</SelectItem>
                  <SelectItem value="OTHER">其他</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="solution_note">处理说明</Label>
              <Textarea
                id="solution_note"
                placeholder="请详细说明处理方案..."
                value={handleData.solution_note}
                onChange={(e) =>
                  setHandleData((prev) => ({
                    ...prev,
                    solution_note: e.target.value,
                  }))
                }
                rows={4}
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowHandleDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleHandle} disabled={actionLoading}>
              {actionLoading ? "处理中..." : "确认处理"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 驳回对话框 */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>驳回缺料上报</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <Label htmlFor="reject_reason">驳回原因</Label>
              <Textarea
                id="reject_reason"
                placeholder="请详细说明驳回原因..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={4}
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowRejectDialog(false);
                setRejectReason("");
              }}
            >
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={actionLoading}
            >
              {actionLoading ? "提交中..." : "确认驳回"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
