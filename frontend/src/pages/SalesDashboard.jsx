/**
 * Sales Dashboard - 销售仪表盘
 * Features:
 * 1. 个人业绩完成度
 * 2. 团队排行
 * 3. Pipeline 健康度
 * 4. 预测 vs 实际
 */

import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Target,
  TrendingUp,
  TrendingDown,
  Users,
  DollarSign,
  Award,
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  PieChart,
  Calendar,
  CheckCircle2,
  Clock,
  Zap,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { salesStatisticsApi, opportunityApi } from "../services/api";

// Mock data for dashboard (fallback when API unavailable)
const MOCK_PERSONAL = {
  target: 12000000,
  achieved: 7860000,
  quota_pct: 65.5,
  won_count: 8,
  pipeline_value: 15200000,
  avg_deal_size: 982500,
  monthly: [
    { month: "1月", target: 1000000, actual: 920000 },
    { month: "2月", target: 1000000, actual: 1100000 },
    { month: "3月", target: 1000000, actual: 1340000 },
    { month: "4月", target: 1000000, actual: 980000 },
    { month: "5月", target: 1000000, actual: 1120000 },
    { month: "6月", target: 1000000, actual: 1400000 },
  ],
};

const MOCK_TEAM_RANKING = [
  { name: "张三", amount: 3200000, deals: 5, target_pct: 80, avatar_color: "bg-blue-500" },
  { name: "李四", amount: 2800000, deals: 4, target_pct: 70, avatar_color: "bg-emerald-500" },
  { name: "王五", amount: 2100000, deals: 3, target_pct: 52.5, avatar_color: "bg-purple-500" },
  { name: "赵六", amount: 1900000, deals: 3, target_pct: 47.5, avatar_color: "bg-amber-500" },
  { name: "钱七", amount: 1500000, deals: 2, target_pct: 37.5, avatar_color: "bg-pink-500" },
  { name: "孙八", amount: 1200000, deals: 2, target_pct: 30, avatar_color: "bg-cyan-500" },
];

const MOCK_PIPELINE = {
  total_value: 28500000,
  weighted_value: 12800000,
  deal_count: 24,
  avg_cycle_days: 45,
  health_score: 72,
  stages: [
    { name: "初步接触", count: 8, value: 8500000, avg_days: 12, health: "good" },
    { name: "需求挖掘", count: 6, value: 7200000, avg_days: 18, health: "good" },
    { name: "方案介绍", count: 5, value: 6800000, avg_days: 22, health: "warning" },
    { name: "价格谈判", count: 3, value: 4200000, avg_days: 15, health: "good" },
    { name: "成交促成", count: 2, value: 1800000, avg_days: 8, health: "good" },
  ],
  risks: [
    { type: "stalled", count: 3, desc: "3个商机超过30天无进展" },
    { type: "no_activity", count: 2, desc: "2个商机近14天无跟进" },
    { type: "overdue", count: 1, desc: "1个商机已过预计成交日期" },
  ],
};

const MOCK_FORECAST = {
  quarters: [
    { label: "Q1", forecast: 3500000, actual: 3360000, variance: -4 },
    { label: "Q2", forecast: 4200000, actual: 3800000, variance: -9.5 },
    { label: "Q3 (当前)", forecast: 4800000, actual: 2400000, variance: null },
    { label: "Q4", forecast: 5000000, actual: null, variance: null },
  ],
  accuracy: 87.5,
  total_forecast: 17500000,
  total_actual: 9560000,
};

export default function SalesDashboard() {
  const navigate = useNavigate();
  const [personal, setPersonal] = useState(MOCK_PERSONAL);
  const [teamRanking, setTeamRanking] = useState(MOCK_TEAM_RANKING);
  const [pipeline, setPipeline] = useState(MOCK_PIPELINE);
  const [forecast, setForecast] = useState(MOCK_FORECAST);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [statsRes] = await Promise.allSettled([
          salesStatisticsApi?.getDashboard?.(),
        ]);
        if (statsRes.status === "fulfilled" && statsRes.value?.data) {
          const d = statsRes.value.data;
          if (d.personal) setPersonal(d.personal);
          if (d.team_ranking) setTeamRanking(d.team_ranking);
          if (d.pipeline) setPipeline(d.pipeline);
          if (d.forecast) setForecast(d.forecast);
        }
      } catch {
        // fallback to mock data
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const pipelineHealthColor = pipeline.health_score >= 80 ? "text-emerald-400" :
    pipeline.health_score >= 60 ? "text-amber-400" : "text-red-400";

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="销售仪表盘"
        description="个人业绩、团队表现、Pipeline 健康度一览"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <button
              onClick={() => navigate("/sales/funnel")}
              className="px-3 py-1.5 text-sm bg-surface-100 border border-white/10 rounded-lg text-slate-300 hover:text-white transition-colors"
            >
              销售漏斗
            </button>
            <button
              onClick={() => navigate("/sales/forecast-dashboard")}
              className="px-3 py-1.5 text-sm bg-surface-100 border border-white/10 rounded-lg text-slate-300 hover:text-white transition-colors"
            >
              预测详情
            </button>
          </motion.div>
        }
      />

      {/* KPI Overview Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Target className="w-5 h-5 text-blue-400" />
              <Badge variant="outline" className="text-xs text-blue-400 border-blue-500/30">
                {personal.quota_pct.toFixed(0)}%
              </Badge>
            </div>
            <div className="text-2xl font-bold text-white">
              ¥{(personal.achieved / 10000).toFixed(0)}万
            </div>
            <p className="text-xs text-slate-400 mt-1">
              目标 ¥{(personal.target / 10000).toFixed(0)}万
            </p>
            <Progress value={personal.quota_pct} className="h-1.5 mt-2" />
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white">{personal.won_count}</div>
            <p className="text-xs text-slate-400 mt-1">赢单数</p>
            <p className="text-xs text-emerald-400 mt-1">
              均单 ¥{(personal.avg_deal_size / 10000).toFixed(0)}万
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-purple-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-5 h-5 text-purple-400" />
              <span className={cn("text-sm font-bold", pipelineHealthColor)}>
                {pipeline.health_score}分
              </span>
            </div>
            <div className="text-2xl font-bold text-white">
              ¥{(pipeline.weighted_value / 10000).toFixed(0)}万
            </div>
            <p className="text-xs text-slate-400 mt-1">加权 Pipeline</p>
            <p className="text-xs text-slate-500 mt-1">
              {pipeline.deal_count}个商机 · 总额¥{(pipeline.total_value / 10000).toFixed(0)}万
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <BarChart3 className="w-5 h-5 text-amber-400" />
              <Badge variant="outline" className="text-xs text-amber-400 border-amber-500/30">
                {forecast.accuracy}%准确
              </Badge>
            </div>
            <div className="text-2xl font-bold text-white">
              ¥{(forecast.total_forecast / 10000).toFixed(0)}万
            </div>
            <p className="text-xs text-slate-400 mt-1">年度预测</p>
            <p className="text-xs text-slate-500 mt-1">
              已完成 ¥{(forecast.total_actual / 10000).toFixed(0)}万
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content - 2 column layout */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left: Personal Performance + Forecast */}
        <div className="xl:col-span-2 space-y-6">
          {/* Monthly Performance Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="w-4 h-4 text-blue-400" />
                个人业绩完成度
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {personal.monthly.map((m) => {
                  const pct = m.target > 0 ? (m.actual / m.target * 100) : 0;
                  const overTarget = pct >= 100;
                  return (
                    <div key={m.month} className="flex items-center gap-3">
                      <div className="w-8 text-xs text-slate-400">{m.month}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-6 bg-slate-800 rounded-md overflow-hidden relative">
                            <div
                              className={cn(
                                "h-full rounded-md transition-all",
                                overTarget ? "bg-emerald-500/60" : "bg-blue-500/60"
                              )}
                              style={{ width: `${Math.min(pct, 100)}%` }}
                            />
                            <div className="absolute inset-0 flex items-center px-2 justify-between">
                              <span className="text-xs text-white/80">
                                ¥{(m.actual / 10000).toFixed(0)}万
                              </span>
                              <span className="text-xs text-slate-500">
                                目标¥{(m.target / 10000).toFixed(0)}万
                              </span>
                            </div>
                          </div>
                          <span className={cn(
                            "text-xs font-medium w-10 text-right",
                            overTarget ? "text-emerald-400" : "text-blue-400"
                          )}>
                            {pct.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Forecast vs Actual */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="w-4 h-4 text-amber-400" />
                预测 vs 实际
                <Badge variant="outline" className="text-xs ml-auto">
                  预测准确率 {forecast.accuracy}%
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {forecast.quarters.map((q) => (
                  <div key={q.label} className="p-3 bg-slate-800/30 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white">{q.label}</span>
                      {q.variance != null && (
                        <Badge variant="outline" className={cn(
                          "text-xs",
                          q.variance >= 0 ? "text-emerald-400 border-emerald-500/30" : "text-red-400 border-red-500/30"
                        )}>
                          {q.variance >= 0 ? "+" : ""}{q.variance}%
                        </Badge>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="text-xs text-slate-500 mb-1">预测</div>
                        <div className="text-sm font-medium text-amber-400">
                          ¥{(q.forecast / 10000).toFixed(0)}万
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500 mb-1">实际</div>
                        <div className="text-sm font-medium text-emerald-400">
                          {q.actual != null ? `¥${(q.actual / 10000).toFixed(0)}万` : "—"}
                        </div>
                      </div>
                    </div>
                    {q.actual != null && (
                      <div className="mt-2 relative h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="absolute h-full bg-amber-500/40 rounded-full"
                          style={{ width: "100%" }}
                        />
                        <div
                          className="absolute h-full bg-emerald-500 rounded-full"
                          style={{ width: `${Math.min((q.actual / q.forecast) * 100, 100)}%` }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Pipeline Health */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Activity className="w-4 h-4 text-purple-400" />
                Pipeline 健康度
                <span className={cn("ml-auto text-lg font-bold", pipelineHealthColor)}>
                  {pipeline.health_score}/100
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Stage breakdown */}
              <div className="space-y-3 mb-4">
                {pipeline.stages.map((stage) => (
                  <div key={stage.name} className="flex items-center gap-3">
                    <div className="w-20 text-xs text-slate-400 truncate">{stage.name}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Progress
                          value={(stage.value / pipeline.total_value) * 100}
                          className="h-2 flex-1"
                        />
                        <span className="text-xs text-white w-16 text-right">
                          ¥{(stage.value / 10000).toFixed(0)}万
                        </span>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs w-8 justify-center">
                      {stage.count}
                    </Badge>
                    <span className="text-xs text-slate-500 w-12">
                      {stage.avg_days}天
                    </span>
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      stage.health === "good" ? "bg-emerald-500" :
                      stage.health === "warning" ? "bg-amber-500" : "bg-red-500"
                    )} />
                  </div>
                ))}
              </div>

              {/* Risk alerts */}
              {pipeline.risks.length > 0 && (
                <div className="pt-3 border-t border-white/5 space-y-2">
                  <div className="text-xs text-slate-400 font-medium">风险提醒</div>
                  {pipeline.risks.map((risk, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 bg-amber-500/5 border border-amber-500/10 rounded-lg">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                      <span className="text-xs text-amber-300">{risk.desc}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Team Ranking */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Award className="w-4 h-4 text-amber-400" />
                团队排行榜
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {teamRanking.map((member, idx) => (
                <div key={member.name} className={cn(
                  "flex items-center gap-3 p-3 rounded-lg transition-colors",
                  idx === 0 ? "bg-amber-500/5 border border-amber-500/10" :
                  idx === 1 ? "bg-slate-800/50" :
                  idx === 2 ? "bg-slate-800/30" : "bg-transparent"
                )}>
                  <div className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold",
                    idx === 0 ? "bg-amber-500 text-black" :
                    idx === 1 ? "bg-slate-400 text-black" :
                    idx === 2 ? "bg-amber-700 text-white" :
                    "bg-slate-700 text-slate-400"
                  )}>
                    {idx + 1}
                  </div>
                  <div className={cn("w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white", member.avatar_color)}>
                    {member.name.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-white">{member.name}</span>
                      <span className="text-sm font-bold text-white">
                        ¥{(member.amount / 10000).toFixed(0)}万
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-slate-500">{member.deals}单</span>
                      <div className="flex items-center gap-1.5">
                        <Progress value={member.target_pct} className="w-16 h-1.5" />
                        <span className={cn(
                          "text-xs",
                          member.target_pct >= 70 ? "text-emerald-400" :
                          member.target_pct >= 50 ? "text-amber-400" : "text-red-400"
                        )}>
                          {member.target_pct}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Zap className="w-4 h-4 text-blue-400" />
                快速指标
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-300">平均销售周期</span>
                </div>
                <span className="text-sm font-medium text-white">{pipeline.avg_cycle_days}天</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-300">平均单笔金额</span>
                </div>
                <span className="text-sm font-medium text-white">
                  ¥{(personal.avg_deal_size / 10000).toFixed(0)}万
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-300">Pipeline覆盖率</span>
                </div>
                <span className={cn(
                  "text-sm font-medium",
                  (pipeline.total_value / personal.target) >= 3 ? "text-emerald-400" :
                  (pipeline.total_value / personal.target) >= 2 ? "text-amber-400" : "text-red-400"
                )}>
                  {((pipeline.total_value / personal.target) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-slate-800/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-300">本月预计成交</span>
                </div>
                <span className="text-sm font-medium text-emerald-400">3个</span>
              </div>
            </CardContent>
          </Card>

          {/* Quick Navigation */}
          <Card>
            <CardContent className="p-3 space-y-1.5">
              {[
                { label: "商机管理", path: "/sales/opportunities", icon: Target },
                { label: "客户管理", path: "/sales/customers", icon: Users },
                { label: "报价管理", path: "/sales/quotes", icon: DollarSign },
                { label: "销售漏斗", path: "/sales/funnel", icon: Activity },
              ].map((item) => (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className="w-full flex items-center justify-between p-2.5 rounded-lg hover:bg-surface-100 text-sm text-slate-300 hover:text-white transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    <item.icon className="w-4 h-4 text-slate-500 group-hover:text-primary" />
                    {item.label}
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400" />
                </button>
              ))}
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </motion.div>
  );
}
