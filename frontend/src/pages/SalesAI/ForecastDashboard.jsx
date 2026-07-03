/**
 * 销售预测与目标管理 - 领导驾驶舱
 * 
 * 功能：
 * 1. 公司整体预测与目标对比
 * 2. 团队分解
 * 3. 个人分解
 * 4. 目标设置（弹窗）
 */

import { useState, useEffect, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  Target,
  DollarSign,
  Users,
  Award,
  AlertTriangle,
  Activity,
  BarChart3,
  Settings,
  Plus,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
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
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Alert,
} from "../../components/ui";
import TargetSettingModal from "../../components/sales/TargetSettingModal";
import api, { salesTargetApi } from "../../services/api";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

// 漏斗阶段中文名（与后端 OpportunityStageEnum 对齐）
const STAGE_LABELS = {
  DISCOVERY: "初步接触",
  QUALIFICATION: "需求挖掘",
  PROPOSAL: "方案介绍",
  NEGOTIATION: "价格谈判",
  CLOSING: "成交促成",
};

// 公司整体预测（整合目标数据 + 真实预测接口）
function CompanyOverview({ targets }) {
  // 计算目标汇总（无数据就是 0，不再用演示常量兜底）
  const targetSummary = useMemo(() => {
    if (!targets || targets.length === 0) {
      return {
        quarterly_target: 0,
        actual_revenue: 0,
        completion_rate: 0,
        time_progress: 0,
      };
    }

    // 筛选当前季度的合同金额目标
    const now = new Date();
    const quarter = Math.ceil((now.getMonth() + 1) / 3);
    const quarterStr = `${now.getFullYear()}-Q${quarter}`;
    
    const quarterlyTargets = targets.filter(
      t => t.target_period === "QUARTERLY" && 
           t.period_value === quarterStr &&
           t.target_type === "CONTRACT_AMOUNT"
    );
    
    const totalTarget = quarterlyTargets.reduce((sum, t) => sum + Number(t.target_value || 0), 0);
    const totalActual = quarterlyTargets.reduce((sum, t) => sum + Number(t.actual_value || 0), 0);
    
    // 计算时间进度
    const startOfQuarter = new Date(now.getFullYear(), (quarter - 1) * 3, 1);
    const endOfQuarter = new Date(now.getFullYear(), quarter * 3, 0);
    const totalDays = (endOfQuarter - startOfQuarter) / (1000 * 60 * 60 * 24);
    const elapsedDays = (now - startOfQuarter) / (1000 * 60 * 60 * 24);
    const timeProgress = Math.min(100, (elapsedDays / totalDays) * 100);
    
    return {
      quarterly_target: totalTarget,
      actual_revenue: totalActual,
      completion_rate: totalTarget > 0 ? (totalActual / totalTarget) * 100 : 0,
      time_progress: timeProgress,
    };
  }, [targets]);

  // 真实预测：SALES-06 接线后的 company-overview 端点（不再使用演示常量）
  const [forecast, setForecast] = useState(null);
  const [forecastError, setForecastError] = useState(null);
  useEffect(() => {
    api
      .get("/sales/forecast/forecast/company-overview", { params: { period: "quarterly" } })
      .then(({ data }) => setForecast(data?.data || data))
      .catch(() => setForecastError("预测服务暂不可用"));
  }, []);

  // 计算预测完成率
  const predictedCompletion = useMemo(() => {
    if (!forecast || targetSummary.quarterly_target === 0) return 0;
    return (forecast.prediction.predicted_revenue / targetSummary.quarterly_target) * 100;
  }, [targetSummary, forecast]);

  // 计算差距
  const predictedGap = forecast
    ? forecast.prediction.predicted_revenue - targetSummary.quarterly_target
    : 0;

  return (
    <div className="space-y-6">
      {/* 核心指标卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-slate-700">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
              <Target className="w-4 h-4" />
              季度目标
            </div>
            <div className="text-2xl font-bold text-white">
              {formatCurrency(targetSummary.quarterly_target)}
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-blue-500/50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
              <DollarSign className="w-4 h-4" />
              已完成
            </div>
            <div className="text-2xl font-bold text-blue-500">
              {formatCurrency(targetSummary.actual_revenue)}
            </div>
            <div className="text-sm text-slate-400">
              {targetSummary.completion_rate.toFixed(1)}%
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-green-500/50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
              <TrendingUp className="w-4 h-4" />
              AI 预测
            </div>
            <div className="text-2xl font-bold text-green-500">
              {forecast ? formatCurrency(forecast.prediction.predicted_revenue) : forecastError || "加载中…"}
            </div>
            <div className="text-sm text-green-500">
              {forecast ? `${predictedCompletion.toFixed(1)}%` : "—"}
            </div>
          </CardContent>
        </Card>
        
        <Card className={predictedGap >= 0 ? "border-emerald-500/50" : "border-orange-500/50"}>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">预测差距</div>
            <div className={`text-2xl font-bold ${predictedGap >= 0 ? "text-emerald-500" : "text-orange-500"}`}>
              {predictedGap >= 0 ? "+" : ""}{formatCurrency(predictedGap)}
            </div>
            <div className="text-sm text-slate-400">
              {forecast ? `置信度 ${forecast.prediction.confidence_level}%` : "—"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 进度对比 */}
      <Card>
        <CardHeader>
          <CardTitle>目标完成进度</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">时间进度</span>
                <span className="text-sm">{targetSummary.time_progress.toFixed(1)}%</span>
              </div>
              <Progress value={targetSummary.time_progress} className="h-3" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">业绩进度</span>
                <span className={`text-sm font-bold ${targetSummary.completion_rate < targetSummary.time_progress ? 'text-orange-500' : 'text-green-500'}`}>
                  {targetSummary.completion_rate.toFixed(1)}%
                </span>
              </div>
              <Progress value={targetSummary.completion_rate} className="h-3" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">预测进度</span>
                <span className="text-sm font-bold text-green-500">{predictedCompletion.toFixed(1)}%</span>
              </div>
              <Progress value={Math.min(100, predictedCompletion)} className="h-3" />
            </div>
          </div>

          {targetSummary.completion_rate < targetSummary.time_progress && (
            <Alert className="mt-4 border-orange-500 bg-orange-500/10">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              <div className="text-sm">
                <strong>注意：</strong>当前业绩进度落后时间进度
                {(targetSummary.time_progress - targetSummary.completion_rate).toFixed(1)}%
              </div>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* 漏斗贡献 */}
      <Card>
        <CardHeader>
          <CardTitle>漏斗商机贡献预测</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {!forecast && (
              <div className="text-sm text-slate-400">{forecastError || "加载中…"}</div>
            )}
            {Object.entries(forecast?.funnel_contribution || {})
              .filter(([stage]) => STAGE_LABELS[stage])
              .map(([stage, data]) => (
              <div key={stage} className="flex items-center gap-4">
                <div className="w-20 text-sm">{STAGE_LABELS[stage]}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-400">
                      {data.count}个商机 · {formatCurrency(data.total_amount)}
                    </span>
                    <span className="text-sm">赢单率{data.win_rate}%</span>
                  </div>
                  <Progress value={data.win_rate} className="h-2" />
                </div>
                <div className="w-24 text-right text-sm font-medium">
                  {formatCurrency(data.total_amount * data.win_rate / 100)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 团队分解
function TeamBreakdown({ targets }) {
  const teams = useMemo(() => {
    // 基于目标数据按团队/大区汇总
    const teamMap = new Map();
    
    (targets || []).forEach(t => {
      const region = t.meta?.region || t.department_name || "未分配";
      if (!teamMap.has(region)) {
        teamMap.set(region, {
          team_name: region,
          manager: t.user_name || "-",
          target: 0,
          actual: 0,
        });
      }
      const team = teamMap.get(region);
      team.target += Number(t.target_value || 0);
      team.actual += Number(t.actual_value || 0);
    });
    
    // 没有数据就是空清单，不再用演示大区兜底
    if (teamMap.size === 0) {
      return [];
    }
    
    return Array.from(teamMap.values())
      .map((team, idx) => ({
        ...team,
        completion: team.target > 0 ? (team.actual / team.target) * 100 : 0,
        predicted: team.target > 0 ? Math.min(120, (team.actual / team.target) * 100 * 1.5) : 0,
        risk: team.target > 0 && (team.actual / team.target) < 0.5 ? "HIGH" : 
              team.target > 0 && (team.actual / team.target) < 0.7 ? "MEDIUM" : "LOW",
        trend: "stable",
        rank: idx + 1,
      }))
      .sort((a, b) => b.completion - a.completion)
      .map((t, idx) => ({ ...t, rank: idx + 1 }));
  }, [targets]);

  const getRiskBadge = (risk) => {
    const config = {
      LOW: { label: "正常", variant: "default" },
      MEDIUM: { label: "关注", variant: "secondary" },
      HIGH: { label: "风险", variant: "destructive" },
    };
    return config[risk] || config.LOW;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>各团队预测完成率</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>排名</TableHead>
                <TableHead>团队</TableHead>
                <TableHead>负责人</TableHead>
                <TableHead className="text-right">目标</TableHead>
                <TableHead className="text-right">已完成</TableHead>
                <TableHead className="text-right">完成率</TableHead>
                <TableHead className="text-right">预测</TableHead>
                <TableHead>风险</TableHead>
                <TableHead>趋势</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {teams.map((team) => (
                <TableRow key={team.team_name} className={team.risk === "HIGH" ? "bg-red-500/5" : ""}>
                  <TableCell>
                    <Badge variant={team.rank === 1 ? "default" : "secondary"}>No.{team.rank}</Badge>
                  </TableCell>
                  <TableCell className="font-medium">{team.team_name}</TableCell>
                  <TableCell>{team.manager}</TableCell>
                  <TableCell className="text-right">{formatCurrency(team.target)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(team.actual)}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={team.completion >= 60 ? "default" : "secondary"}>
                      {team.completion.toFixed(1)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={team.predicted >= 100 ? "text-green-500 font-bold" : "text-orange-500"}>
                      {team.predicted.toFixed(1)}%
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getRiskBadge(team.risk).variant}>{getRiskBadge(team.risk).label}</Badge>
                  </TableCell>
                  <TableCell>
                    {team.trend === "up" && <TrendingUp className="w-4 h-4 text-green-500" />}
                    {team.trend === "down" && <TrendingDown className="w-4 h-4 text-red-500" />}
                    {team.trend === "stable" && <Activity className="w-4 h-4 text-slate-400" />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// 个人分解
function SalesRepBreakdown({ targets }) {
  const reps = useMemo(() => {
    // 筛选个人目标
    const personalTargets = (targets || []).filter(t => t.target_scope === "PERSONAL");
    
    // 没有个人目标就是空清单，不再用演示人员兜底
    if (personalTargets.length === 0) {
      return [];
    }
    
    return personalTargets
      .map(t => ({
        name: t.user_name || "未知",
        team: t.meta?.region || t.department_name || "-",
        target: Number(t.target_value || 0),
        actual: Number(t.actual_value || 0),
        completion: t.target_value > 0 ? (t.actual_value / t.target_value) * 100 : 0,
        predicted: t.target_value > 0 ? Math.min(120, (t.actual_value / t.target_value) * 100 * 1.5) : 0,
        pipeline: Number(t.actual_value || 0) * 1.3,
      }))
      .sort((a, b) => b.completion - a.completion)
      .map((r, idx) => ({ ...r, rank: idx + 1 }));
  }, [targets]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>销售人员预测排名</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>排名</TableHead>
                <TableHead>姓名</TableHead>
                <TableHead>团队</TableHead>
                <TableHead className="text-right">目标</TableHead>
                <TableHead className="text-right">已完成</TableHead>
                <TableHead className="text-right">完成率</TableHead>
                <TableHead className="text-right">预测</TableHead>
                <TableHead className="text-right">漏斗</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reps.map((rep) => (
                <TableRow key={rep.name} className={rep.predicted < 100 ? "bg-orange-500/5" : ""}>
                  <TableCell>
                    {rep.rank === 1 && <Award className="w-5 h-5 text-yellow-500" />}
                    {rep.rank === 2 && <Award className="w-5 h-5 text-slate-400" />}
                    {rep.rank === 3 && <Award className="w-5 h-5 text-orange-500" />}
                    {rep.rank > 3 && <span className="text-slate-400">{rep.rank}</span>}
                  </TableCell>
                  <TableCell className="font-medium">{rep.name}</TableCell>
                  <TableCell>{rep.team}</TableCell>
                  <TableCell className="text-right">{formatCurrency(rep.target)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(rep.actual)}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={rep.completion >= 60 ? "default" : "secondary"}>
                      {rep.completion.toFixed(1)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={rep.predicted >= 100 ? "text-green-500 font-bold" : "text-orange-500"}>
                      {rep.predicted.toFixed(1)}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right text-slate-400">
                    {formatCurrency(rep.pipeline)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// 领导驾驶舱
// 主页面
export default function ForecastDashboard() {
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [targets, setTargets] = useState([]);
  
  // 初始加载目标数据
  useEffect(() => {
    const loadTargets = async () => {
      try {
        const res = await salesTargetApi.list({ page: 1, page_size: 100 });
        if (res.data?.items) {
          setTargets(res.data.items.map(t => ({
            ...t,
            meta: parseMeta(t.description),
            actual_value: Number(t.actual_value || 0),
          })));
        }
      } catch (err) {
        console.error("Failed to load targets:", err);
      }
    };
    loadTargets();
  }, []);

  // 解析 meta 数据
  const parseMeta = (description) => {
    if (!description || !description.includes("[meta]")) return {};
    try {
      const raw = description.split("[meta]")[1];
      return JSON.parse(raw);
    } catch {
      return {};
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="销售目标与预测"
          description="AI 驱动的公司整体销售计划完成情况预测"
          icon={<BarChart3 className="w-6 h-6 text-indigo-500" />}
          actions={
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowTargetModal(true)}>
                <Settings className="w-4 h-4 mr-2" />
                目标管理
              </Button>
              <Button onClick={() => setShowTargetModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                设置目标
              </Button>
            </div>
          }
        />

        <Tabs defaultValue="overview" className="mt-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[450px]">
            <TabsTrigger value="overview">
              <BarChart3 className="w-4 h-4 mr-2" />
              公司预测
            </TabsTrigger>
            <TabsTrigger value="team">
              <Users className="w-4 h-4 mr-2" />
              团队分解
            </TabsTrigger>
            <TabsTrigger value="individual">
              <Award className="w-4 h-4 mr-2" />
              个人分解
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <CompanyOverview targets={targets} />
          </TabsContent>

          <TabsContent value="team" className="mt-6">
            <TeamBreakdown targets={targets} />
          </TabsContent>

          <TabsContent value="individual" className="mt-6">
            <SalesRepBreakdown targets={targets} />
          </TabsContent>
        </Tabs>
      </div>

      {/* 目标设置弹窗 */}
      <TargetSettingModal
        open={showTargetModal}
        onOpenChange={setShowTargetModal}
        onTargetsChange={setTargets}
      />
    </div>
  );
}
