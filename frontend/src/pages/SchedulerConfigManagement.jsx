/**
 * Scheduler Config Management
 * 定时服务配置管理页面
 * 允许管理员配置所有定时服务的执行频率和启用状态
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Settings,
  RefreshCw,
  Save,
  Play,
  Pause,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  Download,
  Upload,
  Info } from
"lucide-react";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
  LoadingCard,
  ErrorMessage,
  EmptyState,
  ApiIntegrationError } from
"../components/ui";
import { cn, formatDate as _formatDate } from "../lib/utils";
import { fadeIn as _fadeIn, staggerContainer as _staggerContainer } from "../lib/animations";
import { schedulerApi } from "../services/api";
import { toast } from "../components/ui/toast";

// Cron配置选项
const CRON_PRESETS = {
  hourly: { label: "每小时", value: { minute: 0 } },
  daily_6am: { label: "每天 6:00", value: { hour: 6, minute: 0 } },
  daily_7am: { label: "每天 7:00", value: { hour: 7, minute: 0 } },
  daily_8am: { label: "每天 8:00", value: { hour: 8, minute: 0 } },
  daily_9am: { label: "每天 9:00", value: { hour: 9, minute: 0 } },
  daily_10am: { label: "每天 10:00", value: { hour: 10, minute: 0 } },
  daily_11am: { label: "每天 11:00", value: { hour: 11, minute: 0 } },
  daily_2pm: { label: "每天 14:00", value: { hour: 14, minute: 0 } },
  daily_3pm: { label: "每天 15:00", value: { hour: 15, minute: 0 } },
  daily_4pm: { label: "每天 16:00", value: { hour: 16, minute: 0 } },
  hourly_5min: { label: "每小时+5分", value: { minute: 5 } },
  hourly_10min: { label: "每小时+10分", value: { minute: 10 } },
  hourly_15min: { label: "每小时+15分", value: { minute: 15 } },
  hourly_30min: { label: "每小时+30分", value: { minute: 30 } },
  custom: { label: "自定义", value: null }
};

const RISK_LEVEL_COLORS = {
  CRITICAL: "bg-red-500/20 text-red-400 border-red-500/30",
  HIGH: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  MEDIUM: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  LOW: "bg-blue-500/20 text-blue-400 border-blue-500/30"
};

export default function SchedulerConfigManagement() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [configs, setConfigs] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterEnabled, setFilterEnabled] = useState("all");
  const [editingConfig, setEditingConfig] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // 获取配置列表
  const fetchConfigs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {};
      if (filterCategory !== "all") {
        params.category = filterCategory;
      }
      if (filterEnabled !== "all") {
        params.enabled = filterEnabled === "enabled";
      }

      const res = await schedulerApi.getConfigs(params);

      if (res.data?.code === 200) {
        setConfigs(res.data.data?.items || []);
      }
    } catch (err) {
      console.error("Failed to fetch configs:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, [filterCategory, filterEnabled]);

  // 同步配置（从scheduler_config.py同步到数据库）
  const handleSync = async (force = false) => {
    try {
      setSyncing(true);
      const res = await schedulerApi.syncConfigs(force);

      if (res.data?.code === 200) {
        toast.success(res.data.data?.message || "配置同步成功");
        await fetchConfigs();
      }
    } catch (err) {
      console.error("Failed to sync configs:", err);
      toast.error(
        "配置同步失败: " + (err.response?.data?.detail || err.message)
      );
    } finally {
      setSyncing(false);
    }
  };

  // 打开编辑对话框
  const handleEdit = (config) => {
    setEditingConfig({
      ...config,
      cron_config: config.cron_config || {}
    });
    setEditDialogOpen(true);
  };

  // 保存配置
  const handleSave = async () => {
    if (!editingConfig) {return;}

    try {
      const updateData = {
        is_enabled: editingConfig.is_enabled,
        cron_config: editingConfig.cron_config
      };

      const res = await schedulerApi.updateConfig(
        editingConfig.task_id,
        updateData
      );

      if (res.data?.code === 200) {
        toast.success("配置已更新");
        setEditDialogOpen(false);
        setEditingConfig(null);
        await fetchConfigs();
      }
    } catch (err) {
      console.error("Failed to update config:", err);
      toast.error(
        "更新配置失败: " + (err.response?.data?.detail || err.message)
      );
    }
  };

  // 切换启用状态
  const handleToggleEnabled = async (config) => {
    try {
      const updateData = {
        is_enabled: !config.is_enabled
      };

      const res = await schedulerApi.updateConfig(config.task_id, updateData);

      if (res.data?.code === 200) {
        toast.success(`任务已${updateData.is_enabled ? "启用" : "禁用"}`);
        await fetchConfigs();
      }
    } catch (err) {
      console.error("Failed to toggle enabled:", err);
      toast.error("操作失败: " + (err.response?.data?.detail || err.message));
    }
  };

  // 格式化Cron配置显示
  const formatCronConfig = (cronConfig) => {
    if (!cronConfig || typeof cronConfig !== "object") {return "未配置";}

    const parts = [];
    if (cronConfig.hour !== undefined) {parts.push(`${cronConfig.hour}:00`);}
    if (cronConfig.minute !== undefined) {
      if (cronConfig.hour === undefined) {
        parts.push(`每小时${cronConfig.minute}分`);
      } else {
        const hour = cronConfig.hour || 0;
        const minute = String(cronConfig.minute).padStart(2, "0");
        parts.push(`${hour}:${minute}`);
      }
    }
    if (cronConfig.day !== undefined) {parts.push(`每月${cronConfig.day}号`);}
    if (cronConfig.month !== undefined) {parts.push(`${cronConfig.month}月`);}

    if (parts.length === 0) {
      // 检查是否是每小时执行
      if (
      Object.keys(cronConfig).length === 1 &&
      cronConfig.minute !== undefined)
      {
        return `每小时${cronConfig.minute}分`;
      }
      return "自定义配置";
    }

    return parts.join(" ");
  };

  // 筛选后的配置
  const filteredConfigs = useMemo(() => {
    let filtered = configs;

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = (filtered || []).filter(
        (config) =>
        config.task_name?.toLowerCase().includes(term) ||
        config.task_id?.toLowerCase().includes(term) ||
        config.category?.toLowerCase().includes(term) ||
        config.owner?.toLowerCase().includes(term)
      );
    }

    return filtered;
  }, [configs, searchTerm]);

  // 获取分类列表
  const categories = useMemo(() => {
    const cats = new Set((configs || []).map((c) => c.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [configs]);

  if (error && configs.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="定时服务配置管理"
          description="配置所有后台定时服务的执行频率和启用状态" />

        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/scheduler/configs"
          onRetry={fetchConfigs} />

      </div>);

  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="定时服务配置管理"
        description="配置所有后台定时服务的执行频率和启用状态">

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSync(false)}
            disabled={syncing}>

            <RefreshCw
              className={cn("h-4 w-4 mr-2", syncing && "animate-spin")} />

            同步配置
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchConfigs}
            disabled={loading}>

            <RefreshCw
              className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />

            刷新
          </Button>
        </div>
      </PageHeader>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">总任务数</p>
                <p className="text-2xl font-bold">{configs.length}</p>
              </div>
              <Settings className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已启用</p>
                <p className="text-2xl font-bold text-green-400">
                  {(configs || []).filter((c) => c.is_enabled).length}
                </p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">已禁用</p>
                <p className="text-2xl font-bold text-red-400">
                  {(configs || []).filter((c) => !c.is_enabled).length}
                </p>
              </div>
              <XCircle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">分类数</p>
                <p className="text-2xl font-bold">{categories?.length}</p>
              </div>
              <Filter className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选和搜索 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索任务名称、ID、分类..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8" />

            </div>
            <Select value={filterCategory} onValueChange={setFilterCategory}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="所有分类" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有分类</SelectItem>
                {(categories || []).map((cat) =>
                <SelectItem key={cat} value={cat}>
                    {cat}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterEnabled} onValueChange={setFilterEnabled}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="全部状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="enabled">已启用</SelectItem>
                <SelectItem value="disabled">已禁用</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 配置列表 */}
      <Card>
        <CardHeader>
          <CardTitle>定时服务配置列表</CardTitle>
          <CardDescription>
            共 {filteredConfigs.length} 个任务配置
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <LoadingCard /> :
          filteredConfigs.length === 0 ?
          <EmptyState
            icon={Settings}
            title="暂无配置"
            description='点击"同步配置"按钮从代码同步任务配置' /> :


          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务名称</TableHead>
                  <TableHead>分类</TableHead>
                  <TableHead>执行频率</TableHead>
                  <TableHead>风险级别</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(filteredConfigs || []).map((config) =>
              <TableRow key={config.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{config.task_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {config.task_id}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {config.category || "未分类"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">
                          {formatCronConfig(config.cron_config)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {config.risk_level &&
                  <Badge
                    className={cn(
                      "border",
                      RISK_LEVEL_COLORS[config.risk_level] ||
                      RISK_LEVEL_COLORS.LOW
                    )}>

                          {config.risk_level}
                  </Badge>
                  }
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Switch
                      checked={config.is_enabled}
                      onCheckedChange={() => handleToggleEnabled(config)} />

                        <span className="text-sm">
                          {config.is_enabled ? "已启用" : "已禁用"}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(config)}>

                          配置
                        </Button>
                      </div>
                    </TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>

      {/* 编辑对话框 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>配置定时服务</DialogTitle>
            <DialogDescription>{editingConfig?.task_name}</DialogDescription>
          </DialogHeader>

          {editingConfig &&
          <div className="space-y-4">
              {/* 基本信息 */}
              <div className="space-y-2">
                <Label>任务ID</Label>
                <Input value={editingConfig.task_id} disabled />
              </div>

              <div className="space-y-2">
                <Label>描述</Label>
                <p className="text-sm text-muted-foreground">
                  {editingConfig.description || "无描述"}
                </p>
              </div>

              {/* 启用状态 */}
              <div className="flex items-center justify-between">
                <div>
                  <Label>启用状态</Label>
                  <p className="text-sm text-muted-foreground">
                    控制任务是否执行
                  </p>
                </div>
                <Switch
                checked={editingConfig.is_enabled}
                onCheckedChange={(checked) =>
                setEditingConfig({ ...editingConfig, is_enabled: checked })
                } />

              </div>

              {/* Cron配置 */}
              <div className="space-y-2">
                <Label>执行频率</Label>
                <Select
                value={
                Object.keys(CRON_PRESETS).find(
                  (key) =>
                  JSON.stringify(CRON_PRESETS[key].value) ===
                  JSON.stringify(editingConfig.cron_config)
                ) || "custom"
                }
                onValueChange={(value) => {
                  if (value !== "custom" && CRON_PRESETS[value].value) {
                    setEditingConfig({
                      ...editingConfig,
                      cron_config: CRON_PRESETS[value].value
                    });
                  }
                }}>

                  <SelectTrigger>
                    <SelectValue placeholder="选择执行频率" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(CRON_PRESETS).map(([key, preset]) =>
                  <SelectItem key={key} value={key}>
                        {preset.label}
                  </SelectItem>
                  )}
                  </SelectContent>
                </Select>
              </div>

              {/* 自定义Cron配置 */}
              {editingConfig.cron_config &&
            <div className="space-y-2 p-4 bg-muted rounded-lg">
                  <Label className="text-sm">当前配置</Label>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs">小时 (0-23)</Label>
                      <Input
                    type="number"
                    min="0"
                    max="23"
                    value={editingConfig.cron_config.hour ?? ""}
                    onChange={(e) =>
                    setEditingConfig({
                      ...editingConfig,
                      cron_config: {
                        ...editingConfig.cron_config,
                        hour: e.target.value ?
                        parseInt(e.target.value) :
                        undefined
                      }
                    })
                    }
                    placeholder="留空表示每小时" />

                    </div>
                    <div>
                      <Label className="text-xs">分钟 (0-59)</Label>
                      <Input
                    type="number"
                    min="0"
                    max="59"
                    value={editingConfig.cron_config.minute ?? ""}
                    onChange={(e) =>
                    setEditingConfig({
                      ...editingConfig,
                      cron_config: {
                        ...editingConfig.cron_config,
                        minute: e.target.value ?
                        parseInt(e.target.value) :
                        undefined
                      }
                    })
                    }
                    placeholder="留空表示每分钟" />

                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    <Info className="h-3 w-3 inline mr-1" />
                    示例：hour=7, minute=0 表示每天7:00执行；minute=0
                    表示每小时整点执行
                  </p>
            </div>
            }

              {/* 风险级别和SLA */}
              {editingConfig.risk_level &&
            <div className="space-y-2">
                  <Label>风险级别</Label>
                  <Badge
                className={cn(
                  "border",
                  RISK_LEVEL_COLORS[editingConfig.risk_level] ||
                  RISK_LEVEL_COLORS.LOW
                )}>

                    {editingConfig.risk_level}
                  </Badge>
            </div>
            }
          </div>
          }

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSave}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}