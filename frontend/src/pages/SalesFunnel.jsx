/**
 * 销售漏斗页
 *
 * 统一使用 funnelApi 获取漏斗统计、转化率、瓶颈和预测准确性，
 * 不再直接消费旧的 salesStatisticsApi / funnelOptimizationApi。
 */

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  RefreshCw,
  Workflow,
} from "lucide-react";


import { funnelApi } from "../services/api";

const HEALTH_LEVEL_META = {
  EXCELLENT: {
    label: "优秀",
    className: "bg-emerald-500",
  },
  GOOD: {
    label: "良好",
    className: "bg-blue-500",
  },
  FAIR: {
    label: "一般",
    className: "bg-amber-500",
  },
  POOR: {
    label: "偏弱",
    className: "bg-red-500",
  },
};

const OPPORTUNITY_STAGE_LABELS = {
  DISCOVERY: "初步接触",
  QUALIFICATION: "需求挖掘",
  PROPOSAL: "方案介绍",
  NEGOTIATION: "价格谈判",
  CLOSING: "成交促成",
  WON: "赢单",
  LOST: "输单",
};

function unwrapResponse(response) {
  return response?.formatted ?? response?.data?.data ?? response?.data ?? null;
}

function formatCurrency(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("zh-CN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount);
}

function formatPercent(value, fractionDigits = 1) {
  const numericValue = Number(value || 0);
  return `${numericValue.toFixed(fractionDigits)}%`;
}

function formatStageLabel(stage) {
  return OPPORTUNITY_STAGE_LABELS[stage] || stage || "未命名阶段";
}

function getTrendIcon(trend) {
  if (trend === "up") {
    return <TrendingUp className="h-4 w-4 text-emerald-400" />;
  }
  if (trend === "down") {
    return <TrendingDown className="h-4 w-4 text-red-400" />;
  }
  return <Activity className="h-4 w-4 text-slate-400" />;
}

function getHealthMeta(level) {
  return HEALTH_LEVEL_META[level] || {
    label: level || "未评级",
    className: "bg-slate-500",
  };
}

function buildDateRange(rangeKey) {
  const now = new Date();

  if (rangeKey === "month") {
    return {
      start_date: new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0],
      end_date: new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split("T")[0],
    };
  }

  if (rangeKey === "year") {
    return {
      start_date: new Date(now.getFullYear(), 0, 1).toISOString().split("T")[0],
      end_date: new Date(now.getFullYear(), 11, 31).toISOString().split("T")[0],
    };
  }

  const quarter = Math.floor(now.getMonth() / 3);
  return {
    start_date: new Date(now.getFullYear(), quarter * 3, 1).toISOString().split("T")[0],
    end_date: new Date(now.getFullYear(), quarter * 3 + 3, 0).toISOString().split("T")[0],
  };
}

function buildOverviewStages(summary) {
  const leads = Number(summary?.leads || 0);
  const opportunities = Number(summary?.opportunities || 0);
  const quotes = Number(summary?.quotes || 0);
  const contracts = Number(summary?.contracts || 0);

  return [
    {
      key: "leads",
      label: "线索",
      count: leads,
      amount: 0,
      conversion: 100,
      route: "/sales/leads",
      color: "bg-slate-500",
    },
    {
      key: "opportunities",
      label: "商机",
      count: opportunities,
      amount: Number(summary?.total_opportunity_amount || 0),
      conversion:
        summary?.conversion_rates?.lead_to_opp ??
        (leads > 0 ? Number(((opportunities / leads) * 100).toFixed(1)) : 0),
      route: "/sales/opportunities",
      color: "bg-blue-500",
    },
    {
      key: "quotes",
      label: "报价",
      count: quotes,
      amount: 0,
      conversion:
        summary?.conversion_rates?.opp_to_quote ??
        (opportunities > 0 ? Number(((quotes / opportunities) * 100).toFixed(1)) : 0),
      route: "/sales/quotes",
      color: "bg-amber-500",
    },
    {
      key: "contracts",
      label: "合同",
      count: contracts,
      amount: Number(summary?.total_contract_amount || 0),
      conversion:
        summary?.conversion_rates?.quote_to_contract ??
        (quotes > 0 ? Number(((contracts / quotes) * 100).toFixed(1)) : 0),
      route: "/sales/contracts",
      color: "bg-violet-500",
    },
  ];
}

export default function SalesFunnel() {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState("quarter");
  const [threshold, setThreshold] = useState("55");
  const [accuracyMonths, setAccuracyMonths] = useState("3");
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    summary: null,
    health: null,
    conversion: null,
    bottlenecks: null,
    prediction: null,
    failures: [],
  });
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const loadDashboard = async () => {
      setLoading(true);

      const rangeParams = buildDateRange(timeRange);
      const tasks = {
        summary: funnelApi.getSummary(rangeParams),
        health: funnelApi.getHealthDashboard(),
        conversion: funnelApi.getConversionRates(rangeParams),
        bottlenecks: funnelApi.getBottlenecks({
          threshold: Number(threshold),
        }),
        prediction: funnelApi.getPredictionAccuracy({
          months: Number(accuracyMonths),
        }),
      };

      const entries = Object.entries(tasks);
      const settled = await Promise.allSettled(entries.map(([, task]) => task));

      if (cancelled) {
        return;
      }

      const nextState = {
        summary: null,
        health: null,
        conversion: null,
        bottlenecks: null,
        prediction: null,
        failures: [],
      };

      settled.forEach((result, index) => {
        const [key] = entries[index];
        if (result.status === "fulfilled") {
          nextState[key] = unwrapResponse(result.value);
          return;
        }

        nextState.failures.push({
          key,
          message:
            result.reason?.response?.data?.detail ||
            result.reason?.message ||
            "加载失败",
        });
      });

      setDashboardData(nextState);
      setLoading(false);
    };

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [accuracyMonths, refreshToken, threshold, timeRange]);

  const stageItems = useMemo(
    () => buildOverviewStages(dashboardData.summary),
    [dashboardData.summary],
  );

  const maxStageCount = Math.max(...stageItems.map((item) => item.count), 1);
  const healthMeta = getHealthMeta(dashboardData.health?.overall_health?.level);
  const conversionStages = dashboardData.conversion?.stages || [];
  const bottleneckItems = dashboardData.bottlenecks?.bottlenecks || [];
  const predictionStages = dashboardData.prediction?.by_stage || [];
  const topAlerts = dashboardData.health?.alerts || [];
  const topActions = dashboardData.health?.top_actions || [];

  return (
    <div className="min-h-screen bg-gray-950 px-6 py-6 text-white">
      <PageHeader
        title="销售漏斗"
        description="统一漏斗工作台，整合阶段统计、转化分析、瓶颈识别和滞留预警。"
        actions={[
          {
            label: "售前工作台",
            icon: Workflow,
            to: "/sales/presale-workbench",
            variant: "outline",
            className: "border-blue-500 text-blue-300 hover:bg-blue-500/10",
          },
          {
            label: "刷新",
            icon: RefreshCw,
            onClick: () => setRefreshToken((value) => value + 1),
            variant: "outline",
            disabled: loading,
          },
        ]}
      />

      <div className="space-y-6">
        {dashboardData.failures.length > 0 && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            部分数据加载失败：
            {dashboardData.failures
              .map((item) => ` ${item.key}(${item.message})`)
              .join("；")}
          </div>
        )}

        <Card className="border-gray-800 bg-gray-900">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-blue-400" />
              分析范围
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <div className="mb-2 text-sm text-gray-400">统计周期</div>
                <Select value={timeRange} onValueChange={setTimeRange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="month">本月</SelectItem>
                    <SelectItem value="quarter">本季度</SelectItem>
                    <SelectItem value="year">本年</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <div className="mb-2 text-sm text-gray-400">瓶颈阈值</div>
                <Select value={threshold} onValueChange={setThreshold}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">50%</SelectItem>
                    <SelectItem value="55">55%</SelectItem>
                    <SelectItem value="60">60%</SelectItem>
                    <SelectItem value="65">65%</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <div className="mb-2 text-sm text-gray-400">预测复盘周期</div>
                <Select value={accuracyMonths} onValueChange={setAccuracyMonths}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">近 3 个月</SelectItem>
                    <SelectItem value="6">近 6 个月</SelectItem>
                    <SelectItem value="12">近 12 个月</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-[760px]">
            <TabsTrigger value="overview">概览</TabsTrigger>
            <TabsTrigger value="conversion">转化分析</TabsTrigger>
            <TabsTrigger value="bottlenecks">瓶颈识别</TabsTrigger>
            <TabsTrigger value="dwell-alerts">滞留预警</TabsTrigger>
            <TabsTrigger value="accuracy">预测准确性</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">线索池</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {dashboardData.summary?.leads || 0}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">当前 Pipeline</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {formatCurrency(dashboardData.health?.key_metrics?.total_pipeline)}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">目标覆盖率</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {formatPercent(dashboardData.health?.key_metrics?.target_coverage)}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-gray-400">漏斗健康度</div>
                      <div className="mt-2 text-3xl font-semibold">
                        {dashboardData.health?.overall_health?.score || 0}
                      </div>
                    </div>
                    <Badge className={healthMeta.className}>{healthMeta.label}</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
              <Card className="border-gray-800 bg-gray-900">
                <CardHeader>
                  <CardTitle>阶段漏斗</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {stageItems.map((stage) => (
                    <button
                      key={stage.key}
                      type="button"
                      className="w-full rounded-lg border border-gray-800 bg-gray-950 px-4 py-3 text-left transition-colors hover:border-gray-700"
                      onClick={() => navigate(stage.route)}
                    >
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <Badge className={stage.color}>{stage.label}</Badge>
                          <span className="text-lg font-semibold">{stage.count}</span>
                          {stage.amount > 0 && (
                            <span className="text-sm text-gray-400">
                              金额 {formatCurrency(stage.amount)}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-400">
                          转化率 {formatPercent(stage.conversion)}
                          <ArrowRight className="h-4 w-4" />
                        </div>
                      </div>
                      <Progress
                        value={(stage.count / maxStageCount) * 100}
                        className="h-2"
                      />
                    </button>
                  ))}
                </CardContent>
              </Card>

              <Card className="border-gray-800 bg-gray-900">
                <CardHeader>
                  <CardTitle>健康摘要</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-lg bg-gray-950 p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <Gauge className="h-4 w-4 text-blue-400" />
                      <span className="font-medium">关键指标</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded bg-gray-900 px-3 py-2">
                        平均客单额
                        <div className="mt-1 text-lg font-semibold">
                          {formatCurrency(dashboardData.health?.key_metrics?.avg_deal_size)}
                        </div>
                      </div>
                      <div className="rounded bg-gray-900 px-3 py-2">
                        销售速度
                        <div className="mt-1 text-lg font-semibold">
                          {dashboardData.health?.key_metrics?.sales_velocity || 0}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="text-sm font-medium text-gray-300">系统预警</div>
                    {topAlerts.length > 0 ? (
                      topAlerts.map((item, index) => (
                        <div key={`${item.title}-${index}`} className="rounded bg-gray-950 px-3 py-3">
                          <div className="flex items-center gap-2">
                            <AlertTriangle className="h-4 w-4 text-amber-400" />
                            <div className="font-medium">{item.title}</div>
                          </div>
                          <div className="mt-1 text-sm text-gray-400">{item.description}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-gray-400">暂无系统级预警</div>
                    )}
                  </div>

                  <div className="space-y-3">
                    <div className="text-sm font-medium text-gray-300">优先动作</div>
                    {topActions.length > 0 ? (
                      topActions.map((item) => (
                        <div key={item.priority} className="rounded bg-gray-950 px-3 py-3">
                          <div className="flex items-center gap-2">
                            <Badge className="bg-red-500">P{item.priority}</Badge>
                            <div className="font-medium">{item.action}</div>
                          </div>
                          <div className="mt-1 text-sm text-gray-400">{item.impact}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-gray-400">暂无高优先级动作建议</div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="conversion" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">总线索</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {dashboardData.conversion?.overall_metrics?.total_leads || 0}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">赢单数</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {dashboardData.conversion?.overall_metrics?.total_won || 0}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">整体转化率</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {formatPercent(
                      dashboardData.conversion?.overall_metrics?.overall_conversion_rate,
                    )}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">平均销售周期</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {dashboardData.conversion?.overall_metrics?.avg_sales_cycle_days || 0} 天
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="border-gray-800 bg-gray-900">
              <CardHeader>
                <CardTitle>阶段转化详情</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>阶段</TableHead>
                      <TableHead>累计商机数</TableHead>
                      <TableHead>向下一阶段转化率</TableHead>
                      <TableHead>平均停留</TableHead>
                      <TableHead>趋势</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conversionStages.map((stage) => (
                      <TableRow key={stage.stage}>
                        <TableCell>{stage.stage_name || formatStageLabel(stage.stage)}</TableCell>
                        <TableCell>{stage.count || 0}</TableCell>
                        <TableCell>
                          {stage.conversion_to_next == null
                            ? "最终阶段"
                            : formatPercent(stage.conversion_to_next)}
                        </TableCell>
                        <TableCell>
                          {stage.avg_days_in_stage == null
                            ? "未统计"
                            : `${stage.avg_days_in_stage} 天`}
                        </TableCell>
                        <TableCell>{getTrendIcon(stage.trend)}</TableCell>
                      </TableRow>
                    ))}
                    {conversionStages.length === 0 && !loading && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-gray-400">
                          当前没有转化分析数据
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="bottlenecks" className="space-y-4">
            <Card className="border-gray-800 bg-gray-900">
              <CardHeader>
                <CardTitle>瓶颈识别</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-sm text-gray-400">
                  当前阈值：低于 {threshold}% 的阶段会被优先识别为瓶颈。
                </div>
                {bottleneckItems.length > 0 ? (
                  bottleneckItems.map((item, index) => (
                    <div
                      key={`${item.stage}-${item.issue_type}-${index}`}
                      className="rounded-lg border border-gray-800 bg-gray-950 p-4"
                    >
                      <div className="mb-3 flex flex-wrap items-center gap-2">
                        <AlertTriangle
                          className={`h-4 w-4 ${
                            item.severity === "HIGH" ? "text-red-400" : "text-amber-400"
                          }`}
                        />
                        <div className="font-medium">
                          {item.stage_name || formatStageLabel(item.stage)}
                        </div>
                        <Badge className={item.severity === "HIGH" ? "bg-red-500" : "bg-amber-500"}>
                          {item.severity}
                        </Badge>
                      </div>
                      <div className="space-y-2 text-sm text-gray-300">
                        <div>
                          {item.issue_type === "low_conversion"
                            ? `当前转化率 ${formatPercent(item.current_rate)}，基准 ${formatPercent(
                                item.benchmark_rate,
                              )}`
                            : `当前停留 ${item.current_days || 0} 天，基准 ${item.benchmark_days || 0} 天`}
                        </div>
                        {item.impact && <div className="text-gray-400">{item.impact}</div>}
                        {item.root_causes?.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {item.root_causes.map((cause) => (
                              <Badge key={cause} variant="outline">
                                {cause}
                              </Badge>
                            ))}
                          </div>
                        )}
                        {item.recommendations?.length > 0 && (
                          <div className="space-y-1">
                            {item.recommendations.map((recommendation) => (
                              <div key={recommendation} className="flex items-start gap-2">
                                <ArrowRight className="mt-0.5 h-4 w-4 text-blue-400" />
                                <span>{recommendation}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-gray-400">当前未识别到显著瓶颈</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dwell-alerts">
            <DwellTimeAlerts
              onAlertClick={(alert) => {
                const routeMap = {
                  LEAD: `/sales/leads/${alert.entity_id}`,
                  OPPORTUNITY: `/sales/opportunities/${alert.entity_id}`,
                  QUOTE: `/sales/quotes/${alert.entity_id}`,
                  CONTRACT: `/sales/contracts/${alert.entity_id}`,
                };
                const targetRoute = routeMap[alert.entity_type];
                if (targetRoute) {
                  navigate(targetRoute);
                }
              }}
            />
          </TabsContent>

          <TabsContent value="accuracy" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">预测赢单率</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {formatPercent(
                      dashboardData.prediction?.overall_accuracy?.predicted_win_rate,
                    )}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">实际赢单率</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {formatPercent(
                      dashboardData.prediction?.overall_accuracy?.actual_win_rate,
                    )}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">准确性评分</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {dashboardData.prediction?.overall_accuracy?.accuracy_score || 0}
                  </div>
                </CardContent>
              </Card>
              <Card className="border-gray-800 bg-gray-900">
                <CardContent className="pt-5">
                  <div className="text-sm text-gray-400">偏差判断</div>
                  <div className="mt-2 text-3xl font-semibold">
                    {dashboardData.prediction?.overall_accuracy?.bias || "未分析"}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card className="border-gray-800 bg-gray-900">
              <CardHeader>
                <CardTitle>分阶段准确性</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>区间</TableHead>
                      <TableHead>预测</TableHead>
                      <TableHead>实际</TableHead>
                      <TableHead>准确性</TableHead>
                      <TableHead>偏差</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {predictionStages.map((stage) => (
                      <TableRow key={stage.stage}>
                        <TableCell>{stage.stage}</TableCell>
                        <TableCell>{formatPercent(stage.predicted)}</TableCell>
                        <TableCell>{formatPercent(stage.actual)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Progress value={stage.accuracy || 0} className="w-28" />
                            <span>{stage.accuracy || 0}</span>
                          </div>
                        </TableCell>
                        <TableCell>{stage.bias || "未分析"}</TableCell>
                      </TableRow>
                    ))}
                    {predictionStages.length === 0 && !loading && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-gray-400">
                          当前没有预测准确性数据
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            <div className="grid gap-6 xl:grid-cols-2">
              <Card className="border-gray-800 bg-gray-900">
                <CardHeader>
                  <CardTitle>过度乐观样本</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(dashboardData.prediction?.over_optimistic || []).map((item) => (
                    <div key={item.opportunity_id} className="rounded bg-gray-950 px-3 py-3">
                      <div className="font-medium">
                        {item.opportunity_name || `商机 #${item.opportunity_id}`}
                      </div>
                      <div className="mt-1 text-sm text-gray-400">
                        预测 {formatPercent(item.predicted_rate)}，结果 {item.actual_outcome}
                      </div>
                    </div>
                  ))}
                  {(dashboardData.prediction?.over_optimistic || []).length === 0 && (
                    <div className="text-sm text-gray-400">暂无高偏差样本</div>
                  )}
                </CardContent>
              </Card>

              <Card className="border-gray-800 bg-gray-900">
                <CardHeader>
                  <CardTitle>系统建议</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(dashboardData.prediction?.recommendations || []).map((item) => (
                    <div key={item} className="flex items-start gap-2 rounded bg-gray-950 px-3 py-3">
                      <Target className="mt-0.5 h-4 w-4 text-blue-400" />
                      <span className="text-sm text-gray-300">{item}</span>
                    </div>
                  ))}
                  {(dashboardData.prediction?.recommendations || []).length === 0 && (
                    <div className="text-sm text-gray-400">暂无预测建议</div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
