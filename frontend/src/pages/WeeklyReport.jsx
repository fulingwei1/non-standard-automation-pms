import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { cn as _cn } from "../lib/utils";
import { pmoApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Badge,
  Progress,
  Input,
  SkeletonCard,
  Button } from
"../components/ui";
import {
  Calendar,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  Briefcase,
  Target,
  ArrowRight,
  ChevronLeft,
  ChevronRight } from
"lucide-react";

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  }
};

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const _getHealthColor = (health) => {
  const colors = {
    H1: "text-emerald-400",
    H2: "text-amber-400",
    H3: "text-orange-400",
    H4: "text-red-400"
  };
  return colors[health] || colors.H1;
};

const getHealthBadge = (health) => {
  const badges = {
    H1: { label: "健康", variant: "success" },
    H2: { label: "良好", variant: "warning" },
    H3: { label: "警告", variant: "warning" },
    H4: { label: "危险", variant: "danger" }
  };
  return badges[health] || badges.H1;
};

export default function WeeklyReport() {
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);
  const [weekStart, setWeekStart] = useState(() => {
    // 计算当前周的周一
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1); // 调整为周一
    const monday = new Date(today.setDate(diff));
    return monday.toISOString().split("T")[0];
  });

  useEffect(() => {
    fetchData();
  }, [weekStart]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = weekStart ? { week_start: weekStart } : {};
      const res = await pmoApi.weeklyReport(params);
      const data = res.data || res;
      setReportData(data);
    } catch (err) {
      console.error("Failed to fetch weekly report:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePreviousWeek = () => {
    const date = new Date(weekStart);
    date.setDate(date.getDate() - 7);
    setWeekStart(date.toISOString().split("T")[0]);
  };

  const handleNextWeek = () => {
    const date = new Date(weekStart);
    date.setDate(date.getDate() + 7);
    setWeekStart(date.toISOString().split("T")[0]);
  };

  const handleCurrentWeek = () => {
    const today = new Date();
    const day = today.getDay();
    const diff = today.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(today.setDate(diff));
    setWeekStart(monday.toISOString().split("T")[0]);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="项目状态周报" description="项目周度状态汇总与分析" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array(8).
          fill(null).
          map((_, i) =>
          <SkeletonCard key={i} />
          )}
        </div>
      </div>);

  }

  if (!reportData) {
    return (
      <div className="space-y-6">
        <PageHeader title="项目状态周报" description="项目周度状态汇总与分析" />
        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            暂无数据
          </CardContent>
        </Card>
      </div>);

  }

  const {
    report_date,
    week_start,
    week_end,
    new_projects,
    completed_projects,
    delayed_projects,
    new_risks,
    resolved_risks,
    project_updates
  } = reportData;

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <PageHeader
        title="项目状态周报"
        description="项目周度状态汇总与分析"
        action={
        <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handlePreviousWeek}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleCurrentWeek}>
              本周
            </Button>
            <Button variant="outline" size="sm" onClick={handleNextWeek}>
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Input
            type="date"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
            className="w-40" />

        </div>
        } />


      {/* Week Info */}
      <Card className="mb-6">
        <CardContent className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">
                报告周期
              </h3>
              <p className="text-sm text-slate-400">
                {week_start ? formatDate(week_start) : ""} 至{" "}
                {week_end ? formatDate(week_end) : ""}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-400">报告日期</p>
              <p className="text-white font-medium">
                {report_date ? formatDate(report_date) : ""}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Briefcase className="h-5 w-5 text-blue-400" />
              </div>
              <TrendingUp className="h-5 w-5 text-emerald-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">新增项目</p>
            <p className="text-2xl font-bold text-white">{new_projects || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-emerald-500/20">
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              </div>
              <TrendingUp className="h-5 w-5 text-emerald-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">完成项目</p>
            <p className="text-2xl font-bold text-white">
              {completed_projects || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-red-500/20">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <TrendingDown className="h-5 w-5 text-red-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">延期项目</p>
            <p className="text-2xl font-bold text-red-400">
              {delayed_projects || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="p-2 rounded-lg bg-orange-500/20">
                <Target className="h-5 w-5 text-orange-400" />
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-1">新增风险</p>
            <p className="text-2xl font-bold text-white">{new_risks || 0}</p>
            <p className="text-xs text-slate-500 mt-1">
              解决: {resolved_risks || 0} 个
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Project Updates */}
      <motion.div variants={staggerChild}>
        <Card>
          <CardContent className="p-0">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <h3 className="text-lg font-semibold text-white">本周项目更新</h3>
              <Link
                to="/projects"
                className="flex items-center gap-1 text-sm text-primary hover:text-primary-light transition-colors">

                查看全部 <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {project_updates && project_updates.length > 0 ?
            <div className="divide-y divide-white/5">
                {(project_updates || []).map((project) => {
                const healthBadge = getHealthBadge(project.health || "H1");
                return (
                  <Link
                    key={project.project_id}
                    to={`/projects/${project.project_id}`}
                    className="block p-5 hover:bg-white/[0.02] transition-colors">

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-indigo-500/10 ring-1 ring-primary/20">
                            <Briefcase className="h-5 w-5 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-semibold text-white truncate">
                                {project.project_name}
                              </h4>
                              <Badge variant={healthBadge.variant}>
                                {healthBadge.label}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-slate-400">
                              <span>{project.project_code}</span>
                              <span>•</span>
                              <span>{project.stage || "S1"}</span>
                              <span>•</span>
                              <span>{project.status || "ST01"}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="w-32 hidden sm:block">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-400">进度</span>
                              <span className="text-white">
                                {project.progress || 0}%
                              </span>
                            </div>
                            <Progress value={project.progress || 0} />
                          </div>
                          <div className="text-xs text-slate-500">
                            {project.updated_at ?
                          formatDate(project.updated_at) :
                          ""}
                          </div>
                          <ArrowRight className="h-5 w-5 text-slate-500" />
                        </div>
                      </div>
                  </Link>);

              })}
            </div> :

            <div className="p-12 text-center text-slate-500">
                本周暂无项目更新
            </div>
            }
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>);

}