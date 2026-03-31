/**
 * KPI 管理列表页面
 * 展示 KPI 卡片、进度条、健康状态、历史趋势、数据采集
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Plus,
  Search,
  RefreshCw,
  Target,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
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
  DialogBody,
  Skeleton,
} from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { BSC_DIMENSIONS } from "../../lib/constants/strategy";
import useKPIData from "./useKPIData";
import KPIForm from "./KPIForm";
import KPICard from "./KPICard";
import UpdateValueDialog from "./UpdateValueDialog";

export default function KPIList() {
  const {
    loading,
    saving,
    activeStrategy,
    kpis,
    loadData,
    handleCollect,
    handleSubmit,
    handleUpdateValue,
  } = useKPIData();

  const [searchQuery, setSearchQuery] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [updateDialogOpen, setUpdateDialogOpen] = useState(false);
  const [editingKpi, setEditingKpi] = useState(null);
  const [updatingKpi, setUpdatingKpi] = useState(null);

  const handleCreate = () => {
    setEditingKpi(null);
    setDialogOpen(true);
  };

  const handleUpdate = (kpi) => {
    setUpdatingKpi(kpi);
    setUpdateDialogOpen(true);
  };

  const onFormSubmit = async (data) => {
    const success = await handleSubmit(data, editingKpi);
    if (success) {
      setDialogOpen(false);
    }
  };

  const onUpdateValue = async (data) => {
    const success = await handleUpdateValue(updatingKpi, data);
    if (success) {
      setUpdateDialogOpen(false);
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
              onSubmit={onFormSubmit}
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
        onSubmit={onUpdateValue}
        loading={saving}
      />
    </motion.div>
  );
}
