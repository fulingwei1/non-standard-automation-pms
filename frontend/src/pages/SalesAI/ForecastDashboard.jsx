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
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Target,
  DollarSign,
  Users,
  Award,
  AlertTriangle,
  ArrowUpRight,
  Activity,
  BarChart3,
  Eye,
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
import { salesTargetApi } from "../../services/api";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

// 公司整体预测（整合目标数据）
function CompanyOverview({ targets }) {
  // 计算目标汇总
  const targetSummary = useMemo(() => {
    if (!targets || targets.length === 0) {
      return {
        quarterly_target: 50000000,
        actual_revenue: 28500000,
        completion_rate: 57.0,
        time_progress: 66.7,
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
      quarterly_target: totalTarget || 50000000,
      actual_revenue: totalActual || 28500000,
      completion_rate: totalTarget > 0 ? (totalActual / totalTarget) * 100 : 57.0,
      time_progress: timeProgress,
    };
  }, [targets]);

  const [forecast, setForecast] = useState({
    prediction: {
      predicted_revenue: 52800000,
      predicted_completion_rate: 105.6,
      confidence_level: 85,
      risk_level: "LOW",
    },
    funnel_contribution: {
      stage1: { count: 45, total_amount: 18000000, win_rate: 25 },
      stage2: { count: 28, total_amount: 12000000, win_rate: 50 },
      stage3: { count: 15, total_amount: 8000000, win_rate: 65 },
      stage4: { count: 10, total_amount: 5000000, win_rate: 75 },
      stage5: { count: 5, total_amount: 2500000, win_rate: 85 },
    },
  });

  // 计算预测完成率
  const predictedCompletion = useMemo(() => {
    if (targetSummary.quarterly_target === 0) return 0;
    return (forecast.prediction.predicted_revenue / targetSummary.quarterly_target) * 100;
  }, [targetSummary, forecast]);

  // 计算差距
  const gap = targetSummary.quarterly_target - targetSummary.actual_revenue;
  const predictedGap = forecast.prediction.predicted_revenue - targetSummary.quarterly_target;

  const getRiskColor = (level) => {
    switch (level) {
      case "LOW": return "text-green-500 bg-green-500/10";
      case "MEDIUM": return "text-orange-500 bg-orange-500/10";
      case "HIGH": return "text-red-500 bg-red-500/10";
      default: return "text-slate-400";
    }
  };

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
              {formatCurrency(forecast.prediction.predicted_revenue)}
            </div>
            <div className="text-sm text-green-500">
              {predictedCompletion.toFixed(1)}%
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
              置信度 {forecast.prediction.confidence_level}%
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
            {Object.entries(forecast.funnel_contribution).map(([stage, data]) => (
              <div key={stage} className="flex items-center gap-4">
                <div className="w-20 text-sm">
                  {stage === 'stage1' && '初步接触'}
                  {stage === 'stage2' && '需求挖掘'}
                  {stage === 'stage3' && '方案介绍'}
                  {stage === 'stage4' && '价格谈判'}
                  {stage === 'stage5' && '成交促成'}
                </div>
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
    
    // 如果没有数据，使用默认数据
    if (teamMap.size === 0) {
      return [
        { team_name: "华南大区", manager: "王五", target: 18000000, actual: 10800000, completion: 60.0, predicted: 108.3, risk: "LOW", trend: "up", rank: 1 },
        { team_name: "华东大区", manager: "李四", target: 16000000, actual: 9200000, completion: 57.5, predicted: 107.5, risk: "MEDIUM", trend: "stable", rank: 2 },
        { team_name: "华北大区", manager: "赵六", target: 16000000, actual: 8500000, completion: 53.1, predicted: 98.8, risk: "HIGH", trend: "down", rank: 3 },
      ];
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
    
    if (personalTargets.length === 0) {
      return [
        { name: "张三", team: "华南大区", target: 10000000, actual: 6500000, completion: 65.0, predicted: 112.0, pipeline: 8500000, rank: 1 },
        { name: "李四", team: "华东大区", target: 10000000, actual: 5800000, completion: 58.0, predicted: 105.0, pipeline: 7200000, rank: 2 },
        { name: "王五", team: "华南大区", target: 10000000, actual: 5200000, completion: 52.0, predicted: 92.0, pipeline: 6500000, rank: 3 },
        { name: "赵六", team: "华北大区", target: 10000000, actual: 4800000, completion: 48.0, predicted: 88.0, pipeline: 5800000, rank: 4 },
      ];
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
function ExecutiveDashboard({ targets }) {
  // 基于目标计算关键 KPI
  const kpis = useMemo(() => {
    const totalTarget = (targets || []).reduce((sum, t) => sum + Number(t.target_value || 0), 0);
    const totalActual = (targets || []).reduce((sum, t) => sum + Number(t.actual_value || 0), 0);
    const predictedCompletion = totalTarget > 0 ? (totalActual / totalTarget) * 100 * 1.5 : 105.6;
    
    return {
      predicted_completion: Math.min(120, predictedCompletion),
      excess_amount: totalTarget > 0 ? totalActual * 1.5 - totalTarget : 2800000,
    };
  }, [targets]);

  return (
    <div className="space-y-6">
      {/* 核心 KPI */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card className="border-green-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-500">
              <DollarSign className="w-5 h-5" />
              业绩预测
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-500 mb-2">
              {kpis.predicted_completion.toFixed(1)}%
            </div>
            <div className="text-sm text-slate-400">预计完成季度目标</div>
            <div className="flex items-center gap-2 mt-2 text-sm text-green-500">
              <TrendingUp className="w-4 h-4" />
              <span>{kpis.excess_amount >= 0 ? "超额" : "缺口"} {formatCurrency(Math.abs(kpis.excess_amount))}</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-blue-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-500">
              <Users className="w-5 h-5" />
              新客户
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-500 mb-2">106.7%</div>
            <div className="text-sm text-slate-400">预计完成获客目标</div>
            <div className="flex items-center gap-2 mt-2 text-sm text-blue-500">
              <TrendingUp className="w-4 h-4" />
              <span>超额 2 家</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-purple-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-500">
              <Target className="w-5 h-5" />
              平均客单价
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-500 mb-2">¥158 万</div>
            <div className="text-sm text-slate-400">同比提升 5.3%</div>
            <div className="flex items-center gap-2 mt-2 text-sm text-green-500">
              <ArrowUpRight className="w-4 h-4" />
              <span>超目标 8 万</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 红绿灯预警 */}
      <Card>
        <CardHeader>
          <CardTitle>红绿灯预警</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-500/10 rounded border border-green-500">
              <div className="text-2xl font-bold text-green-500 mb-1">华南大区</div>
              <div className="text-sm">预测 108.3% ✅</div>
            </div>
            <div className="text-center p-4 bg-green-500/10 rounded border border-green-500">
              <div className="text-2xl font-bold text-green-500 mb-1">华东大区</div>
              <div className="text-sm">预测 107.5% ✅</div>
            </div>
            <div className="text-center p-4 bg-red-500/10 rounded border border-red-500">
              <div className="text-2xl font-bold text-red-500 mb-1">华北大区</div>
              <div className="text-sm">预测 98.8% ⚠️</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 需要领导关注 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="w-5 h-5" />
            需要您关注的事项
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 bg-red-500/10 rounded">
              <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium">拜访欣旺达高层</div>
                <div className="text-sm text-slate-400">320 万项目处于决策阶段，需要高层推动</div>
                <div className="text-sm text-red-500 mt-1">截止：3 月 10 日</div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-orange-500/10 rounded">
              <AlertTriangle className="w-5 h-5 text-orange-500 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium">审批华北大区特殊折扣政策</div>
                <div className="text-sm text-slate-400">帮助华北大区追赶进度</div>
                <div className="text-sm text-orange-500 mt-1">截止：3 月 5 日</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

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
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
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
            <TabsTrigger value="executive">
              <Eye className="w-4 h-4 mr-2" />
              驾驶舱
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

          <TabsContent value="executive" className="mt-6">
            <ExecutiveDashboard targets={targets} />
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
