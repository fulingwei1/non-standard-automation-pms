/**
 * 仓储管理员工作台
 * 核心入口页面，展示出入库任务、库存预警、盘点任务等
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Package,
  ArrowDownToLine,
  ArrowUpFromLine,
  AlertTriangle,
  ClipboardCheck,
  Search,
  Bell,
  TrendingUp,
  Warehouse,
  MapPin,
  Clock,
  CheckCircle2,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { fadeIn, staggerContainer } from "../../lib/animations";

// 统计卡片
function StatsCards({ stats }) {
  const cards = [
    {
      title: "待处理入库",
      value: stats.pendingInbound || 0,
      subtitle: "今日新增 " + (stats.todayInbound || 0),
      icon: ArrowDownToLine,
      color: "text-blue-400",
      bgColor: "bg-blue-400/10",
      path: "/warehouse/inbound?status=pending",
    },
    {
      title: "待处理出库",
      value: stats.pendingOutbound || 0,
      subtitle: "紧急 " + (stats.urgentOutbound || 0),
      icon: ArrowUpFromLine,
      color: "text-emerald-400",
      bgColor: "bg-emerald-400/10",
      path: "/warehouse/outbound?status=pending",
    },
    {
      title: "库存预警",
      value: stats.alerts || 0,
      subtitle: "低库存 " + (stats.lowStock || 0),
      icon: AlertTriangle,
      color: "text-amber-400",
      bgColor: "bg-amber-400/10",
      path: "/warehouse/alerts",
    },
    {
      title: "本月盘点",
      value: stats.countTasks || 0,
      subtitle: "完成 " + (stats.countCompleted || 0),
      icon: ClipboardCheck,
      color: "text-violet-400",
      bgColor: "bg-violet-400/10",
      path: "/warehouse/count",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <a key={index} href={card.path}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-surface-200 rounded-xl p-5 border border-white/5 hover:border-white/10 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm text-text-secondary mb-1">{card.title}</p>
                  <p className="text-3xl font-bold text-text-primary mb-1">{card.value}</p>
                  <p className="text-xs text-text-muted">{card.subtitle}</p>
                </div>
                <div className={`p-3 rounded-lg ${card.bgColor}`}>
                  <Icon className={`h-5 w-5 ${card.color}`} />
                </div>
              </div>
            </motion.div>
          </a>
        );
      })}
    </div>
  );
}

// 任务列表卡片
function TaskListCard({ title, tasks, icon: Icon, viewAllPath, emptyMessage }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-200 rounded-xl border border-white/5"
    >
      <div className="p-5 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-violet-500/10">
              <Icon className="h-5 w-5 text-violet-400" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
          </div>
          <a href={viewAllPath} className="text-sm text-violet-400 hover:text-violet-300">
            查看全部 →
          </a>
        </div>
      </div>
      <div className="p-5">
        {tasks.length === 0 ? (
          <div className="text-center py-8 text-text-muted">{emptyMessage}</div>
        ) : (
          <div className="space-y-3">
            {tasks.slice(0, 5).map((task, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-surface-300 hover:bg-surface-400 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-text-primary truncate">
                      {task.code || task.materialName}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        task.priority === "high"
                          ? "bg-red-500/20 text-red-400"
                          : task.priority === "medium"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {task.status}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted truncate">{task.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-text-muted">{task.time}</p>
                  <p className="text-xs text-text-muted">{task.date}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// 快捷操作
function QuickActions() {
  const actions = [
    { name: "入库登记", icon: ArrowDownToLine, path: "/warehouse/inbound/new", color: "from-blue-500 to-cyan-600" },
    { name: "出库拣货", icon: ArrowUpFromLine, path: "/warehouse/outbound/new", color: "from-emerald-500 to-teal-600" },
    { name: "库存查询", icon: Search, path: "/warehouse/inventory", color: "from-violet-500 to-purple-600" },
    { name: "盘点任务", icon: ClipboardCheck, path: "/warehouse/count", color: "from-amber-500 to-orange-600" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-200 rounded-xl border border-white/5 p-5"
    >
      <h3 className="text-lg font-semibold text-text-primary mb-4">快捷操作</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {actions.map((action, index) => {
          const Icon = action.icon;
          return (
            <a
              key={index}
              href={action.path}
              className={`flex flex-col items-center justify-center p-4 rounded-xl bg-gradient-to-br ${action.color} hover:opacity-90 transition-opacity`}
            >
              <Icon className="h-6 w-6 text-white mb-2" />
              <span className="text-sm font-medium text-white">{action.name}</span>
            </a>
          );
        })}
      </div>
    </motion.div>
  );
}

// 库存预警列表
function StockAlertList({ alerts }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-200 rounded-xl border border-white/5"
    >
      <div className="p-5 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">库存预警</h3>
          </div>
          <a href="/warehouse/alerts" className="text-sm text-violet-400 hover:text-violet-300">
            查看全部 →
          </a>
        </div>
      </div>
      <div className="p-5">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-text-muted">暂无预警</div>
        ) : (
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-surface-300"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-text-primary">{alert.materialName}</p>
                  <p className="text-xs text-text-muted">
                    规格: {alert.specification} | 库位: {alert.location}
                  </p>
                </div>
                <div className="text-right">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-red-400">{alert.currentStock}</span>
                    <span className="text-xs text-text-muted">/</span>
                    <span className="text-xs text-text-muted">{alert.minStock}</span>
                  </div>
                  <span className="text-xs text-amber-400">{alert.type}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function WarehouseWorkstation() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [inboundTasks, setInboundTasks] = useState([]);
  const [outboundTasks, setOutboundTasks] = useState([]);
  const [stockAlerts, setStockAlerts] = useState([]);

  useEffect(() => {
    // TODO: 从 API 加载数据
    // 模拟数据
    setTimeout(() => {
      setStats({
        pendingInbound: 5,
        todayInbound: 2,
        pendingOutbound: 8,
        urgentOutbound: 3,
        alerts: 12,
        lowStock: 7,
        countTasks: 3,
        countCompleted: 1,
      });
      setInboundTasks([
        { code: "IB-2026-0123", materialName: "伺服电机", status: "待入库", priority: "high", description: "型号: R88M-K1K030", time: "14:30", date: "2026-01-22" },
        { code: "IB-2026-0124", materialName: "直线导轨", status: "待入库", priority: "medium", description: "规格: HGH20CA", time: "10:15", date: "2026-01-22" },
      ]);
      setOutboundTasks([
        { code: "OB-2026-0089", materialName: "伺服电机", status: "拣货中", priority: "high", description: "项目: PJ250108001", time: "16:00", date: "2026-01-22" },
        { code: "OB-2026-0090", materialName: "控制器", status: "待拣货", priority: "medium", description: "项目: PJ250115002", time: "17:30", date: "2026-01-22" },
      ]);
      setStockAlerts([
        { materialName: "伺服电机", specification: "R88M-K1K030", location: "A01-01-01", currentStock: 5, minStock: 20, type: "低库存" },
        { materialName: "气缸", specification: "CDJ2B16-45", location: "B02-03-05", currentStock: 0, minStock: 50, type: "缺货" },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="仓储工作台"
        subtitle="仓储管理中心"
        icon={<Warehouse className="h-6 w-6" />}
      />

      <main className="container mx-auto px-4 py-6 max-w-7xl">
        <motion.div
          initial="initial"
          animate="animate"
          variants={staggerContainer}
          className="space-y-6"
        >
          {/* 统计卡片 */}
          <StatsCards stats={stats} />

          {/* 快捷操作 */}
          <QuickActions />

          {/* 任务列表 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TaskListCard
              title="入库任务"
              tasks={inboundTasks}
              icon={ArrowDownToLine}
              viewAllPath="/warehouse/inbound?status=pending"
              emptyMessage="暂无待处理入库任务"
            />
            <TaskListCard
              title="出库任务"
              tasks={outboundTasks}
              icon={ArrowUpFromLine}
              viewAllPath="/warehouse/outbound?status=pending"
              emptyMessage="暂无待处理出库任务"
            />
          </div>

          {/* 库存预警 */}
          <StockAlertList alerts={stockAlerts} />
        </motion.div>
      </main>
    </div>
  );
}
