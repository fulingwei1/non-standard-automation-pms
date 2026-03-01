/**
 * 销售预测仪表盘 - 领导驾驶舱
 * 
 * 功能：
 * 1. 公司整体预测
 * 2. 团队分解
 * 3. 个人分解
 * 4. 预测准确性
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Target,
  DollarSign,
  Users,
  Award,
  AlertTriangle,
  CheckCircle,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  BarChart3,
  Eye,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
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

// 公司整体预测
function CompanyOverview() {
  const [forecast, _setForecast] = useState({
    targets: {
      quarterly_target: 50000000,
      actual_revenue: 28500000,
      completion_rate: 57.0,
      time_progress: 66.7,
    },
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
      {/* 核心指标 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">季度目标</div>
            <div className="text-2xl font-bold">¥{(forecast.targets.quarterly_target / 1000000).toFixed(0)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">已完成</div>
            <div className="text-2xl font-bold text-blue-500">¥{(forecast.targets.actual_revenue / 1000000).toFixed(1)}M</div>
            <div className="text-sm text-slate-400">{forecast.targets.completion_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">AI 预测</div>
            <div className="text-2xl font-bold text-green-500">¥{(forecast.prediction.predicted_revenue / 1000000).toFixed(1)}M</div>
            <div className="text-sm text-green-500">{forecast.prediction.predicted_completion_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">风险等级</div>
            <div className={`text-2xl font-bold ${getRiskColor(forecast.prediction.risk_level).split(' ')[0]}`}>
              {forecast.prediction.risk_level === "LOW" ? "低" : forecast.prediction.risk_level === "MEDIUM" ? "中" : "高"}
            </div>
            <div className="text-sm text-slate-400">置信度 {forecast.prediction.confidence_level}%</div>
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
                <span className="text-sm">{forecast.targets.time_progress}%</span>
              </div>
              <Progress value={forecast.targets.time_progress} className="h-3" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">业绩进度</span>
                <span className={`text-sm font-bold ${forecast.targets.completion_rate < forecast.targets.time_progress ? 'text-orange-500' : 'text-green-500'}`}>
                  {forecast.targets.completion_rate}%
                </span>
              </div>
              <Progress value={forecast.targets.completion_rate} className="h-3" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">预测进度</span>
                <span className="text-sm font-bold text-green-500">{forecast.prediction.predicted_completion_rate}%</span>
              </div>
              <Progress value={Math.min(100, forecast.prediction.predicted_completion_rate)} className="h-3" />
            </div>
          </div>

          {forecast.targets.completion_rate < forecast.targets.time_progress && (
            <Alert className="mt-4 border-orange-500 bg-orange-500/10">
              <AlertTriangle className="h-4 w-4 text-orange-500" />
              <div className="text-sm">
                <strong>注意：</strong>当前业绩进度落后时间进度{(forecast.targets.time_progress - forecast.targets.completion_rate).toFixed(1)}%
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
                    <span className="text-sm text-slate-400">{data.count}个商机 · ¥{(data.total_amount / 1000000).toFixed(1)}M</span>
                    <span className="text-sm">赢单率{data.win_rate}%</span>
                  </div>
                  <Progress value={data.win_rate} className="h-2" />
                </div>
                <div className="w-24 text-right text-sm font-medium">
                  ¥{((data.total_amount * data.win_rate / 100) / 1000000).toFixed(2)}M
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
function TeamBreakdown() {
  const [teams, _setTeams] = useState([
    { team_name: "华南大区", manager: "王五", target: 18000000, actual: 10800000, completion: 60.0, predicted: 108.3, risk: "LOW", trend: "up", rank: 1 },
    { team_name: "华东大区", manager: "李四", target: 16000000, actual: 9200000, completion: 57.5, predicted: 107.5, risk: "MEDIUM", trend: "stable", rank: 2 },
    { team_name: "华北大区", manager: "赵六", target: 16000000, actual: 8500000, completion: 53.1, predicted: 98.8, risk: "HIGH", trend: "down", rank: 3 },
  ]);

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
                  <TableCell className="text-right">¥{(team.target / 1000000).toFixed(1)}M</TableCell>
                  <TableCell className="text-right">¥{(team.actual / 1000000).toFixed(1)}M</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={team.completion >= 60 ? "default" : "secondary"}>
                      {team.completion}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={team.predicted >= 100 ? "text-green-500 font-bold" : "text-orange-500"}>
                      {team.predicted}%
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
function SalesRepBreakdown() {
  const [reps, _setReps] = useState([
    { name: "张三", team: "华南大区", target: 10000000, actual: 6500000, completion: 65.0, predicted: 112.0, pipeline: 8500000, rank: 1 },
    { name: "李四", team: "华东大区", target: 10000000, actual: 5800000, completion: 58.0, predicted: 105.0, pipeline: 7200000, rank: 2 },
    { name: "王五", team: "华南大区", target: 10000000, actual: 5200000, completion: 52.0, predicted: 92.0, pipeline: 6500000, rank: 3 },
    { name: "赵六", team: "华北大区", target: 10000000, actual: 4800000, completion: 48.0, predicted: 88.0, pipeline: 5800000, rank: 4 },
  ]);

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
                  <TableCell className="text-right">¥{(rep.target / 1000000).toFixed(1)}M</TableCell>
                  <TableCell className="text-right">¥{(rep.actual / 1000000).toFixed(1)}M</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={rep.completion >= 60 ? "default" : "secondary"}>
                      {rep.completion}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className={rep.predicted >= 100 ? "text-green-500 font-bold" : "text-orange-500"}>
                      {rep.predicted}%
                    </span>
                  </TableCell>
                  <TableCell className="text-right text-slate-400">
                    ¥{(rep.pipeline / 1000000).toFixed(1)}M
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
function ExecutiveDashboard() {
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
            <div className="text-3xl font-bold text-green-500 mb-2">105.6%</div>
            <div className="text-sm text-slate-400">预计完成季度目标</div>
            <div className="flex items-center gap-2 mt-2 text-sm text-green-500">
              <TrendingUp className="w-4 h-4" />
              <span>超额 280 万</span>
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
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="销售预测仪表盘"
          description="AI 驱动的公司整体销售计划完成情况预测"
          icon={<BarChart3 className="w-6 h-6 text-indigo-500" />}
          actions={
            <div className="flex gap-2">
              <Button variant="outline">
                <Target className="w-4 h-4 mr-2" />
                调整目标
              </Button>
              <Button>
                <Eye className="w-4 h-4 mr-2" />
                领导驾驶舱
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
            <CompanyOverview />
          </TabsContent>

          <TabsContent value="team" className="mt-6">
            <TeamBreakdown />
          </TabsContent>

          <TabsContent value="individual" className="mt-6">
            <SalesRepBreakdown />
          </TabsContent>

          <TabsContent value="executive" className="mt-6">
            <ExecutiveDashboard />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
