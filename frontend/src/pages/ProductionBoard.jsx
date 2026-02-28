/**
 * 生产看板 - Production Board Dashboard
 * 汇总工单状态、生产进度、车间负荷
 */
import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Factory, ClipboardList, Play, CheckCircle2, AlertTriangle,
  RefreshCw, Clock, Users, Wrench, BarChart3, Calendar
} from "lucide-react";
import { productionApi } from "../services/api";
import { PageHeader } from "../components/layout";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";

const STATUS_CONFIG = {
  pending: { label: "待开始", color: "bg-slate-500/20 text-slate-400 border-slate-500/30", icon: Clock },
  in_progress: { label: "进行中", color: "bg-blue-500/20 text-blue-400 border-blue-500/30", icon: Play },
  completed: { label: "已完成", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30", icon: CheckCircle2 },
  paused: { label: "已暂停", color: "bg-amber-500/20 text-amber-400 border-amber-500/30", icon: AlertTriangle },
};

const PRIORITY_CONFIG = {
  HIGH: { label: "高", color: "bg-red-500/20 text-red-400" },
  MEDIUM: { label: "中", color: "bg-amber-500/20 text-amber-400" },
  LOW: { label: "低", color: "bg-slate-500/20 text-slate-400" },
  NORMAL: { label: "普通", color: "bg-slate-500/20 text-slate-400" },
};

export default function ProductionBoard() {
  const [workOrders, setWorkOrders] = useState([]);
  const [plans, setPlans] = useState([]);
  const [workshops, setWorkshops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const results = await Promise.allSettled([
        productionApi.workOrders.getList({ page_size: 1000 }),
        productionApi.plans.getList({ page_size: 100 }),
        productionApi.workshops.getList({ page_size: 100 }),
      ]);
      if (results[0].status === "fulfilled") {
        const d = results[0].value?.data;
        setWorkOrders(d?.items || d || []);
      }
      if (results[1].status === "fulfilled") {
        const d = results[1].value?.data;
        setPlans(d?.items || d || []);
      }
      if (results[2].status === "fulfilled") {
        const d = results[2].value?.data;
        setWorkshops(d?.items || d || []);
      }
    } catch (e) {
      console.error("Failed to fetch production data:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  // Stats
  const stats = useMemo(() => {
    const total = workOrders.length;
    const pending = workOrders.filter(w => w.status === "pending").length;
    const inProgress = workOrders.filter(w => w.status === "in_progress").length;
    const completed = workOrders.filter(w => w.status === "completed").length;
    const delayed = workOrders.filter(w => {
      if (!w.planned_end_date) return false;
      return new Date(w.planned_end_date) < new Date() && w.status !== "completed";
    }).length;
    return [
      { label: "工单总数", value: total, icon: ClipboardList, color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
      { label: "进行中", value: inProgress, icon: Play, color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20" },
      { label: "已完成", value: completed, icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
      { label: "逾期", value: delayed, icon: AlertTriangle, color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
    ];
  }, [workOrders]);

  // Group work orders by status for kanban
  const kanbanColumns = useMemo(() => {
    const cols = {
      pending: { label: "待开始", items: [], color: "border-slate-500/30" },
      in_progress: { label: "进行中", items: [], color: "border-blue-500/30" },
      completed: { label: "已完成", items: [], color: "border-emerald-500/30" },
    };
    (workOrders || []).forEach(wo => {
      const status = wo.status || "pending";
      if (cols[status]) cols[status].items.push(wo);
      else if (status === "paused") cols.pending.items.push(wo);
    });
    return cols;
  }, [workOrders]);

  // Workshop load
  const workshopLoad = useMemo(() => {
    return (workshops || []).map(ws => {
      const wsOrders = (workOrders || []).filter(wo => wo.workshop_id === ws.id);
      const activeOrders = wsOrders.filter(wo => wo.status === "in_progress").length;
      const totalOrders = wsOrders.length;
      return { ...ws, activeOrders, totalOrders };
    });
  }, [workshops, workOrders]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-primary animate-spin" />
          <p className="text-slate-400">加载生产数据...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="min-h-screen bg-background p-6 space-y-6"
      variants={staggerContainer}
      initial="hidden"
      animate="show"
    >
      <PageHeader
        title="生产看板"
        subtitle={`${workOrders.length} 个工单 · ${plans.length} 个生产计划 · ${workshops.length} 个车间`}
        icon={Factory}
        actions={
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 transition-colors"
            disabled={refreshing}
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
            刷新
          </button>
        }
      />

      {/* Stats Row */}
      <motion.div className="grid grid-cols-2 md:grid-cols-4 gap-4" variants={fadeIn}>
        {stats.map((stat, i) => (
          <Card key={i} className={cn("border", stat.bg)}>
            <CardContent className="p-4 flex items-center gap-4">
              <div className={cn("p-3 rounded-xl bg-white/5")}>
                <stat.icon className={cn("w-6 h-6", stat.color)} />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Production Plans */}
      {plans.length > 0 && (
        <motion.div variants={fadeIn}>
          <h2 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            生产计划进度
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {plans.map(plan => {
              const planOrders = (workOrders || []).filter(wo => wo.production_plan_id === plan.id);
              const completedCount = planOrders.filter(wo => wo.status === "completed").length;
              const total = planOrders.length;
              const pct = total > 0 ? Math.round((completedCount / total) * 100) : 0;
              return (
                <Card key={plan.id} className="border border-border">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium text-foreground truncate">{plan.plan_name || plan.name || `计划#${plan.id}`}</h3>
                      <Badge className={cn(
                        "text-xs",
                        plan.status === "completed" ? "bg-emerald-500/20 text-emerald-400" :
                        plan.status === "in_progress" ? "bg-blue-500/20 text-blue-400" :
                        "bg-slate-500/20 text-slate-400"
                      )}>
                        {plan.status === "completed" ? "已完成" : plan.status === "in_progress" ? "进行中" : "待开始"}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {plan.start_date && <span>{plan.start_date.slice(0,10)}</span>}
                      {plan.start_date && plan.end_date && <span> → </span>}
                      {plan.end_date && <span>{plan.end_date.slice(0,10)}</span>}
                    </div>
                    <div>
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>{completedCount}/{total} 工单</span>
                        <span>{pct}%</span>
                      </div>
                      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Work Order Kanban */}
      <motion.div variants={fadeIn}>
        <h2 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
          <ClipboardList className="w-5 h-5 text-primary" />
          工单看板
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(kanbanColumns).map(([status, col]) => (
            <div key={status} className={cn("rounded-xl border bg-card/50 p-4", col.color)}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-foreground">{col.label}</h3>
                <Badge variant="outline" className="text-xs">{col.items.length}</Badge>
              </div>
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {col.items.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">暂无工单</p>
                ) : col.items.map(wo => (
                  <Card key={wo.id} className="border border-border hover:border-primary/30 transition-colors">
                    <CardContent className="p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono text-muted-foreground">{wo.work_order_no}</span>
                        {wo.priority && PRIORITY_CONFIG[wo.priority] && (
                          <Badge className={cn("text-xs", PRIORITY_CONFIG[wo.priority].color)}>
                            {PRIORITY_CONFIG[wo.priority].label}
                          </Badge>
                        )}
                      </div>
                      <p className="font-medium text-sm text-foreground">{wo.task_name}</p>
                      {wo.project_name && (
                        <p className="text-xs text-muted-foreground truncate">
                          📋 {wo.project_name}
                        </p>
                      )}
                      {wo.workshop_name && (
                        <p className="text-xs text-muted-foreground">
                          🏭 {wo.workshop_name}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Workshop Load */}
      {workshopLoad.length > 0 && (
        <motion.div variants={fadeIn}>
          <h2 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            车间负荷
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {workshopLoad.map(ws => (
              <Card key={ws.id} className="border border-border">
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <Factory className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-medium text-foreground">{ws.name}</h3>
                      <p className="text-xs text-muted-foreground">{ws.workshop_type || "车间"}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white/5 rounded-lg p-2 text-center">
                      <p className="text-lg font-bold text-blue-400">{ws.activeOrders}</p>
                      <p className="text-xs text-muted-foreground">进行中</p>
                    </div>
                    <div className="bg-white/5 rounded-lg p-2 text-center">
                      <p className="text-lg font-bold text-foreground">{ws.totalOrders}</p>
                      <p className="text-xs text-muted-foreground">总工单</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
