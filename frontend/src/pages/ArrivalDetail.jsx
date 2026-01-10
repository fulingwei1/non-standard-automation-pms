/**
 * Arrival Detail - 到货跟踪详情页
 * 显示到货跟踪的详细信息，支持状态更新、跟催、收货等操作
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Truck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Calendar,
  Package,
  RefreshCw,
  XCircle,
  Phone,
  Mail,
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
  Input,
  Label,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
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
  PENDING: { label: "待处理", color: "bg-slate-500", icon: Clock },
  IN_TRANSIT: { label: "在途", color: "bg-blue-500", icon: Truck },
  DELAYED: { label: "延迟", color: "bg-red-500", icon: AlertTriangle },
  RECEIVED: { label: "已收货", color: "bg-emerald-500", icon: CheckCircle2 },
  CANCELLED: { label: "已取消", color: "bg-slate-400", icon: XCircle },
};

export default function ArrivalDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [arrival, setArrival] = useState(null);
  const [followUps, setFollowUps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showReceiveDialog, setShowReceiveDialog] = useState(false);
  const [showFollowUpDialog, setShowFollowUpDialog] = useState(false);
  const [receiveQty, setReceiveQty] = useState("");
  const [followUpData, setFollowUpData] = useState({
    follow_up_type: "CALL",
    follow_up_note: "",
    supplier_response: "",
    next_follow_up_date: "",
  });

  useEffect(() => {
    loadArrival();
    loadFollowUps();
  }, [id]);

  const loadArrival = async () => {
    setLoading(true);
    try {
      const res = await shortageApi.arrivals.get(id);
      setArrival(res.data);
      if (res.data.expected_qty) {
        setReceiveQty(String(res.data.expected_qty));
      }
    } catch (error) {
      console.error("加载到货跟踪详情失败", error);
    } finally {
      setLoading(false);
    }
  };

  const loadFollowUps = async () => {
    try {
      const res = await shortageApi.arrivals.getFollowUps(id, {
        page: 1,
        page_size: 50,
      });
      setFollowUps(res.data.items || []);
    } catch (error) {
      console.error("加载跟催记录失败", error);
    }
  };

  const handleReceive = async () => {
    if (!receiveQty || parseFloat(receiveQty) <= 0) {
      alert("请输入有效的实收数量");
      return;
    }
    setActionLoading(true);
    try {
      await shortageApi.arrivals.receive(id, parseFloat(receiveQty));
      setShowReceiveDialog(false);
      await loadArrival();
    } catch (error) {
      console.error("确认收货失败", error);
      alert("确认收货失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateFollowUp = async () => {
    if (!followUpData.follow_up_note.trim()) {
      alert("请输入跟催内容");
      return;
    }
    setActionLoading(true);
    try {
      await shortageApi.arrivals.createFollowUp(id, {
        ...followUpData,
        next_follow_up_date: followUpData.next_follow_up_date || null,
      });
      setShowFollowUpDialog(false);
      setFollowUpData({
        follow_up_type: "CALL",
        follow_up_note: "",
        supplier_response: "",
        next_follow_up_date: "",
      });
      await loadFollowUps();
      await loadArrival();
    } catch (error) {
      console.error("创建跟催记录失败", error);
      alert(
        "创建跟催记录失败：" + (error.response?.data?.detail || error.message),
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateStatus = async (status) => {
    if (!confirm(`确认要将状态更新为"${statusConfigs[status]?.label}"吗？`))
      return;
    setActionLoading(true);
    try {
      await shortageApi.arrivals.updateStatus(id, status);
      await loadArrival();
    } catch (error) {
      console.error("更新状态失败", error);
      alert("更新状态失败：" + (error.response?.data?.detail || error.message));
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

  if (!arrival) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <XCircle className="h-12 w-12 text-muted-foreground" />
        <div className="text-muted-foreground">到货跟踪不存在</div>
        <Button variant="outline" onClick={() => navigate("/shortage")}>
          返回列表
        </Button>
      </div>
    );
  }

  const status = statusConfigs[arrival.status] || statusConfigs.PENDING;
  const StatusIcon = status.icon;

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/shortage")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader
          title={`到货跟踪 - ${arrival.arrival_no}`}
          description="查看到货跟踪的详细信息和跟催记录"
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
                <Badge
                  variant="outline"
                  className={cn(status.color, "text-white")}
                >
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {status.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">到货单号</div>
                  <div className="font-medium">{arrival.arrival_no}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">物料编码</div>
                  <div className="font-medium">{arrival.material_code}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">物料名称</div>
                  <div className="font-medium">{arrival.material_name}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">预期数量</div>
                  <div className="font-medium">{arrival.expected_qty}</div>
                </div>
                {arrival.supplier_name && (
                  <>
                    <div>
                      <div className="text-sm text-muted-foreground">
                        供应商
                      </div>
                      <div className="font-medium">{arrival.supplier_name}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">
                        供应商ID
                      </div>
                      <div className="font-medium">
                        {arrival.supplier_id || "-"}
                      </div>
                    </div>
                  </>
                )}
                <div>
                  <div className="text-sm text-muted-foreground">
                    预期到货日期
                  </div>
                  <div className="font-medium">
                    {formatDate(arrival.expected_date)}
                  </div>
                </div>
                {arrival.actual_date && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      实际到货日期
                    </div>
                    <div className="font-medium">
                      {formatDate(arrival.actual_date)}
                    </div>
                  </div>
                )}
                {arrival.is_delayed && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      延迟天数
                    </div>
                    <div className="font-medium text-red-400">
                      {arrival.delay_days} 天
                    </div>
                  </div>
                )}
                {arrival.received_qty > 0 && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      实收数量
                    </div>
                    <div className="font-medium">{arrival.received_qty}</div>
                  </div>
                )}
                {arrival.received_at && (
                  <div>
                    <div className="text-sm text-muted-foreground">
                      收货时间
                    </div>
                    <div className="font-medium">
                      {formatDate(arrival.received_at)}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 跟催记录 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>跟催记录</CardTitle>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowFollowUpDialog(true)}
                >
                  <Phone className="h-4 w-4 mr-2" />
                  添加跟催
                </Button>
              </div>
              <CardDescription>
                共 {arrival.follow_up_count || 0} 次跟催
              </CardDescription>
            </CardHeader>
            <CardContent>
              {followUps.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  暂无跟催记录
                </div>
              ) : (
                <div className="space-y-4">
                  {followUps.map((followUp) => (
                    <div
                      key={followUp.id}
                      className="p-4 rounded-lg border border-border bg-surface-1"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {followUp.follow_up_type}
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            {followUp.followed_by_name}
                          </span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(followUp.followed_at)}
                        </span>
                      </div>
                      <div className="text-sm mb-2">
                        {followUp.follow_up_note}
                      </div>
                      {followUp.supplier_response && (
                        <div className="text-sm text-muted-foreground bg-surface-2 p-2 rounded mt-2">
                          <div className="font-medium mb-1">供应商反馈：</div>
                          {followUp.supplier_response}
                        </div>
                      )}
                      {followUp.next_follow_up_date && (
                        <div className="text-xs text-muted-foreground mt-2">
                          下次跟催：{formatDate(followUp.next_follow_up_date)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 备注 */}
          {arrival.remark && (
            <Card>
              <CardHeader>
                <CardTitle>备注</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm whitespace-pre-wrap">
                  {arrival.remark}
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
              {arrival.status === "PENDING" && (
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => handleUpdateStatus("IN_TRANSIT")}
                  disabled={actionLoading}
                >
                  <Truck className="h-4 w-4 mr-2" />
                  标记在途
                </Button>
              )}
              {arrival.status === "IN_TRANSIT" && (
                <>
                  <Button
                    className="w-full"
                    onClick={() => setShowReceiveDialog(true)}
                    disabled={actionLoading}
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    确认收货
                  </Button>
                  <Button
                    className="w-full"
                    variant="outline"
                    onClick={() => setShowFollowUpDialog(true)}
                    disabled={actionLoading}
                  >
                    <Phone className="h-4 w-4 mr-2" />
                    添加跟催
                  </Button>
                </>
              )}
              {arrival.status !== "RECEIVED" &&
                arrival.status !== "CANCELLED" && (
                  <Button
                    className="w-full"
                    variant="outline"
                    onClick={() => setShowFollowUpDialog(true)}
                    disabled={actionLoading}
                  >
                    <Phone className="h-4 w-4 mr-2" />
                    添加跟催
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
                    <StatusIcon className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{status.label}</div>
                    <div className="text-sm text-muted-foreground">
                      {formatDate(arrival.created_at)}
                    </div>
                  </div>
                </div>
                {arrival.received_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-emerald-500/10 text-emerald-400">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">已收货</div>
                      <div className="text-sm text-muted-foreground">
                        {formatDate(arrival.received_at)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        实收：{arrival.received_qty}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.div>

      {/* 确认收货对话框 */}
      <Dialog open={showReceiveDialog} onOpenChange={setShowReceiveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认收货</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <Label htmlFor="receive_qty">实收数量</Label>
                <Input
                  id="receive_qty"
                  type="number"
                  step="0.01"
                  min="0"
                  value={receiveQty}
                  onChange={(e) => setReceiveQty(e.target.value)}
                  placeholder="请输入实收数量"
                />
                <div className="text-xs text-muted-foreground mt-1">
                  预期数量：{arrival.expected_qty}
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowReceiveDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleReceive} disabled={actionLoading}>
              {actionLoading ? "确认中..." : "确认收货"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 添加跟催对话框 */}
      <Dialog open={showFollowUpDialog} onOpenChange={setShowFollowUpDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>添加跟催记录</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <Label htmlFor="follow_up_type">跟催方式</Label>
                <Select
                  value={followUpData.follow_up_type}
                  onValueChange={(value) =>
                    setFollowUpData((prev) => ({
                      ...prev,
                      follow_up_type: value,
                    }))
                  }
                >
                  <SelectTrigger id="follow_up_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CALL">电话</SelectItem>
                    <SelectItem value="EMAIL">邮件</SelectItem>
                    <SelectItem value="VISIT">拜访</SelectItem>
                    <SelectItem value="OTHER">其他</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="follow_up_note">跟催内容</Label>
                <Textarea
                  id="follow_up_note"
                  placeholder="请输入跟催内容..."
                  value={followUpData.follow_up_note}
                  onChange={(e) =>
                    setFollowUpData((prev) => ({
                      ...prev,
                      follow_up_note: e.target.value,
                    }))
                  }
                  rows={4}
                />
              </div>
              <div>
                <Label htmlFor="supplier_response">供应商反馈</Label>
                <Textarea
                  id="supplier_response"
                  placeholder="供应商的反馈信息..."
                  value={followUpData.supplier_response}
                  onChange={(e) =>
                    setFollowUpData((prev) => ({
                      ...prev,
                      supplier_response: e.target.value,
                    }))
                  }
                  rows={3}
                />
              </div>
              <div>
                <Label htmlFor="next_follow_up_date">下次跟催日期</Label>
                <Input
                  id="next_follow_up_date"
                  type="date"
                  value={followUpData.next_follow_up_date}
                  onChange={(e) =>
                    setFollowUpData((prev) => ({
                      ...prev,
                      next_follow_up_date: e.target.value,
                    }))
                  }
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowFollowUpDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreateFollowUp} disabled={actionLoading}>
              {actionLoading ? "提交中..." : "提交"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
