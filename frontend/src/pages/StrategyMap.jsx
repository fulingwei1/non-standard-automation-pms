/**
 * 战略地图页面 - BSC 战略地图可视化
 * 展示四个维度的 CSF 和 KPI 层级关系
 */
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  Users,
  Activity,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Target,
  Layers,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Skeleton } from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import { strategyApi, csfApi } from "@/services/api/strategy";
import { BSC_DIMENSIONS } from "@/lib/constants/strategy";

// 维度配置（使用任务指定的颜色）
const DIMENSION_CONFIG = {
  FINANCIAL: {
    ...BSC_DIMENSIONS.FINANCIAL,
    color: "#22c55e",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    icon: TrendingUp,
  },
  CUSTOMER: {
    ...BSC_DIMENSIONS.CUSTOMER,
    color: "#3b82f6",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    icon: Users,
  },
  INTERNAL: {
    ...BSC_DIMENSIONS.INTERNAL,
    color: "#f59e0b",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    icon: Activity,
  },
  LEARNING: {
    ...BSC_DIMENSIONS.LEARNING,
    color: "#a855f7",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    icon: BookOpen,
  },
};

// 维度顺序（从上到下）
const DIMENSION_ORDER = ["FINANCIAL", "CUSTOMER", "INTERNAL", "LEARNING"];

// CSF 卡片组件
function CSFCard({ csf, color }) {
  const [expanded, setExpanded] = useState(false);
  const kpiCount = csf.kpis?.length || 0;

  return (
    <motion.div
      variants={fadeIn}
      className="rounded-xl border border-white/10 bg-slate-800/50 overflow-hidden"
    >
      <div
        className="p-4 cursor-pointer hover:bg-slate-800/80 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
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
            <h4 className="text-sm font-semibold text-white mb-1">
              {csf.name}
            </h4>
            {csf.description && (
              <p className="text-xs text-slate-400 line-clamp-2">
                {csf.description}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-slate-400">关联 KPI</p>
              <p className="text-lg font-bold" style={{ color }}>
                {kpiCount}
              </p>
            </div>
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {expanded && kpiCount > 0 && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-white/5"
          >
            <div className="p-4 pt-3 bg-slate-900/30">
              <p className="text-xs text-slate-500 mb-2 flex items-center gap-1">
                <Target className="w-3 h-3" />
                关键绩效指标
              </p>
              <div className="space-y-2">
                {csf.kpis.map((kpi) => (
                  <div
                    key={kpi.id}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50"
                  >
                    <span className="text-xs text-slate-300">{kpi.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">
                        目标：{kpi.target_value}
                      </span>
                      <Badge
                        variant={
                          kpi.status === "ON_TRACK"
                            ? "success"
                            : kpi.status === "AT_RISK"
                              ? "warning"
                              : "danger"
                        }
                        className="text-xs"
                      >
                        {kpi.current_value || 0}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// 维度区域组件
function DimensionSection({ dimension, csfs, color, bgColor, borderColor, Icon }) {
  const config = DIMENSION_CONFIG[dimension];

  return (
    <motion.div
      variants={fadeIn}
      className="space-y-4"
    >
      <div className="flex items-center gap-3 mb-4">
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: bgColor, borderColor }}
        >
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">{config.name}</h3>
          <p className="text-xs text-slate-400">{config.description}</p>
        </div>
        <Badge variant="outline" className="ml-auto">
          {csfs?.length || 0} 个 CSF
        </Badge>
      </div>

      {csfs && csfs.length > 0 ? (
        <div className="grid grid-cols-1 gap-3">
          {csfs.map((csf) => (
            <CSFCard key={csf.id} csf={csf} color={color} />
          ))}
        </div>
      ) : (
        <div
          className="p-8 rounded-xl border border-dashed text-center"
          style={{ borderColor: "rgba(255,255,255,0.1)" }}
        >
          <Layers className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">暂无关键成功因素</p>
        </div>
      )}
    </motion.div>
  );
}

export default function StrategyMap() {
  const [loading, setLoading] = useState(true);
  const [activeStrategy, setActiveStrategy] = useState(null);
  const [dimensionData, setDimensionData] = useState({
    FINANCIAL: [],
    CUSTOMER: [],
    INTERNAL: [],
    LEARNING: [],
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // 获取当前生效战略
      const strategyRes = await strategyApi.getActive();
      const strategy = strategyRes.data;
      setActiveStrategy(strategy);

      if (strategy?.id) {
        // 获取各维度 CSF
        const csfRes = await csfApi.getByDimension(strategy.id);
        const csfs = csfRes.data || [];

        // 按维度分组
        const grouped = {
          FINANCIAL: [],
          CUSTOMER: [],
          INTERNAL: [],
          LEARNING: [],
        };

        csfs.forEach((csf) => {
          const dim = csf.dimension?.toUpperCase() || "FINANCIAL";
          if (grouped[dim]) {
            grouped[dim].push(csf);
          }
        });

        setDimensionData(grouped);
      }
    } catch (error) {
      console.error("加载战略地图失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 渲染加载骨架屏
  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <div className="space-y-6">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-64 w-full" />
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
        title="战略地图"
        description="BSC 平衡计分卡战略地图可视化 | 财务 → 客户 → 内部流程 → 学习成长"
        breadcrumbs={[
          { label: "战略管理", href: "/strategy" },
          { label: "战略地图" },
        ]}
      />

      {/* 当前战略信息 */}
      {activeStrategy && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-r from-slate-800/50 to-primary/10 border-primary/30">
            <CardContent className="py-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-primary/20">
                  <Target className="w-6 h-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h2 className="text-lg font-bold text-white">
                    {activeStrategy.name}
                  </h2>
                  <p className="text-sm text-slate-400">
                    {activeStrategy.year}年度 | {activeStrategy.vision || "暂无愿景描述"}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className={
                    activeStrategy.status === "ACTIVE"
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                  }
                >
                  {activeStrategy.status === "ACTIVE" ? "生效中" : activeStrategy.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* 战略地图可视化 - 四个维度从上到下 */}
      <div className="space-y-6">
        {DIMENSION_ORDER.map((dimension) => {
          const config = DIMENSION_CONFIG[dimension];
          return (
            <motion.div key={dimension} variants={fadeIn}>
              <Card
                className="overflow-hidden"
                style={{ borderColor: config.borderColor }}
              >
                <CardHeader
                  className="py-4"
                  style={{ backgroundColor: config.bgColor }}
                >
                  <div className="flex items-center gap-3">
                    <config.icon className="w-5 h-5" style={{ color: config.color }} />
                    <CardTitle className="text-base" style={{ color: config.color }}>
                      {config.name}
                    </CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="p-5">
                  <DimensionSection
                    dimension={dimension}
                    csfs={dimensionData[dimension]}
                    color={config.color}
                    bgColor={config.bgColor}
                    borderColor={config.borderColor}
                    Icon={config.icon}
                  />
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* 图例说明 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardContent className="py-4">
            <div className="flex items-center justify-center gap-6 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                <span>财务维度</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span>客户维度</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-amber-500" />
                <span>内部流程</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500" />
                <span>学习成长</span>
              </div>
              <div className="h-4 w-px bg-slate-600" />
              <span className="flex items-center gap-1">
                <ChevronRight className="w-3 h-3" />
                点击 CSF 展开查看 KPI
              </span>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
