import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Bell,
  Plus,
  Edit,
  Trash2,
  Power,
  PowerOff,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Settings,
  Clock,
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
import { LoadingCard, ErrorMessage, EmptyState } from "../components/common";
import { toast } from "../components/ui/toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
  DialogDescription,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Label } from "../components/ui/label";
import { Checkbox } from "../components/ui/checkbox";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { alertApi, projectApi } from "../services/api";

// 预警类型选项
import { confirmAction } from "@/lib/confirmAction";
const alertTypeOptions = [
  { value: "", label: "全部类型" },
  { value: "SCHEDULE_DELAY", label: "进度延期" },
  { value: "COST_OVERRUN", label: "成本超支" },
  { value: "MILESTONE_DUE", label: "里程碑到期" },
  { value: "DELIVERY_DUE", label: "交期预警" },
  { value: "MATERIAL_SHORTAGE", label: "物料短缺" },
  { value: "QUALITY_ISSUE", label: "质量问题" },
  { value: "PAYMENT_DUE", label: "付款到期" },
  { value: "SPECIFICATION_MISMATCH", label: "规格不匹配" },
];

// 预警级别选项
const alertLevelOptions = [
  { value: "INFO", label: "提示", color: "blue" },
  { value: "WARNING", label: "注意", color: "amber" },
  { value: "CRITICAL", label: "严重", color: "orange" },
  { value: "URGENT", label: "紧急", color: "red" },
];

// 通知渠道选项
const channelOptions = [
  { value: "SYSTEM", label: "站内消息" },
  { value: "EMAIL", label: "邮件" },
  { value: "WECHAT", label: "企业微信" },
  { value: "SMS", label: "短信" },
];

export default function AlertSubscriptionSettings() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editingSubscription, setEditingSubscription] = useState(null);

  // 表单状态
  const [formData, setFormData] = useState({
    alert_type: "",
    project_id: null,
    min_level: "WARNING",
    notify_channels: ["SYSTEM"],
    quiet_start: "",
    quiet_end: "",
    is_active: true,
  });

  const loadSubscriptions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchQuery) {
        // 可以根据需要添加搜索功能
      }
      const response = await alertApi.subscriptions.list(params);
      const data = response.data?.data || response.data || response;
      if (data && typeof data === "object" && "items" in data) {
        setSubscriptions(data.items || []);
        setTotal(data.total || 0);
      } else if (Array.isArray(data)) {
        setSubscriptions(data);
        setTotal(data?.length);
      } else {
        setSubscriptions([]);
        setTotal(0);
      }
    } catch (err) {
      console.error("Failed to load subscriptions:", err);
      setError(err.response?.data?.detail || err.message || "加载订阅列表失败");
      setSubscriptions([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchQuery]);

  const loadProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({ page: 1, page_size: 100 });
      const data = response.data?.data || response.data || response;
      if (data && typeof data === "object" && "items" in data) {
        setProjects(data.items || []);
      } else if (Array.isArray(data)) {
        setProjects(data);
      }
    } catch (err) {
      console.error("Failed to load projects:", err);
    }
  }, []);

  useEffect(() => {
    loadSubscriptions();
    loadProjects();
  }, [loadSubscriptions, loadProjects]);

  const handleCreate = () => {
    setEditingSubscription(null);
    setFormData({
      alert_type: "",
      project_id: null,
      min_level: "WARNING",
      notify_channels: ["SYSTEM"],
      quiet_start: "",
      quiet_end: "",
      is_active: true,
    });
    setShowDialog(true);
  };

  const handleEdit = (subscription) => {
    setEditingSubscription(subscription);
    setFormData({
      alert_type: subscription.alert_type || "",
      project_id: subscription.project_id || null,
      min_level: subscription.min_level || "WARNING",
      notify_channels: subscription.notify_channels || ["SYSTEM"],
      quiet_start: subscription.quiet_start || "",
      quiet_end: subscription.quiet_end || "",
      is_active: subscription.is_active !== false,
    });
    setShowDialog(true);
  };

  const handleDelete = async (subscription) => {
    if (!await confirmAction(`确定要删除订阅配置吗？`)) {
      return;
    }
    try {
      await alertApi.subscriptions.delete(subscription.id);
      toast.success("订阅配置已删除");
      loadSubscriptions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "删除失败");
    }
  };

  const handleToggle = async (subscription) => {
    try {
      await alertApi.subscriptions.toggle(subscription.id);
      toast.success(subscription.is_active ? "订阅已禁用" : "订阅已启用");
      loadSubscriptions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "操作失败");
    }
  };

  const handleSave = async () => {
    try {
      // 表单验证
      if (formData.quiet_start && formData.quiet_end) {
        // 验证时间格式
        const timePattern = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
        if (!timePattern.test(formData.quiet_start)) {
          toast.error("免打扰开始时间格式错误，应为 HH:mm 格式");
          return;
        }
        if (!timePattern.test(formData.quiet_end)) {
          toast.error("免打扰结束时间格式错误，应为 HH:mm 格式");
          return;
        }
      }

      if (editingSubscription) {
        // 更新
        await alertApi.subscriptions.update(editingSubscription.id, formData);
        toast.success("订阅配置已更新");
      } else {
        // 创建
        await alertApi.subscriptions.create(formData);
        toast.success("订阅配置已创建");
      }
      setShowDialog(false);
      loadSubscriptions();
    } catch (err) {
      toast.error(err.response?.data?.detail || "保存失败");
    }
  };

  const handleChannelToggle = (channel) => {
    setFormData((prev) => {
      const channels = prev.notify_channels || [];
      if (channels.includes(channel)) {
        return {
          ...prev,
          notify_channels: (channels || []).filter((c) => c !== channel),
        };
      } else {
        return { ...prev, notify_channels: [...channels, channel] };
      }
    });
  };

  const formatLevel = (level) => {
    const option = (alertLevelOptions || []).find((o) => o.value === level);
    return option?.label || level;
  };

  const getLevelColor = (level) => {
    const option = (alertLevelOptions || []).find((o) => o.value === level);
    return option?.color || "slate";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="预警订阅配置"
        description="管理您的预警接收设置，自定义接收的预警类型和通知方式"
        actions={
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="w-4 h-4" />
            新建订阅
          </Button>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 筛选栏 */}
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex-1 min-w-[200px]">
                <Input
                  placeholder="搜索订阅配置..."
                  value={searchQuery || "unknown"}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-surface-2"
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={loadSubscriptions}
                className="gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                刷新
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 订阅列表 */}
        {loading ? (
          <LoadingCard />
        ) : error ? (
          <ErrorMessage message={error} />
        ) : subscriptions.length === 0 ? (
          <EmptyState
            icon={Bell}
            title="暂无订阅配置"
            description="点击「新建订阅」按钮创建第一个订阅配置"
          />
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-4"
          >
            {(subscriptions || []).map((subscription) => (
              <motion.div key={subscription.id} variants={fadeIn}>
                <Card className="bg-surface-1/50 hover:bg-surface-1 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-white">
                            {subscription.alert_type
                              ? (alertTypeOptions || []).find(
                                  (o) => o.value === subscription.alert_type,
                                )?.label || subscription.alert_type
                              : "全部类型"}
                          </h3>
                          <Badge
                            variant={
                              subscription.is_active ? "default" : "secondary"
                            }
                            className={cn(
                              subscription.is_active
                                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                                : "bg-slate-500/20 text-slate-400 border-slate-500/30",
                            )}
                          >
                            {subscription.is_active ? (
                              <>
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                已启用
                              </>
                            ) : (
                              <>
                                <XCircle className="w-3 h-3 mr-1" />
                                已禁用
                              </>
                            )}
                          </Badge>
                          <Badge
                            className={`bg-${getLevelColor(subscription.min_level)}-500/20 text-${getLevelColor(subscription.min_level)}-400 border-${getLevelColor(subscription.min_level)}-500/30`}
                          >
                            最低级别: {formatLevel(subscription.min_level)}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-400 mb-3">
                          <div>
                            <span className="text-slate-500">项目范围:</span>{" "}
                            <span className="text-white">
                              {subscription.project_name ||
                                subscription.project_id ||
                                "全部项目"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">通知渠道:</span>{" "}
                            <span className="text-white">
                              {(subscription.notify_channels || ["SYSTEM"])
                                .map(
                                  (ch) =>
                                    (channelOptions || []).find((o) => o.value === ch)
                                      ?.label || ch,
                                )
                                .join(", ")}
                            </span>
                          </div>
                          {subscription.quiet_start &&
                            subscription.quiet_end && (
                              <div>
                                <span className="text-slate-500">
                                  免打扰时段:
                                </span>{" "}
                                <span className="text-white">
                                  {subscription.quiet_start} -{" "}
                                  {subscription.quiet_end}
                                </span>
                              </div>
                            )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleToggle(subscription)}
                          className="gap-2"
                          title={
                            subscription.is_active ? "禁用订阅" : "启用订阅"
                          }
                        >
                          {subscription.is_active ? (
                            <PowerOff className="w-4 h-4" />
                          ) : (
                            <Power className="w-4 h-4" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(subscription)}
                          className="gap-2"
                        >
                          <Edit className="w-4 h-4" />
                          编辑
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(subscription)}
                          className="gap-2 text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                          删除
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* 分页 */}
        {total > pageSize && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              上一页
            </Button>
            <span className="text-sm text-slate-400">
              第 {page} 页，共 {Math.ceil(total / pageSize)} 页
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))
              }
              disabled={page >= Math.ceil(total / pageSize)}
            >
              下一页
            </Button>
          </div>
        )}
      </div>

      {/* 创建/编辑对话框 */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingSubscription ? "编辑预警订阅" : "新建预警订阅"}
            </DialogTitle>
            <DialogDescription>
              {editingSubscription
                ? "修改预警订阅的配置信息"
                : "创建新的预警订阅，自定义接收的预警类型和通知方式"}
            </DialogDescription>
          </DialogHeader>
          <DialogBody className="space-y-6">
            {/* 订阅范围 */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">订阅范围</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="alert_type">预警类型</Label>
                  <Select
                    value={formData.alert_type || ""}
                    onValueChange={(val) =>
                      setFormData((prev) => ({
                        ...prev,
                        alert_type: val || "",
                      }))
                    }
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue placeholder="选择预警类型（空表示全部）" />
                    </SelectTrigger>
                    <SelectContent>
                      {(alertTypeOptions || []).map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    选择"全部类型"将接收所有类型的预警
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project_id">项目范围</Label>
                  <Select
                    value={formData.project_id?.toString() || ""}
                    onValueChange={(val) =>
                      setFormData((prev) => ({
                        ...prev,
                        project_id: val ? parseInt(val) : null,
                      }))
                    }
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue placeholder="选择项目（空表示全部）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部项目</SelectItem>
                      {(projects || []).map((project) => (
                        <SelectItem
                          key={project.id}
                          value={project.id.toString()}
                        >
                          {project.project_name || project.project_code}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    选择"全部项目"将接收所有项目的预警
                  </p>
                </div>
              </div>
            </div>

            {/* 接收级别和通知渠道 */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">
                接收级别和通知渠道
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="min_level">最低接收级别</Label>
                  <Select
                    value={formData.min_level}
                    onValueChange={(val) =>
                      setFormData((prev) => ({ ...prev, min_level: val }))
                    }
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {(alertLevelOptions || []).map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    只接收此级别及以上的预警
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>通知渠道</Label>
                  <div className="flex flex-wrap gap-3 mt-2">
                    {(channelOptions || []).map((channel) => (
                      <div
                        key={channel.value}
                        className="flex items-center space-x-2"
                      >
                        <Checkbox
                          id={`channel-${channel.value}`}
                          checked={formData.notify_channels?.includes(
                            channel.value,
                          )}
                          onCheckedChange={() =>
                            handleChannelToggle(channel.value)
                          }
                        />
                        <Label
                          htmlFor={`channel-${channel.value}`}
                          className="text-sm font-normal cursor-pointer"
                        >
                          {channel.label}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 免打扰时段 */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">
                免打扰时段（可选）
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="quiet_start">开始时间</Label>
                  <Input
                    id="quiet_start"
                    type="text"
                    value={formData.quiet_start}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        quiet_start: e.target.value,
                      }))
                    }
                    placeholder="例如: 22:00"
                    className="bg-surface-2"
                  />
                  <p className="text-xs text-slate-500">
                    格式: HH:mm (24小时制)
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="quiet_end">结束时间</Label>
                  <Input
                    id="quiet_end"
                    type="text"
                    value={formData.quiet_end}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        quiet_end: e.target.value,
                      }))
                    }
                    placeholder="例如: 08:00"
                    className="bg-surface-2"
                  />
                  <p className="text-xs text-slate-500">
                    格式: HH:mm (24小时制)
                  </p>
                </div>
              </div>
              <p className="text-xs text-slate-500">
                在免打扰时段内，即使匹配到订阅也不会发送通知（紧急预警除外）
              </p>
            </div>

            {/* 启用状态 */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData((prev) => ({ ...prev, is_active: checked }))
                }
              />
              <Label htmlFor="is_active" className="cursor-pointer">
                启用此订阅
              </Label>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSave}>
              {editingSubscription ? "保存" : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}