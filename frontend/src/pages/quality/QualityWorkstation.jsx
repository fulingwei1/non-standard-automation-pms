/**
 * 质量工程师/质量主管工作台
 * 核心入口页面，展示检验任务、质量问题、验收任务等
 */
import React, { useState, useEffect } from "react";
import { qualityApi } from "../../services/api/quality";
import { motion } from "framer-motion";
import {
  CheckCircle,
  AlertCircle,
  FileCheck,
  TrendingUp,
  Search,
  Bell,
  Shield,
  ClipboardList,
  Award,
  AlertTriangle,
  Clock,
  CheckSquare,
  XCircle,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { staggerContainer } from "../../lib/animations";

// 统计卡片
function StatsCards({ stats }) {
  const cards = [
    {
      title: "待检验",
      value: stats.pendingInspection || 0,
      subtitle: "今日新增 " + (stats.todayInspection || 0),
      icon: FileCheck,
      color: "text-blue-400",
      bgColor: "bg-blue-400/10",
      path: "/quality/inspections?status=pending",
    },
    {
      title: "质量问题",
      value: stats.openIssues || 0,
      subtitle: "严重 " + (stats.criticalIssues || 0),
      icon: AlertTriangle,
      color: "text-amber-400",
      bgColor: "bg-amber-400/10",
      path: "/quality/issues?status=open",
    },
    {
      title: "待验收",
      value: stats.pendingAcceptance || 0,
      subtitle: "本周 " + (stats.weekAcceptance || 0),
      icon: Award,
      color: "text-violet-400",
      bgColor: "bg-violet-400/10",
      path: "/quality/acceptance?status=pending",
    },
    {
      title: "合格率",
      value: (stats.passRate || 98) + "%",
      subtitle: "环比 " + (stats.passRateTrend || "+0.5%"),
      icon: TrendingUp,
      color: "text-emerald-400",
      bgColor: "bg-emerald-400/10",
      path: "/quality/reports",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {(cards || []).map((card, index) => {
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

// 检验任务列表
function InspectionTasksCard({ tasks, viewAllPath }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-200 rounded-xl border border-white/5"
    >
      <div className="p-5 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <FileCheck className="h-5 w-5 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">检验任务</h3>
          </div>
          <a href={viewAllPath} className="text-sm text-violet-400 hover:text-violet-300">
            查看全部 →
          </a>
        </div>
      </div>
      <div className="p-5">
        {tasks?.length === 0 ? (
          <div className="text-center py-8 text-text-muted">暂无检验任务</div>
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
                      {task.inspectionNo}
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
                      {task.priority === "high" ? "紧急" : task.priority === "medium" ? "中等" : "普通"}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted truncate">
                    {task.materialName} | {task.projectCode}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-text-muted">{task.dueDate}</p>
                  <p className="text-xs text-text-muted">{task.inspector}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// 质量问题列表
function QualityIssuesCard({ issues, viewAllPath }) {
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
              <AlertCircle className="h-5 w-5 text-amber-400" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">质量问题</h3>
          </div>
          <a href={viewAllPath} className="text-sm text-violet-400 hover:text-violet-300">
            查看全部 →
          </a>
        </div>
      </div>
      <div className="p-5">
        {issues?.length === 0 ? (
          <div className="text-center py-8 text-text-muted">暂无质量问题</div>
        ) : (
          <div className="space-y-3">
            {issues.slice(0, 5).map((issue, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-surface-300 hover:bg-surface-400 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-text-primary truncate">
                      {issue.issueNo}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        issue.level === "critical"
                          ? "bg-red-500/20 text-red-400"
                          : issue.level === "major"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {issue.level === "critical" ? "严重" : issue.level === "major" ? "主要" : "次要"}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted truncate">{issue.description}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-text-muted">{issue.daysOpen} 天未关闭</p>
                  <p className="text-xs text-text-muted">{issue.responsible}</p>
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
    { name: "新建检验", icon: FileCheck, path: "/quality/inspections/new", color: "from-blue-500 to-cyan-600" },
    { name: "记录问题", icon: AlertCircle, path: "/quality/issues/new", color: "from-amber-500 to-orange-600" },
    { name: "验收管理", icon: Award, path: "/quality/acceptance", color: "from-violet-500 to-purple-600" },
    { name: "质量报表", icon: TrendingUp, path: "/quality/reports", color: "from-emerald-500 to-teal-600" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-200 rounded-xl border border-white/5 p-5"
    >
      <h3 className="text-lg font-semibold text-text-primary mb-4">快捷操作</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(actions || []).map((action, index) => {
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

// 验收任务列表
function AcceptanceTasksCard({ tasks, viewAllPath }) {
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
              <Award className="h-5 w-5 text-violet-400" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">验收任务</h3>
          </div>
          <a href={viewAllPath} className="text-sm text-violet-400 hover:text-violet-300">
            查看全部 →
          </a>
        </div>
      </div>
      <div className="p-5">
        {tasks?.length === 0 ? (
          <div className="text-center py-8 text-text-muted">暂无验收任务</div>
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
                      {task.projectName}
                    </span>
                    <span className="px-2 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400">
                      {task.type}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted truncate">{task.projectCode}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-text-muted">{task.scheduledDate}</p>
                  <p className="text-xs text-text-muted">{task.customer}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function QualityWorkstation() {
  const [_loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [inspectionTasks, setInspectionTasks] = useState([]);
  const [qualityIssues, setQualityIssues] = useState([]);
  const [acceptanceTasks, setAcceptanceTasks] = useState([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsRes, inspectionRes, alertsRes] = await Promise.all([
          qualityApi.statistics(),
          qualityApi.inspection.list({ status: 'pending' }),
          qualityApi.alerts.list({ status: 'open' }),
        ]);
        const statsData = statsRes.data || statsRes;
        setStats({
          pendingInspection: statsData.pendingInspection ?? 0,
          todayInspection: statsData.todayInspection ?? 0,
          openIssues: statsData.openIssues ?? 0,
          criticalIssues: statsData.criticalIssues ?? 0,
          pendingAcceptance: statsData.pendingAcceptance ?? 0,
          weekAcceptance: statsData.weekAcceptance ?? 0,
          passRate: statsData.passRate ?? 0,
          passRateTrend: statsData.passRateTrend ?? "",
        });
        const inspectionItems = inspectionRes.data?.items || inspectionRes.data?.items || inspectionRes.data || [];
        setInspectionTasks(Array.isArray(inspectionItems) ? inspectionItems : []);
        const alertItems = alertsRes.data?.items || alertsRes.data?.items || alertsRes.data || [];
        setQualityIssues(Array.isArray(alertItems) ? alertItems : []);
        // acceptanceTasks - use inspection list with acceptance type if available
        setAcceptanceTasks([]);
      } catch (err) {
        console.error('Failed to load quality workstation data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="质量工作台"
        subtitle="质量管理中心"
        icon={<Shield className="h-6 w-6" />}
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
            <InspectionTasksCard
              tasks={inspectionTasks}
              viewAllPath="/quality/inspections?status=pending"
            />
            <QualityIssuesCard
              issues={qualityIssues}
              viewAllPath="/quality/issues?status=open"
            />
          </div>

          {/* 验收任务 */}
          <AcceptanceTasksCard
            tasks={acceptanceTasks}
            viewAllPath="/quality/acceptance?status=pending"
          />
        </motion.div>
      </main>
    </div>
  );
}
