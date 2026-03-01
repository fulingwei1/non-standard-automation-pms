/**
 * KPI 管理列表页面
 * 展示 KPI 卡片、进度条、健康状态、历史趋势、数据采集
 */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Edit2,
  Trash2,
  Search,
  RefreshCw,
  TrendingUp,
  Activity,
  Calendar,
  ChevronDown,
  ChevronRight,
  Target,
  AlertCircle,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
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
  DialogFooter,
  DialogTitle,
  DialogBody,
  Progress,
  Skeleton,
} from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import { strategyApi, kpiApi } from "@/services/api/strategy";
import { BSC_DIMENSIONS } from "@/lib/constants/strategy";

// 健康状态配置
const HEALTH_STATUS = {
  ON_TRACK: {
    label: "正常",
    color: "#22c55e",
    bgColor: "bg-emerald-500/20",
    borderColor: "border-emerald-500/30",
    icon: CheckCircle2,
  },
  AT_RISK: {
    label: "预警",
    color: "#f59e0b",
    bgColor: "bg-amber-500/20",
    borderColor: "border-amber-500/30",
    icon: AlertCircle,
  },
  OFF_TRACK: {
    label: "落后",
    color: "#ef4444",
    bgColor: "bg-red-500/20",
    borderColor: "border-red-500/30",
    icon: XCircle,
  },
};

// 采集频率配置
const COLLECTION_FREQUENCY = {
  DAILY: { label: "每日", icon: Calendar },
  WEEKLY: { label: "每周", icon: Calendar },
  MONTHLY: { label: "每月", icon: Calendar },
  QUARTERLY: { label: "每季", icon: Calendar },
  YEARLY: { label: "每年", icon: Calendar },
};

// KPI 表单组件
function KPIForm({ kpi, onSubmit, onCancel, loading }) {
  const [formData, setFormData] = useState({
    name: kpi?.name || "",
    description: kpi?.description || "",
    target_value: kpi?.target_value || 100,
    current_value: kpi?.current_value || 0,
    unit: kpi?.unit || "%",
    collection_frequency: kpi?.collection_frequency || "MONTHLY",
    dimension: kpi?.dimension || "FINANCIAL",
    csf_id: kpi?.csf_id || "",
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            KPI 名称 *
          </label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="输入 KPI 名称"
            required
            className="bg-slate-800/50 border-slate-700"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            描述
          </label>
          <textarea
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            placeholder="描述该 KPI 指标"
            rows={2}
            className="w-full rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              目标值 *
            </label>
            <Input
              type="number"
              step="0.01"
              value={formData.target_value}
              onChange={(e) =>
                setFormData({ ...formData, target_value: e.target.value })
              }
              className="bg-slate-800/50 border-slate-700"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              当前值
            </label>
            <Input
              type="number"
              step="0.01"
              value={formData.current_value}
              onChange={(e) =>
                setFormData({ ...formData, current_value: e.target.value })
              }
              className="bg-slate-800/50 border-slate-700"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              单位
            </label>
            <Input
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              placeholder="%"
              className="bg-slate-800/50 border-slate-700"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              BSC 维度 *
            </label>
            <select
              value={formData.dimension}
              onChange={(e) =>
                setFormData({ ...formData, dimension: e.target.value })
              }
              className="w-full rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            >
              {Object.entries(BSC_DIMENSIONS).map(([key, config]) => (
                <option key={key} value={key || "unknown"}>
                  {config.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              采集频率 *
            </label>
            <select
              value={formData.collection_frequency}
              onChange={(e) =>
                setFormData({ ...formData, collection_frequency: e.target.value })
              }
              className="w-full rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              required
            >
              {Object.entries(COLLECTION_FREQUENCY).map(([key, config]) => (
                <option key={key} value={key || "unknown"}>
                  {config.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <DialogFooter className="mt-6">
        <Button type="button" variant="outline" onClick={onCancel}>
          取消
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? "保存中..." : kpi?.id ? "更新" : "创建"}
        </Button>
      </DialogFooter>
    </form>
  );
}

// 更新 KPI 值弹窗
function UpdateValueDialog({ kpi, open, onClose, onSubmit, loading }) {
  const [value, setValue] = useState(kpi?.current_value || 0);

  useEffect(() => {
    if (kpi) {
      setValue(kpi.current_value || 0);
    }
  }, [kpi]);

  const handleSubmit = () => {
    onSubmit({ current_value: parseFloat(value) });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>更新 KPI 值</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-slate-400 mb-1">KPI 名称</p>
              <p className="text-base font-medium text-white">{kpi?.name}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                当前值 ({kpi?.unit || "%"}) *
              </label>
              <Input
                type="number"
                step="0.01"
                value={value || "unknown"}
                onChange={(e) => setValue(e.target.value)}
                className="bg-slate-800/50 border-slate-700 text-lg"
              />
            </div>

            <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700">
              <p className="text-sm text-slate-400">目标值</p>
              <p className="text-lg font-semibold text-white">
                {kpi?.target_value} {kpi?.unit || "%"}
              </p>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? "更新中..." : "确认更新"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// KPI 卡片组件
function KPICard({ kpi, onUpdate, onCollect, color }) {
  const [expanded, setExpanded] = useState(false);
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const status = kpi.status || "ON_TRACK";
  const statusConfig = HEALTH_STATUS[status] || HEALTH_STATUS.ON_TRACK;
  const progress = kpi.target_value
    ? Math.min(100, ((kpi.current_value || 0) / kpi.target_value) * 100)
    : 0;

  const loadHistory = async () => {
    if (!kpi.id || loadingHistory) return;

    try {
      setLoadingHistory(true);
      const res = await kpiApi.getHistory(kpi.id, 6);
      setHistory(res.data || []);
    } catch (error) {
      console.error("加载历史数据失败:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleExpand = () => {
    if (!expanded) {
      loadHistory();
    }
    setExpanded(!expanded);
  };

  const FreqIcon =
    COLLECTION_FREQUENCY[kpi.collection_frequency]?.icon || Calendar;

  return (
    <motion.div
      variants={fadeIn}
      className="rounded-xl border border-white/10 bg-slate-800/50 overflow-hidden"
    >
      {/* 卡片头部 */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span
                className="text-xs font-mono px-2 py-0.5 rounded"
                style={{ backgroundColor: `${color}20`, color }}
              >
                {kpi.code || `KPI-${kpi.id}`}
              </span>
              <Badge
                variant="outline"
                className={`${statusConfig.bgColor} ${statusConfig.borderColor} ${statusConfig.color} border`}
              >
                <statusConfig.icon className="w-3 h-3 mr-1" />
                {statusConfig.label}
              </Badge>
            </div>
            <h4 className="text-sm font-semibold text-white mb-1">
              {kpi.name}
            </h4>
            {kpi.description && (
              <p className="text-xs text-slate-400 line-clamp-1">
                {kpi.description}
              </p>
            )}
          </div>
          <button
            onClick={handleExpand}
            className="text-slate-400 hover:text-white transition-colors"
          >
            {expanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* 进度条 */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400">进度</span>
            <span className="text-white font-medium">
              {kpi.current_value || 0} / {kpi.target_value} {kpi.unit || "%"}
            </span>
          </div>
          <Progress
            value={progress || "unknown"}
            className="h-2"
            indicatorClassName={
              status === "ON_TRACK"
                ? "bg-gradient-to-r from-emerald-500 to-green-500"
                : status === "AT_RISK"
                  ? "bg-gradient-to-r from-amber-500 to-orange-500"
                  : "bg-gradient-to-r from-red-500 to-rose-500"
            }
          />
        </div>

        {/* 底部操作栏 */}
        <div className="flex items-center justify-between pt-3 border-t border-white/5">
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <div className="flex items-center gap-1">
              <FreqIcon className="w-3.5 h-3.5" />
              <span>
                {COLLECTION_FREQUENCY[kpi.collection_frequency]?.label || "每月"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => onUpdate(kpi)}
            >
              更新值
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={() => onCollect(kpi)}
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              采集
            </Button>
          </div>
        </div>
      </div>

      {/* 展开的历史数据 */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-white/5 bg-slate-900/30"
          >
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-slate-500" />
                <span className="text-xs font-medium text-slate-400">
                  历史数据 (最近 6 期)
                </span>
              </div>

              {loadingHistory ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              ) : history.length > 0 ? (
                <div className="space-y-2">
                  {history.map((item, index) => (
                    <div
                      key={item.id || index}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50"
                    >
                      <div className="flex items-center gap-2">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        <span className="text-xs text-slate-400">
                          {item.collection_date || item.date || `第${index + 1}期`}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-white">
                          {item.value || item.current_value} {kpi.unit || "%"}
                        </span>
                        {item.value >= (kpi.target_value * 0.9) && (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 text-center py-4">
                  暂无历史数据
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function KPIList() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeStrategy, setActiveStrategy] = useState(null);
  const [kpis, setKpis] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [editingKpi, setEditingKpi] = useState(null);
  const [updatingKpi, setUpdatingKpi] = useState(null);
  const [_collecting, setCollecting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // 获取当前战略
      const strategyRes = await strategyApi.getActive();
      const strategy = strategyRes.data;
      setActiveStrategy(strategy);

      if (strategy?.id) {
        // 获取 KPI 列表
        const kpiRes = await kpiApi.list({ strategy_id: strategy.id });
        setKpis(kpiRes.data || []);
      } else {
        setKpis([]);
      }
    } catch (error) {
      // 404 = 当前没有生效的战略，属于正常业务状态，显示空状态
      if (error?.response?.status === 404) {
        setActiveStrategy(null);
        setKpis([]);
        return;
      }
      console.error("加载数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingKpi(null);
    setDialogOpen(true);
  };

  // const handleEdit = (kpi) => {
  const handleUpdate = (kpi) => {
    setUpdatingKpi(kpi);
    setUpdateDialogOpen(true);
  };

  const handleCollect = async (kpi) => {
    if (!confirm(`确定要采集 KPI "${kpi.name}" 的数据吗？`)) return;

    try {
      setCollecting(true);
      await kpiApi.collect(kpi.id);
      loadData();
      alert("数据采集成功");
    } catch (error) {
      console.error("数据采集失败:", error);
      alert("采集失败，请重试");
    } finally {
      setCollecting(false);
    }
  };


  const handleSubmit = async (data) => {
    try {
      setSaving(true);
      if (editingKpi?.id) {
        await kpiApi.update(editingKpi.id, data);
      } else {
        await kpiApi.create({
          ...data,
          strategy_id: activeStrategy.id,
        });
      }
      setDialogOpen(false);
      loadData();
    } catch (error) {
      console.error("保存 KPI 失败:", error);
      alert("保存失败，请重试");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateValue = async (data) => {
    if (!updatingKpi?.id) return;

    try {
      setSaving(true);
      await kpiApi.updateValue(updatingKpi.id, data);
      setUpdateDialogOpen(false);
      loadData();
    } catch (error) {
      console.error("更新 KPI 值失败:", error);
      alert("更新失败，请重试");
    } finally {
      setSaving(false);
    }
  };

  const filteredKpis = kpis.filter(
    (kpi) =>
      !searchQuery ||
      kpi.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      kpi.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 按维度分组
  const kpisByDimension = filteredKpis.reduce((acc, kpi) => {
    const dim = kpi.dimension?.toUpperCase() || "FINANCIAL";
    if (!acc[dim]) {
      acc[dim] = [];
    }
    acc[dim].push(kpi);
    return acc;
  }, {});

  // 渲染加载骨架屏
  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-10 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="KPI 指标管理"
        description="管理关键绩效指标 | 数据采集 | 历史趋势"
        breadcrumbs={[
          { label: "战略管理", href: "/strategy/analysis" },
          { label: "KPI 管理" },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={loadData}
              className="flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              刷新
            </Button>
            {activeStrategy && (
              <Button onClick={handleCreate} className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                新建 KPI
              </Button>
            )}
          </div>
        }
      />

      {/* 无生效战略时的空状态 */}
      {!activeStrategy && (
        <motion.div variants={fadeIn}>
          <Card className="border-dashed border-slate-600/50 bg-slate-800/30">
            <CardContent className="py-16 text-center">
              <Target className="w-14 h-14 text-slate-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-300 mb-2">
                当前没有生效的战略
              </h3>
              <p className="text-sm text-slate-500 mb-6 max-w-md mx-auto">
                请先在战略管理中创建年度战略并发布，发布后可在此管理 KPI 指标。
              </p>
              <Button asChild variant="outline" className="border-slate-500/50">
                <Link to="/strategy/analysis">前往战略管理</Link>
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* 当前战略信息 */}
      {activeStrategy && (
        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="py-3">
              <div className="flex items-center gap-3">
                <Target className="w-4 h-4 text-primary" />
                <span className="text-sm text-slate-400">当前战略:</span>
                <span className="text-sm font-medium text-white">
                  {activeStrategy.name} ({activeStrategy.year}年度)
                </span>
                <Badge variant="outline" className="ml-auto">
                  共 {kpis.length} 个 KPI
                </Badge>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* 有生效战略时显示搜索与 KPI 列表 */}
      {activeStrategy && (
        <>
      {/* 搜索栏 */}
      <motion.div variants={fadeIn} className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            value={searchQuery || ""}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索 KPI 名称或描述..."
            className="pl-9 bg-slate-800/50 border-slate-700"
          />
        </div>
      </motion.div>

      {/* KPI 列表按维度分组 */}
      <div className="space-y-6">
        {Object.entries(BSC_DIMENSIONS).map(([dimension, config]) => {
          const dimensionKpis = kpisByDimension[dimension] || [];
          const Icon = config.icon;

          return (
            <motion.div key={dimension} variants={fadeIn}>
              <Card className="overflow-hidden">
                <CardHeader
                  className="py-3"
                  style={{ backgroundColor: `${config.color}10` }}
                >
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4" style={{ color: config.color }} />
                    <CardTitle className="text-sm" style={{ color: config.color }}>
                      {config.name}
                    </CardTitle>
                    <Badge variant="outline" className="text-xs ml-auto">
                      {dimensionKpis.length} 个 KPI
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-4">
                  {dimensionKpis.length > 0 ? (
                    <motion.div
                      variants={staggerContainer}
                      initial="hidden"
                      animate="visible"
                      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                    >
                      {dimensionKpis.map((kpi) => (
                        <KPICard
                          key={kpi.id}
                          kpi={kpi}
                          color={config.color}
                          onUpdate={handleUpdate}
                          onCollect={handleCollect}
                        />
                      ))}
                    </motion.div>
                  ) : (
                    <div className="py-8 text-center text-slate-500 text-sm">
                      暂无 KPI 指标
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
        </>
      )}

      {/* 创建/编辑弹窗 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingKpi?.id ? "编辑 KPI" : "创建 KPI"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <KPIForm
              kpi={editingKpi}
              onSubmit={handleSubmit}
              onCancel={() => setDialogOpen(false)}
              loading={saving}
            />
          </DialogBody>
        </DialogContent>
      </Dialog>

      {/* 更新值弹窗 */}
      <UpdateValueDialog
        kpi={updatingKpi}
        open={updateDialogOpen}
        onClose={() => setUpdateDialogOpen(false)}
        onSubmit={handleUpdateValue}
        loading={saving}
      />
    </motion.div>
  );
}
