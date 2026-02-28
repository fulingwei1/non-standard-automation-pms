/**
 * CSF 关键成功因素管理列表
 * 按 BSC 维度分 Tab 显示，支持创建/编辑/删除
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Edit2,
  Trash2,
  Search,
  TrendingUp,
  Users,
  Activity,
  BookOpen,
  Target,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogBody,
  Skeleton,
} from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import { strategyApi, csfApi } from "@/services/api/strategy";
import { BSC_DIMENSIONS } from "@/lib/constants/strategy";

// 维度配置（使用任务指定的颜色）
const DIMENSION_CONFIG = {
  FINANCIAL: {
    ...BSC_DIMENSIONS.FINANCIAL,
    color: "#22c55e",
    icon: TrendingUp,
  },
  CUSTOMER: {
    ...BSC_DIMENSIONS.CUSTOMER,
    color: "#3b82f6",
    icon: Users,
  },
  INTERNAL: {
    ...BSC_DIMENSIONS.INTERNAL,
    color: "#f59e0b",
    icon: Activity,
  },
  LEARNING: {
    ...BSC_DIMENSIONS.LEARNING,
    color: "#a855f7",
    icon: BookOpen,
  },
};

const DIMENSION_TABS = [
  { value: "FINANCIAL", label: "财务维度" },
  { value: "CUSTOMER", label: "客户维度" },
  { value: "INTERNAL", label: "内部运营" },
  { value: "LEARNING", label: "学习成长" },
];

// CSF 表单组件
function CSFForm({ csf, dimensions, onSubmit, onCancel, loading }) {
  const [formData, setFormData] = useState({
    name: csf?.name || "",
    description: csf?.description || "",
    dimension: csf?.dimension || "FINANCIAL",
    weight: csf?.weight || 25,
    strategy_id: csf?.strategy_id || "",
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      weight: parseFloat(formData.weight),
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            CSF 名称 *
          </label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="输入关键成功因素名称"
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
            placeholder="描述该关键成功因素"
            rows={3}
            className="w-full rounded-lg bg-slate-800/50 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
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
              {dimensions.map((dim) => (
                <option key={dim.value} value={dim.value}>
                  {dim.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              权重 (%) *
            </label>
            <Input
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={formData.weight}
              onChange={(e) =>
                setFormData({ ...formData, weight: e.target.value })
              }
              className="bg-slate-800/50 border-slate-700"
              required
            />
          </div>
        </div>
      </div>

      <DialogFooter className="mt-6">
        <Button type="button" variant="outline" onClick={onCancel}>
          取消
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? "保存中..." : csf?.id ? "更新" : "创建"}
        </Button>
      </DialogFooter>
    </form>
  );
}

// CSF 卡片组件
function CSFCard({ csf, onEdit, onDelete, color }) {
  const kpiCount = csf.kpi_count || csf.kpis?.length || 0;

  return (
    <motion.div
      variants={fadeIn}
      whileHover={{ scale: 1.01 }}
      className="rounded-xl border border-white/10 bg-slate-800/50 p-4 hover:border-white/20 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-mono px-2 py-0.5 rounded"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {csf.code || `CSF-${csf.id}`}
          </span>
          <Badge variant="outline" className="text-xs">
            权重 {csf.weight?.toFixed(1) || 0}%
          </Badge>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => onEdit(csf)}
          >
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-red-400 hover:text-red-300"
            onClick={() => onDelete(csf)}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>

      <h4 className="text-sm font-semibold text-white mb-2">{csf.name}</h4>

      {csf.description && (
        <p className="text-xs text-slate-400 mb-3 line-clamp-2">
          {csf.description}
        </p>
      )}

      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Target className="w-3.5 h-3.5" />
          <span>关联 KPI</span>
        </div>
        <span className="text-sm font-bold" style={{ color }}>
          {kpiCount}
        </span>
      </div>
    </motion.div>
  );
}

export default function CSFList() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("FINANCIAL");
  const [activeStrategy, setActiveStrategy] = useState(null);
  const [csfs, setCsfs] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCsf, setEditingCsf] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (activeStrategy?.id) {
      loadCSFs();
    }
  }, [activeTab, activeStrategy]);

  const loadData = async () => {
    try {
      setLoading(true);
      const strategyRes = await strategyApi.getActive();
      setActiveStrategy(strategyRes.data);
    } catch (error) {
      console.error("加载战略失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadCSFs = async () => {
    if (!activeStrategy?.id) return;

    try {
      const res = await csfApi.list({
        strategy_id: activeStrategy.id,
        dimension: activeTab,
      });
      setCsfs(res.data || []);
    } catch (error) {
      console.error("加载 CSF 失败:", error);
    }
  };

  const handleCreate = () => {
    setEditingCsf(null);
    setDialogOpen(true);
  };

  const handleEdit = (csf) => {
    setEditingCsf(csf);
    setDialogOpen(true);
  };

  const handleDelete = async (csf) => {
    if (!confirm(`确定要删除 CSF "${csf.name}" 吗？`)) return;

    try {
      await csfApi.delete(csf.id);
      loadCSFs();
    } catch (error) {
      console.error("删除 CSF 失败:", error);
      alert("删除失败，请重试");
    }
  };

  const handleSubmit = async (data) => {
    try {
      setSaving(true);
      if (editingCsf?.id) {
        await csfApi.update(editingCsf.id, {
          ...data,
          strategy_id: activeStrategy.id,
        });
      } else {
        await csfApi.create({
          ...data,
          strategy_id: activeStrategy.id,
        });
      }
      setDialogOpen(false);
      loadCSFs();
    } catch (error) {
      console.error("保存 CSF 失败:", error);
      alert("保存失败，请重试");
    } finally {
      setSaving(false);
    }
  };

  const filteredCsfs = csfs.filter(
    (csf) =>
      !searchQuery ||
      csf.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      csf.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 渲染加载骨架屏
  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-10 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-40" />
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
        title="关键成功因素 (CSF)"
        description="管理 BSC 四个维度的关键成功因素"
        breadcrumbs={[
          { label: "战略管理", href: "/strategy" },
          { label: "CSF 管理" },
        ]}
        actions={
          <Button onClick={handleCreate} className="flex items-center gap-2">
            <Plus className="w-4 h-4" />
            新建 CSF
          </Button>
        }
      />

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
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* 搜索栏 */}
      <motion.div variants={fadeIn} className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索 CSF 名称或描述..."
            className="pl-9 bg-slate-800/50 border-slate-700"
          />
        </div>
      </motion.div>

      {/* 维度 Tab */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-slate-800/50 border-white/10">
          {DIMENSION_TABS.map((tab) => {
            const config = DIMENSION_CONFIG[tab.value];
            const Icon = config.icon;
            return (
              <TabsTrigger
                key={tab.value}
                value={tab.value}
                className="flex items-center gap-2"
              >
                <Icon className="w-4 h-4" style={{ color: config.color }} />
                {tab.label}
              </TabsTrigger>
            );
          })}
        </TabsList>

        {DIMENSION_TABS.map((tab) => (
          <TabsContent key={tab.value} value={tab.value} className="space-y-4">
            {filteredCsfs.length > 0 ? (
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
              >
                {filteredCsfs.map((csf) => (
                  <CSFCard
                    key={csf.id}
                    csf={csf}
                    color={DIMENSION_CONFIG[csf.dimension]?.color || "#22c55e"}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                  />
                ))}
              </motion.div>
            ) : (
              <Card className="bg-slate-800/30 border-slate-700/50">
                <CardContent className="py-12 text-center">
                  <Target className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400 mb-4">
                    {searchQuery
                      ? "没有找到匹配的 CSF"
                      : `暂无${tab.label}的 CSF`}
                  </p>
                  {!searchQuery && (
                    <Button onClick={handleCreate} variant="outline">
                      <Plus className="w-4 h-4 mr-2" />
                      创建第一个 CSF
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}
          </TabsContent>
        ))}
      </Tabs>

      {/* 创建/编辑弹窗 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingCsf?.id ? "编辑 CSF" : "创建 CSF"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <CSFForm
              csf={editingCsf}
              dimensions={DIMENSION_TABS}
              onSubmit={handleSubmit}
              onCancel={() => setDialogOpen(false)}
              loading={saving}
            />
          </DialogBody>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
