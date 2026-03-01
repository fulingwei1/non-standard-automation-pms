import {
  Activity,
  AlertTriangle,
  BarChart3,
  CalendarDays,
  Factory,
  Gauge,
  TrendingUp,
  Wrench,
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
import { cn } from "../lib/utils";

const workCenterCapacityData = [
  {
    id: "WC-A01",
    name: "冲压一线",
    plannedHours: 920,
    availableHours: 880,
    actualHours: 842,
    plannedOutput: 12800,
    actualOutput: 12160,
    utilization: 95.7,
    oee: 88.4,
  },
  {
    id: "WC-B02",
    name: "焊装二线",
    plannedHours: 860,
    availableHours: 825,
    actualHours: 803,
    plannedOutput: 11300,
    actualOutput: 10820,
    utilization: 97.3,
    oee: 84.9,
  },
  {
    id: "WC-C03",
    name: "总装三线",
    plannedHours: 980,
    availableHours: 930,
    actualHours: 852,
    plannedOutput: 14200,
    actualOutput: 13610,
    utilization: 91.6,
    oee: 86.1,
  },
  {
    id: "WC-D04",
    name: "测试工站",
    plannedHours: 740,
    availableHours: 705,
    actualHours: 598,
    plannedOutput: 6800,
    actualOutput: 6315,
    utilization: 84.8,
    oee: 81.7,
  },
];

const utilizationTrendData = [
  { week: "2月W1", utilization: 86.2, attainment: 92.4 },
  { week: "2月W2", utilization: 88.6, attainment: 93.7 },
  { week: "2月W3", utilization: 90.5, attainment: 95.1 },
  { week: "2月W4", utilization: 91.8, attainment: 96.3 },
  { week: "3月W1", utilization: 92.6, attainment: 97.2 },
  { week: "3月W2", utilization: 91.1, attainment: 95.8 },
];

const utilizationLossData = [
  { reason: "换型切换等待", value: 26, detail: "平均每班损失 0.9h" },
  { reason: "关键工位返修", value: 22, detail: "返修率 3.4%" },
  { reason: "设备点检超时", value: 19, detail: "计划外停机 41h/月" },
  { reason: "跨线协同排队", value: 15, detail: "平均排队 37 分钟/批次" },
];

const bottleneckData = [
  {
    item: "焊装二线机器人 R-17",
    type: "设备瓶颈",
    severity: "high",
    utilization: 98.1,
    queueHours: 21.4,
    outputImpact: 12.8,
    reason: "焊接夹具更换频繁，节拍波动明显",
    suggestion: "引入快速换型夹具，并将预热工序前移至备料段",
  },
  {
    item: "总装三线末端工位",
    type: "工位瓶颈",
    severity: "medium",
    utilization: 93.4,
    queueHours: 14.9,
    outputImpact: 8.6,
    reason: "末端复检资源不足，峰值时段排队累积",
    suggestion: "增加 1 个复检工位并采用分时批次放行",
  },
  {
    item: "测试工站夜班组",
    type: "人员瓶颈",
    severity: "medium",
    utilization: 89.7,
    queueHours: 10.6,
    outputImpact: 6.9,
    reason: "关键技能覆盖不足，异常处理依赖资深人员",
    suggestion: "安排双周技能轮训，补齐夜班故障诊断能力",
  },
];

const forecastData = [
  {
    period: "3月第3周",
    demand: 12700,
    forecast: 12380,
    optimistic: 12950,
    conservative: 11920,
    confidence: 91,
  },
  {
    period: "3月第4周",
    demand: 13150,
    forecast: 12620,
    optimistic: 13210,
    conservative: 12110,
    confidence: 89,
  },
  {
    period: "4月第1周",
    demand: 13600,
    forecast: 12980,
    optimistic: 13680,
    conservative: 12430,
    confidence: 87,
  },
  {
    period: "4月第2周",
    demand: 13950,
    forecast: 13220,
    optimistic: 13990,
    conservative: 12690,
    confidence: 86,
  },
];

function formatPercent(value) {
  return `${value.toFixed(1)}%`;
}

function formatHours(value) {
  return `${value.toLocaleString()}h`;
}

function formatUnits(value) {
  return `${value.toLocaleString()} 件`;
}

function getUtilizationMeta(value) {
  if (value >= 95) {
    return {
      label: "高负载",
      badgeClass: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
      progressColor: "danger",
    };
  }
  if (value >= 88) {
    return {
      label: "平衡",
      badgeClass: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
      progressColor: "warning",
    };
  }
  return {
    label: "可提升",
    badgeClass: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
    progressColor: "success",
  };
}

function getSeverityMeta(level) {
  const config = {
    high: {
      label: "高风险",
      className: "bg-rose-500/20 text-rose-300 border border-rose-500/40",
    },
    medium: {
      label: "中风险",
      className: "bg-amber-500/20 text-amber-300 border border-amber-500/40",
    },
    low: {
      label: "低风险",
      className: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40",
    },
  };

  return config[level] || config.low;
}

export default function CapacityAnalysis() {
  const totalPlannedHours = workCenterCapacityData.reduce(
    (sum, item) => sum + item.plannedHours,
    0,
  );
  const totalAvailableHours = workCenterCapacityData.reduce(
    (sum, item) => sum + item.availableHours,
    0,
  );
  const totalActualHours = workCenterCapacityData.reduce(
    (sum, item) => sum + item.actualHours,
    0,
  );
  const totalPlannedOutput = workCenterCapacityData.reduce(
    (sum, item) => sum + item.plannedOutput,
    0,
  );
  const totalActualOutput = workCenterCapacityData.reduce(
    (sum, item) => sum + item.actualOutput,
    0,
  );
  const averageUtilization = totalActualHours / totalAvailableHours * 100;
  const averageOee =
    workCenterCapacityData.reduce((sum, item) => sum + item.oee, 0) /
    workCenterCapacityData.length;
  const bottleneckCount = bottleneckData.filter(
    (item) => item.severity === "high" || item.severity === "medium",
  ).length;
  const forecastGap = forecastData.reduce(
    (sum, item) => sum + Math.max(item.demand - item.forecast, 0),
    0,
  );
  const maxTrendValue = Math.max(
    ...utilizationTrendData.map((item) => Math.max(item.utilization, item.attainment)),
  );
  const maxForecastValue = Math.max(
    ...forecastData.map((item) => Math.max(item.demand, item.optimistic)),
  );

  const overviewCards = [
    {
      title: "平均产能利用率",
      value: formatPercent(averageUtilization),
      hint: `${formatHours(totalActualHours)} / ${formatHours(totalAvailableHours)}`,
      trend: "较上月 +1.8%",
      icon: Gauge,
    },
    {
      title: "工作中心达成率",
      value: formatPercent((totalActualOutput / totalPlannedOutput) * 100),
      hint: `${formatUnits(totalActualOutput)} 实际完成`,
      trend: "计划达成稳定",
      icon: Factory,
    },
    {
      title: "已识别瓶颈",
      value: `${bottleneckCount} 个`,
      hint: "覆盖设备 / 工位 / 人员",
      trend: "高风险 1 个",
      icon: AlertTriangle,
    },
    {
      title: "未来四周缺口",
      value: formatUnits(forecastGap),
      hint: "需求与预测产能差值",
      trend: "建议预留加班产能",
      icon: TrendingUp,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="产能分析"
        description="聚焦工作中心产能统计、利用率波动、瓶颈定位与未来产能预测。"
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {overviewCards.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title} className="border-slate-800/70">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-sm text-slate-300">
                  <span>{item.title}</span>
                  <Icon className="h-4 w-4 text-slate-400" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold text-white">{item.value}</p>
                <p className="mt-1 text-xs text-slate-400">{item.hint}</p>
                <Badge className="mt-3 bg-slate-800 text-slate-200">{item.trend}</Badge>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <BarChart3 className="h-4 w-4 text-cyan-400" />
            工作中心产能统计
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>工作中心</TableHead>
                <TableHead>计划工时</TableHead>
                <TableHead>可用工时</TableHead>
                <TableHead>实际投入</TableHead>
                <TableHead>利用率</TableHead>
                <TableHead>OEE</TableHead>
                <TableHead>产能达成</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {workCenterCapacityData.map((item) => {
                const meta = getUtilizationMeta(item.utilization);
                const outputRate = item.actualOutput / item.plannedOutput * 100;
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium text-slate-200">
                      {item.name}
                    </TableCell>
                    <TableCell>{formatHours(item.plannedHours)}</TableCell>
                    <TableCell>{formatHours(item.availableHours)}</TableCell>
                    <TableCell>{formatHours(item.actualHours)}</TableCell>
                    <TableCell className="min-w-48">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-300">{formatPercent(item.utilization)}</span>
                          <Badge className={meta.badgeClass}>{meta.label}</Badge>
                        </div>
                        <Progress value={item.utilization} color={meta.progressColor} />
                      </div>
                    </TableCell>
                    <TableCell>{formatPercent(item.oee)}</TableCell>
                    <TableCell>
                      <Badge className="bg-blue-500/15 text-blue-300 border border-blue-500/30">
                        {formatPercent(outputRate)}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>

          <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 text-sm text-slate-300">
            汇总：本周期计划工时 {formatHours(totalPlannedHours)}，可用工时{" "}
            {formatHours(totalAvailableHours)}，实际投入 {formatHours(totalActualHours)}，平均
            OEE {formatPercent(averageOee)}。
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <Activity className="h-4 w-4 text-emerald-400" />
            利用率分析
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-4 rounded-lg border border-slate-800/80 p-4">
              <h3 className="text-sm font-medium text-slate-200">工作中心负荷分布</h3>
              {workCenterCapacityData.map((item) => {
                const utilizationDelta = item.utilization - averageUtilization;
                const toneClass =
                  utilizationDelta >= 2
                    ? "text-rose-300"
                    : utilizationDelta <= -2
                      ? "text-emerald-300"
                      : "text-slate-300";
                return (
                  <div key={`${item.id}-distribution`} className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{item.name}</span>
                      <span className={toneClass}>
                        {utilizationDelta >= 0 ? "+" : ""}
                        {utilizationDelta.toFixed(1)}%
                      </span>
                    </div>
                    <Progress
                      value={item.utilization}
                      color={getUtilizationMeta(item.utilization).progressColor}
                    />
                  </div>
                );
              })}
            </div>

            <div className="space-y-4 rounded-lg border border-slate-800/80 p-4">
              <h3 className="text-sm font-medium text-slate-200">近 6 周利用率趋势</h3>
              <div className="grid h-44 grid-cols-6 items-end gap-3">
                {utilizationTrendData.map((item) => (
                  <div key={item.week} className="flex flex-col items-center gap-2">
                    <div className="flex h-32 w-full items-end gap-1 rounded-md bg-slate-900/60 p-1">
                      <div
                        className="w-1/2 rounded-sm bg-gradient-to-t from-blue-500/40 to-blue-300/90"
                        style={{ height: `${(item.utilization / maxTrendValue) * 100}%` }}
                        title={`利用率 ${formatPercent(item.utilization)}`}
                      />
                      <div
                        className="w-1/2 rounded-sm bg-gradient-to-t from-cyan-500/40 to-cyan-300/90"
                        style={{ height: `${(item.attainment / maxTrendValue) * 100}%` }}
                        title={`达成率 ${formatPercent(item.attainment)}`}
                      />
                    </div>
                    <span className="text-[11px] text-slate-400">{item.week}</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-blue-300" />
                  利用率
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-cyan-300" />
                  达成率
                </span>
              </div>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {utilizationLossData.map((item) => (
              <div
                key={item.reason}
                className="rounded-lg border border-slate-800/80 bg-slate-950/30 p-4"
              >
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="text-slate-200">{item.reason}</span>
                  <Badge className="bg-slate-800 text-slate-200">{item.value}%</Badge>
                </div>
                <Progress value={item.value} color="warning" />
                <p className="mt-2 text-xs text-slate-400">{item.detail}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            瓶颈识别
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {bottleneckData.map((item) => {
              const severity = getSeverityMeta(item.severity);
              return (
                <div
                  key={item.item}
                  className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4"
                >
                  <div className="mb-3 flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-slate-200">{item.item}</p>
                      <p className="text-xs text-slate-400">{item.type}</p>
                    </div>
                    <Badge className={severity.className}>{severity.label}</Badge>
                  </div>

                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex items-center justify-between">
                      <span>利用率</span>
                      <span>{formatPercent(item.utilization)}</span>
                    </div>
                    <Progress value={item.utilization} color="danger" />
                    <div className="flex items-center justify-between">
                      <span>累计排队时长</span>
                      <span>{item.queueHours.toFixed(1)}h</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>产出影响</span>
                      <span className="text-rose-300">{formatPercent(item.outputImpact)}</span>
                    </div>
                  </div>

                  <div className="mt-3 rounded-md border border-slate-800/80 bg-slate-900/60 p-3 text-xs text-slate-300">
                    <p className="font-medium text-slate-200">成因</p>
                    <p className="mt-1">{item.reason}</p>
                  </div>
                  <div className="mt-3 rounded-md border border-cyan-700/30 bg-cyan-950/20 p-3 text-xs text-cyan-100">
                    <p className="font-medium">建议措施</p>
                    <p className="mt-1">{item.suggestion}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800/70">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base text-white">
            <CalendarDays className="h-4 w-4 text-violet-400" />
            产能预测
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 xl:grid-cols-5">
            <div className="space-y-3 rounded-lg border border-slate-800/80 p-4 xl:col-span-3">
              <h3 className="text-sm font-medium text-slate-200">未来 4 周需求 vs 预测产能</h3>
              {forecastData.map((item) => {
                const demandWidth = item.demand / maxForecastValue * 100;
                const forecastWidth = item.forecast / maxForecastValue * 100;
                const gap = item.forecast - item.demand;
                return (
                  <div key={item.period} className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-300">{item.period}</span>
                      <span
                        className={cn(
                          "font-medium",
                          gap >= 0 ? "text-emerald-300" : "text-rose-300",
                        )}
                      >
                        {gap >= 0 ? "+" : ""}
                        {formatUnits(gap)}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <div className="h-2 w-full rounded-full bg-slate-900/80">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-slate-500/60 to-slate-300/80"
                          style={{ width: `${demandWidth}%` }}
                        />
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-900/80">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-violet-500/60 to-violet-300/90"
                          style={{ width: `${forecastWidth}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-slate-300" />
                  需求
                </span>
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-violet-300" />
                  预测产能
                </span>
              </div>
            </div>

            <div className="space-y-4 rounded-lg border border-slate-800/80 p-4 xl:col-span-2">
              <h3 className="text-sm font-medium text-slate-200">预测可靠性与行动建议</h3>
              <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-3">
                <p className="text-xs text-slate-400">平均置信度</p>
                <p className="mt-1 text-lg font-semibold text-white">
                  {formatPercent(
                    forecastData.reduce((sum, item) => sum + item.confidence, 0) /
                      forecastData.length,
                  )}
                </p>
              </div>
              <div className="rounded-md border border-violet-700/30 bg-violet-950/20 p-3 text-xs text-slate-300">
                <div className="mb-1 flex items-center gap-2 text-violet-200">
                  <Wrench className="h-3.5 w-3.5" />
                  产能补偿策略
                </div>
                <p>
                  对焊装二线安排周末 1 个加班班次，并将测试工站夜班补入 2 名多技能人员，
                  预计可补充约 1,040 件周产能。
                </p>
              </div>
              <div className="rounded-md border border-emerald-700/30 bg-emerald-950/20 p-3 text-xs text-slate-300">
                <div className="mb-1 flex items-center gap-2 text-emerald-200">
                  <TrendingUp className="h-3.5 w-3.5" />
                  趋势判断
                </div>
                <p>
                  需求增长斜率高于产能提升斜率，若不进行资源重排，4 月上旬缺口将扩大至
                  700+ 件/周。
                </p>
              </div>
            </div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>预测周期</TableHead>
                <TableHead>需求</TableHead>
                <TableHead>基准预测</TableHead>
                <TableHead>乐观场景</TableHead>
                <TableHead>保守场景</TableHead>
                <TableHead>置信度</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {forecastData.map((item) => (
                <TableRow key={item.period}>
                  <TableCell className="font-medium text-slate-200">{item.period}</TableCell>
                  <TableCell>{formatUnits(item.demand)}</TableCell>
                  <TableCell>{formatUnits(item.forecast)}</TableCell>
                  <TableCell>{formatUnits(item.optimistic)}</TableCell>
                  <TableCell>{formatUnits(item.conservative)}</TableCell>
                  <TableCell>
                    <Badge
                      className={cn(
                        "border",
                        item.confidence >= 90
                          ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                          : "bg-amber-500/15 text-amber-300 border-amber-500/30",
                      )}
                    >
                      {formatPercent(item.confidence)}
                    </Badge>
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
