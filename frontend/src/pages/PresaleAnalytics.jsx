import {
  BarChart3,
  Briefcase,
  Clock3,
  Gauge,
  LineChart,
  Target,
  TrendingUp,
  UserRound,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui";

const conversionFunnelData = [
  { stage: "线索 -> 技术澄清", count: 148, conversionRate: 78.2 },
  { stage: "技术澄清 -> 方案提交", count: 112, conversionRate: 75.7 },
  { stage: "方案提交 -> 报价完成", count: 87, conversionRate: 77.6 },
  { stage: "报价完成 -> 商务谈判", count: 61, conversionRate: 70.1 },
  { stage: "商务谈判 -> 成交", count: 34, conversionRate: 55.7 },
];

const conversionTrendData = [
  { month: "9月", conversionRate: 19.3 },
  { month: "10月", conversionRate: 21.8 },
  { month: "11月", conversionRate: 23.4 },
  { month: "12月", conversionRate: 22.7 },
  { month: "1月", conversionRate: 24.6 },
  { month: "2月", conversionRate: 26.1 },
];

const winRateSegmentData = [
  {
    segment: "新能源装备",
    opportunities: 18,
    wins: 12,
    winRate: 66.7,
    cycleDays: 34,
  },
  {
    segment: "流程制造升级",
    opportunities: 23,
    wins: 13,
    winRate: 56.5,
    cycleDays: 42,
  },
  {
    segment: "智能仓储",
    opportunities: 15,
    wins: 8,
    winRate: 53.3,
    cycleDays: 39,
  },
  {
    segment: "海外改造项目",
    opportunities: 10,
    wins: 4,
    winRate: 40.0,
    cycleDays: 51,
  },
];

const resourceAnalysisData = [
  {
    type: "售前工程师工时",
    used: 1320,
    capacity: 1600,
    utilization: 82.5,
    gap: 280,
  },
  {
    type: "标准方案复用",
    used: 248,
    capacity: 320,
    utilization: 77.5,
    gap: 72,
  },
  {
    type: "PoC测试资源",
    used: 96,
    capacity: 140,
    utilization: 68.6,
    gap: 44,
  },
  {
    type: "技术评审席位",
    used: 106,
    capacity: 120,
    utilization: 88.3,
    gap: 14,
  },
];

const resourceWasteData = [
  { item: "重复方案编写", wasteRate: 31, impact: "月均浪费 124 工时" },
  { item: "跨部门等待", wasteRate: 26, impact: "平均延误 2.8 天" },
  { item: "需求反复确认", wasteRate: 22, impact: "返工率 17%" },
  { item: "样机测试排队", wasteRate: 18, impact: "赢单率下降 3.2%" },
];

const salesEfficiencyData = [
  {
    owner: "李铭",
    opportunities: 16,
    supportHours: 188,
    avgResponseHour: 2.1,
    winRate: 68.8,
    perCapitaOutput: 392,
  },
  {
    owner: "王璇",
    opportunities: 19,
    supportHours: 226,
    avgResponseHour: 2.9,
    winRate: 57.9,
    perCapitaOutput: 365,
  },
  {
    owner: "赵晨",
    opportunities: 14,
    supportHours: 170,
    avgResponseHour: 2.6,
    winRate: 64.3,
    perCapitaOutput: 338,
  },
  {
    owner: "周宁",
    opportunities: 17,
    supportHours: 240,
    avgResponseHour: 3.5,
    winRate: 47.1,
    perCapitaOutput: 294,
  },
];

function formatPercent(value) {
  return `${value.toFixed(1)}%`;
}

function formatAmountInWan(value) {
  return `${value.toFixed(0)}万`;
}

function getProgressColor(value, high = 75, medium = 60) {
  if (value >= high) {
    return "success";
  }
  if (value >= medium) {
    return "warning";
  }
  return "danger";
}

export default function PresaleAnalytics() {
  const totalFunnelCount = conversionFunnelData.reduce(
    (sum, item) => sum + item.count,
    0,
  );
  const overallConversionRate =
    conversionFunnelData[conversionFunnelData.length - 1].count /
    conversionFunnelData[0].count *
    100;
  const overallWinRate =
    winRateSegmentData.reduce((sum, item) => sum + item.wins, 0) /
    winRateSegmentData.reduce((sum, item) => sum + item.opportunities, 0) *
    100;
  const averageUtilization =
    resourceAnalysisData.reduce((sum, item) => sum + item.utilization, 0) /
    resourceAnalysisData.length;
  const averageResponseTime =
    salesEfficiencyData.reduce((sum, item) => sum + item.avgResponseHour, 0) /
    salesEfficiencyData.length;
  const averagePerCapitaOutput =
    salesEfficiencyData.reduce((sum, item) => sum + item.perCapitaOutput, 0) /
    salesEfficiencyData.length;
  const maxTrendValue = Math.max(
    ...conversionTrendData.map((item) => item.conversionRate),
  );

  const overviewCards = [
    {
      title: "整体转化率",
      value: formatPercent(overallConversionRate),
      hint: "线索到赢单端到端转化",
      icon: Target,
      trend: "+2.6% 环比",
    },
    {
      title: "整体赢单率",
      value: formatPercent(overallWinRate),
      hint: "重点行业商机赢单情况",
      icon: TrendingUp,
      trend: "+4.2% 环比",
    },
    {
      title: "资源利用率",
      value: formatPercent(averageUtilization),
      hint: "工时、方案、PoC、评审席位",
      icon: Gauge,
      trend: "高负载项 1 个",
    },
    {
      title: "人均产出",
      value: formatAmountInWan(averagePerCapitaOutput),
      hint: "销售支持人均成交贡献",
      icon: UserRound,
      trend: `${averageResponseTime.toFixed(1)}h 平均响应`,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="销售漏斗分析"
        description="围绕转化率、赢单率、资源配置和销售人效，定位售前支持提效机会。"
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {overviewCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.title} className="border-slate-800/70">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-sm text-slate-300">
                  <span>{card.title}</span>
                  <Icon className="h-4 w-4 text-slate-400" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold text-white">{card.value}</div>
                <p className="mt-1 text-xs text-slate-400">{card.hint}</p>
                <Badge className="mt-3 bg-slate-800 text-slate-200">{card.trend}</Badge>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <LineChart className="h-4 w-4 text-cyan-400" />
            转化率分析
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-4 rounded-lg border border-slate-800/80 p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-200">售前漏斗转化效率</h3>
                <span className="text-xs text-slate-400">
                  总跟进量 {totalFunnelCount} 条
                </span>
              </div>
              {conversionFunnelData.map((item) => (
                <div key={item.stage} className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300">{item.stage}</span>
                    <span className="text-slate-400">
                      {item.count} 条 / {formatPercent(item.conversionRate)}
                    </span>
                  </div>
                  <Progress
                    value={item.conversionRate}
                    color={getProgressColor(item.conversionRate)}
                  />
                </div>
              ))}
            </div>

            <div className="rounded-lg border border-slate-800/80 p-4">
              <h3 className="mb-4 text-sm font-medium text-slate-200">近 6 个月转化率趋势</h3>
              <div className="grid h-40 grid-cols-6 items-end gap-3">
                {conversionTrendData.map((item) => (
                  <div key={item.month} className="flex flex-col items-center gap-2">
                    <div className="flex h-28 w-full items-end rounded-md bg-slate-900/60 p-1">
                      <div
                        className="w-full rounded-sm bg-gradient-to-t from-cyan-500/50 to-blue-400/80"
                        style={{
                          height: `${(item.conversionRate / maxTrendValue) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-slate-400">{item.month}</span>
                    <span className="text-xs font-medium text-cyan-300">
                      {formatPercent(item.conversionRate)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <Target className="h-4 w-4 text-emerald-400" />
            赢单率分析
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>业务细分</TableHead>
                <TableHead>商机数</TableHead>
                <TableHead>赢单数</TableHead>
                <TableHead>赢单率</TableHead>
                <TableHead>平均成交周期</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {winRateSegmentData.map((item) => (
                <TableRow key={item.segment}>
                  <TableCell className="font-medium text-slate-200">{item.segment}</TableCell>
                  <TableCell>{item.opportunities}</TableCell>
                  <TableCell>{item.wins}</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        item.winRate >= 60
                          ? "bg-emerald-500/20 text-emerald-300"
                          : item.winRate >= 50
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-rose-500/20 text-rose-300"
                      }
                    >
                      {formatPercent(item.winRate)}
                    </Badge>
                  </TableCell>
                  <TableCell>{item.cycleDays} 天</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-emerald-700/30 bg-emerald-950/20 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-emerald-300">
                <Briefcase className="h-4 w-4" />
                赢单驱动因素
              </div>
              <ul className="space-y-2 text-sm text-slate-300">
                <li>标准化方案复用率提升至 77%，响应速度提升 1.4 天。</li>
                <li>技术澄清阶段提前介入，关键人覆盖率由 63% 提升至 79%。</li>
                <li>报价前进行竞品策略评估的项目，赢单率高出平均值 9.1%。</li>
              </ul>
            </div>
            <div className="rounded-lg border border-amber-700/30 bg-amber-950/20 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-amber-300">
                <Clock3 className="h-4 w-4" />
                主要风险点
              </div>
              <ul className="space-y-2 text-sm text-slate-300">
                <li>海外改造项目方案确认周期偏长，拖慢整体赢单节奏。</li>
                <li>跨部门成本核算反馈不稳定，导致报价窗口错失风险上升。</li>
                <li>高定制项目的需求变更频次偏高，返工影响商务推进。</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <BarChart3 className="h-4 w-4 text-violet-400" />
            资源分析
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-4 rounded-lg border border-slate-800/80 p-4">
            <h3 className="text-sm font-medium text-slate-200">资源利用概览</h3>
            {resourceAnalysisData.map((item) => (
              <div key={item.type} className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">{item.type}</span>
                  <span className="text-slate-400">
                    {item.used}/{item.capacity}，缺口 {item.gap}
                  </span>
                </div>
                <Progress
                  value={item.utilization}
                  color={getProgressColor(item.utilization, 80, 65)}
                />
              </div>
            ))}
          </div>

          <div className="space-y-4 rounded-lg border border-slate-800/80 p-4">
            <h3 className="text-sm font-medium text-slate-200">资源浪费分析</h3>
            {resourceWasteData.map((item) => (
              <div key={item.item} className="rounded-md border border-slate-800/80 p-3">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-slate-200">{item.item}</span>
                  <Badge className="bg-rose-500/15 text-rose-300">
                    浪费率 {item.wasteRate}%
                  </Badge>
                </div>
                <Progress value={item.wasteRate} color="danger" />
                <p className="mt-2 text-xs text-slate-400">{item.impact}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <Gauge className="h-4 w-4 text-orange-400" />
            销售人效分析
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>销售负责人</TableHead>
                <TableHead>支持商机数</TableHead>
                <TableHead>售前工时</TableHead>
                <TableHead>平均响应时长</TableHead>
                <TableHead>赢单率</TableHead>
                <TableHead>人均产出</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {salesEfficiencyData.map((item) => (
                <TableRow key={item.owner}>
                  <TableCell className="font-medium text-slate-200">{item.owner}</TableCell>
                  <TableCell>{item.opportunities}</TableCell>
                  <TableCell>{item.supportHours}h</TableCell>
                  <TableCell>{item.avgResponseHour.toFixed(1)}h</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        item.winRate >= 60
                          ? "bg-emerald-500/20 text-emerald-300"
                          : item.winRate >= 50
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-rose-500/20 text-rose-300"
                      }
                    >
                      {formatPercent(item.winRate)}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatAmountInWan(item.perCapitaOutput)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="rounded-lg border border-blue-800/40 bg-blue-950/20 p-4 text-sm text-slate-300">
            建议：针对响应时长超过 3 小时且赢单率低于 50% 的项目，优先引入标准方案模板
            与关键问题清单，缩短售前协同等待时间并降低返工率。
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
