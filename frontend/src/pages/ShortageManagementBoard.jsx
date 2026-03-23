/**
 * Shortage Management Board Page - 缺料管理看板页面
 * 统一入口，直接消费真实 shortage analytics / arrivals API
 */
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  BarChart3,
  FolderKanban,
  Package,
  ShieldAlert,
  Truck,
} from "lucide-react";




import { formatDate } from "../lib/utils";
import { shortageApi } from "../services/api";

const extractApiData = (response) => response?.data?.data ?? response?.data ?? response ?? null;

const extractList = (response) => {
  const data = extractApiData(response);
  if (Array.isArray(data?.items)) {
    return data.items;
  }
  if (Array.isArray(data)) {
    return data;
  }
  return [];
};

const urgentLevelLabel = (level) => {
  switch (level) {
    case "CRITICAL":
      return "特急";
    case "URGENT":
      return "紧急";
    case "NORMAL":
      return "普通";
    default:
      return level || "未知";
  }
};

const urgentLevelVariant = (level) => {
  switch (level) {
    case "CRITICAL":
      return "danger";
    case "URGENT":
      return "warning";
    case "NORMAL":
      return "info";
    default:
      return "outline";
  }
};

const arrivalStatusLabel = (status) => {
  switch (status) {
    case "PENDING":
      return "待到货";
    case "IN_TRANSIT":
      return "运输中";
    case "ARRIVED":
      return "已到货";
    case "RECEIVED":
      return "已收货";
    case "CANCELLED":
      return "已取消";
    default:
      return status || "未知";
  }
};

const solutionTypeLabel = (value) => {
  const map = {
    PURCHASE: "采购补料",
    SUBSTITUTE: "物料替代",
    TRANSFER: "库存调拨",
    DESIGN_CHANGE: "设计变更",
    REPAIR: "返修处理",
    WAITING: "等待到货",
    UNKNOWN: "未标记",
  };
  return map[value] || value || "未知";
};

const chartPalette = ["#8b5cf6", "#06b6d4", "#f59e0b", "#ef4444", "#22c55e", "#a855f7"];

const toSortedArray = (items, field = "count") =>
  Array.isArray(items)
    ? [...items].sort((a, b) => (b?.[field] || 0) - (a?.[field] || 0))
    : [];

const SectionEmpty = ({ text }) => (
  <div className="text-center py-10 text-slate-400 text-sm">{text}</div>
);

const MiniMetric = ({ label, value, hint, valueClassName = "text-white" }) => (
  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 space-y-1">
    <div className="text-xs text-slate-400">{label}</div>
    <div className={`text-xl font-semibold ${valueClassName}`}>{value}</div>
    {hint ? <div className="text-xs text-slate-500">{hint}</div> : null}
  </div>
);

const DistributionRow = ({ label, value, total, color = "primary", extra }) => {
  const percent = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-4 text-sm">
        <div>
          <div className="text-slate-200 font-medium">{label}</div>
          {extra ? <div className="text-xs text-slate-500">{extra}</div> : null}
        </div>
        <div className="text-right">
          <div className="text-white font-semibold">{value}</div>
          <div className="text-xs text-slate-500">{percent}%</div>
        </div>
      </div>
      <Progress value={percent} color={color} />
    </div>
  );
};

export default function ShortageManagementBoard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [boardData, setBoardData] = useState(null);
  const [arrivals, setArrivals] = useState([]);
  const [latestDailyReport, setLatestDailyReport] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [causeAnalysis, setCauseAnalysis] = useState(null);

  const loadBoardData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, arrivalsRes, dailyRes, trendsRes, causeRes] = await Promise.allSettled([
        shortageApi.statistics.dashboard(),
        shortageApi.arrivals.list({ page_size: 10 }),
        shortageApi.statistics.latestDailyReport(),
        shortageApi.statistics.trends({ days: 30 }),
        shortageApi.statistics.causeAnalysis(),
      ]);

      setBoardData(
        dashboardRes.status === "fulfilled" ? extractApiData(dashboardRes.value) || {} : null,
      );
      setArrivals(arrivalsRes.status === "fulfilled" ? extractList(arrivalsRes.value) : []);
      setLatestDailyReport(
        dailyRes.status === "fulfilled" ? extractApiData(dailyRes.value) : null,
      );
      setTrendData(trendsRes.status === "fulfilled" ? extractApiData(trendsRes.value) : null);
      setCauseAnalysis(
        causeRes.status === "fulfilled" ? extractApiData(causeRes.value) : null,
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBoardData();
  }, []);

  const recentReports = boardData?.recent_reports || [];
  const dashboardReports = boardData?.reports || {};
  const dashboardAlerts = boardData?.alerts || {};
  const dashboardArrivals = boardData?.arrivals || {};
  const dashboardSubstitutions = boardData?.substitutions || {};
  const dashboardTransfers = boardData?.transfers || {};
  const trendSummary = trendData?.summary || {};
  const trendSeries = useMemo(
    () =>
      (trendData?.daily || []).slice(-14).map((item) => ({
        ...item,
        label: item.date?.slice(5) || item.date,
      })),
    [trendData],
  );
  const topSolutions = useMemo(
    () => toSortedArray(causeAnalysis?.by_solution, "count").slice(0, 5),
    [causeAnalysis],
  );
  const urgentDistribution = useMemo(
    () => toSortedArray(causeAnalysis?.by_urgent, "count"),
    [causeAnalysis],
  );
  const topProjects = useMemo(
    () => toSortedArray(causeAnalysis?.by_project, "count").slice(0, 5),
    [causeAnalysis],
  );
  const solutionChartData = useMemo(
    () =>
      topSolutions.map((item, index) => ({
        ...item,
        name: solutionTypeLabel(item.solution_type),
        fill: chartPalette[index % chartPalette.length],
      })),
    [topSolutions],
  );
  const urgentTotal = urgentDistribution.reduce((sum, item) => sum + (item.count || 0), 0);
  const projectTotal = topProjects.reduce((sum, item) => sum + (item.count || 0), 0);
  const latestAlertLevels = latestDailyReport?.alerts?.levels || {};
  const onTimeRate = Number(latestDailyReport?.arrivals?.on_time_rate || 0);
  const kitRate = Number(latestDailyReport?.kit?.kit_rate || 0);
  const avgResolveHours = Number(latestDailyReport?.response?.avg_resolve_hours || 0);

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-3">
          <PageHeader
            title="缺料管理看板"
            description="统一入口，直接使用真实 shortage analytics / arrivals API 数据"
          />
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="success">真实 API</Badge>
            <Badge variant="info">数据库实时数据</Badge>
            <Badge variant="outline">
              周期：{trendData?.period?.days || 30} 天
            </Badge>
            {causeAnalysis?.period?.start && causeAnalysis?.period?.end ? (
              <Badge variant="outline">
                分析区间：{causeAnalysis.period.start} ~ {causeAnalysis.period.end}
              </Badge>
            ) : null}
          </div>
        </div>

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate("/shortage")}>缺料管理</Button>
          <Button variant="outline" onClick={loadBoardData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-6 gap-4">
        <DashboardStatCard
          icon={Package}
          label="缺料上报总数"
          value={dashboardReports.total || 0}
          description="当前系统累计缺料上报"
          iconColor="text-blue-400"
          iconBg="bg-blue-500/10"
        />
        <DashboardStatCard
          icon={AlertTriangle}
          label="紧急缺料"
          value={dashboardReports.urgent || 0}
          description="需要优先处理"
          iconColor="text-red-400"
          iconBg="bg-red-500/10"
        />
        <DashboardStatCard
          icon={ShieldAlert}
          label="未解决预警"
          value={dashboardAlerts.unresolved || 0}
          description={`严重预警 ${dashboardAlerts.critical || 0} 条`}
          iconColor="text-amber-400"
          iconBg="bg-amber-500/10"
        />
        <DashboardStatCard
          icon={Truck}
          label="延迟到货"
          value={dashboardArrivals.delayed || 0}
          description={`待到货 ${dashboardArrivals.pending || 0} 条`}
          iconColor="text-orange-400"
          iconBg="bg-orange-500/10"
        />
        <DashboardStatCard
          icon={FolderKanban}
          label="待处理替代"
          value={dashboardSubstitutions.pending || 0}
          description={`替代总数 ${dashboardSubstitutions.total || 0}`}
          iconColor="text-cyan-400"
          iconBg="bg-cyan-500/10"
        />
        <DashboardStatCard
          icon={BarChart3}
          label="待处理调拨"
          value={dashboardTransfers.pending || 0}
          description={`调拨总数 ${dashboardTransfers.total || 0}`}
          iconColor="text-violet-400"
          iconBg="bg-violet-500/10"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  缺料趋势
                </CardTitle>
                <CardDescription>最近 14 天新增 / 已解决 / 净新增变化</CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">新增 {trendSummary.total_new || 0}</Badge>
                <Badge variant="outline">解决 {trendSummary.total_resolved || 0}</Badge>
                <Badge variant="outline">日均新增 {trendSummary.avg_daily_new || 0}</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {trendSeries.length === 0 ? (
              <SectionEmpty text="暂无趋势数据" />
            ) : (
              <div className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendSeries}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                    <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        background: "#0f172a",
                        border: "1px solid rgba(148,163,184,0.2)",
                        borderRadius: 12,
                        color: "#e2e8f0",
                      }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="new" name="新增" stroke="#8b5cf6" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="resolved" name="解决" stroke="#22c55e" strokeWidth={3} dot={false} />
                    <Line type="monotone" dataKey="net" name="净新增" stroke="#f59e0b" strokeWidth={3} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="w-4 h-4 text-cyan-400" />
                最新缺料日报
              </CardTitle>
              <CardDescription>看今天缺料处理有没有真往前走</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {latestDailyReport ? (
                <>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">日报日期</span>
                    <span className="text-white font-medium">{latestDailyReport.date || "-"}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <MiniMetric label="新增上报" value={latestDailyReport.reports?.new || 0} />
                    <MiniMetric label="已解决" value={latestDailyReport.reports?.resolved || 0} valueClassName="text-emerald-400" />
                    <MiniMetric label="延迟到货" value={latestDailyReport.arrivals?.delayed || 0} valueClassName="text-amber-400" />
                    <MiniMetric label="停线时长" value={`${latestDailyReport.stoppage?.hours || 0}h`} valueClassName="text-orange-400" />
                  </div>
                  <div className="space-y-3 pt-1">
                    <div>
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-slate-400">到货准时率</span>
                        <span className="text-white font-medium">{onTimeRate}%</span>
                      </div>
                      <Progress value={onTimeRate} color={onTimeRate >= 85 ? "success" : onTimeRate >= 60 ? "warning" : "danger"} />
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-slate-400">齐套率</span>
                        <span className="text-white font-medium">{kitRate}%</span>
                      </div>
                      <Progress value={kitRate} color={kitRate >= 85 ? "success" : kitRate >= 60 ? "warning" : "danger"} />
                    </div>
                  </div>
                </>
              ) : (
                <SectionEmpty text="暂无最新日报数据" />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                今日风险摘要
              </CardTitle>
              <CardDescription>最值得盯的缺料与响应指标</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3">
              <MiniMetric label="一级预警" value={latestAlertLevels.level1 || 0} valueClassName="text-red-400" />
              <MiniMetric label="二级预警" value={latestAlertLevels.level2 || 0} valueClassName="text-amber-400" />
              <MiniMetric label="平均响应" value={`${latestDailyReport?.response?.avg_response_minutes || 0} 分钟`} />
              <MiniMetric label="平均解决" value={`${avgResolveHours} 小时`} valueClassName="text-cyan-400" />
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-violet-400" />
              原因分析 / 解决方案分布
            </CardTitle>
            <CardDescription>先看哪种处理方式最常见，再看它到底有没有效率</CardDescription>
          </CardHeader>
          <CardContent>
            {solutionChartData.length === 0 ? (
              <SectionEmpty text="暂无原因分析数据" />
            ) : (
              <div className="space-y-6">
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={solutionChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.12)" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#94a3b8" fontSize={12} />
                      <Tooltip
                        contentStyle={{
                          background: "#0f172a",
                          border: "1px solid rgba(148,163,184,0.2)",
                          borderRadius: 12,
                          color: "#e2e8f0",
                        }}
                      />
                      <Legend />
                      <Bar dataKey="count" name="次数" radius={[8, 8, 0, 0]}>
                        {solutionChartData.map((entry, index) => (
                          <Cell key={entry.name} fill={entry.fill || chartPalette[index % chartPalette.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="space-y-3">
                  {solutionChartData.map((item) => (
                    <div key={item.name} className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <div className="text-white font-medium">{item.name}</div>
                          <div className="text-xs text-slate-500">
                            平均解决时长 {item.avg_resolve_time_hours || 0} 小时
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-semibold">{item.count} 次</div>
                          <div className="text-xs text-slate-500">总缺料 {item.total_shortage_qty || 0}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldAlert className="w-4 h-4 text-red-400" />
                紧急程度分布
              </CardTitle>
              <CardDescription>看问题是“多”还是“急”</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {urgentDistribution.length === 0 ? (
                <SectionEmpty text="暂无紧急程度分布数据" />
              ) : (
                urgentDistribution.map((item) => (
                  <DistributionRow
                    key={item.urgent_level}
                    label={urgentLevelLabel(item.urgent_level)}
                    value={item.count || 0}
                    total={urgentTotal}
                    color={item.urgent_level === "CRITICAL" ? "danger" : item.urgent_level === "URGENT" ? "warning" : "primary"}
                    extra={`总缺料 ${item.total_shortage_qty || 0}`}
                  />
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FolderKanban className="w-4 h-4 text-cyan-400" />
                项目分布 Top 5
              </CardTitle>
              <CardDescription>最容易出缺料的项目，一眼看出来</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {topProjects.length === 0 ? (
                <SectionEmpty text="暂无项目分布数据" />
              ) : (
                topProjects.map((item, index) => (
                  <DistributionRow
                    key={`${item.project_id}-${item.project_name}`}
                    label={`${index + 1}. ${item.project_name || "未命名项目"}`}
                    value={item.count || 0}
                    total={projectTotal}
                    color={index === 0 ? "danger" : index < 3 ? "warning" : "primary"}
                    extra={`缺料数量 ${item.total_shortage_qty || 0}`}
                  />
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle>最新缺料上报</CardTitle>
                <CardDescription>从看板直接钻到最该处理的单子</CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate("/shortage-reports")}>
                查看全部
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {recentReports.length === 0 ? (
              <SectionEmpty text="暂无缺料上报" />
            ) : (
              <div className="space-y-3">
                {recentReports.slice(0, 5).map((report) => (
                  <div
                    key={report.id}
                    className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:bg-white/[0.05] transition-colors cursor-pointer"
                    onClick={() => navigate(`/shortage/reports/${report.id}`)}
                  >
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-white truncate">
                          {report.material_name || report.title || "未命名缺料上报"}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          {report.project_name || "未关联项目"}
                        </div>
                      </div>
                      <Badge variant={urgentLevelVariant(report.urgent_level)}>
                        {urgentLevelLabel(report.urgent_level)}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="text-slate-400">
                        缺料数量
                        <div className="text-red-400 font-semibold text-sm mt-1">
                          {report.shortage_qty || 0}
                        </div>
                      </div>
                      <div className="text-slate-400">
                        上报时间
                        <div className="text-slate-200 font-medium text-sm mt-1">
                          {report.report_time ? formatDate(report.report_time) : "-"}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle>到货跟踪</CardTitle>
                <CardDescription>缺料闭环有没有推进，看这个就够了</CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate("/arrival-tracking")}>
                查看全部
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {arrivals.length === 0 ? (
              <SectionEmpty text="暂无到货跟踪" />
            ) : (
              <div className="space-y-3">
                {arrivals.slice(0, 5).map((arrival) => (
                  <div
                    key={arrival.id}
                    className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:bg-white/[0.05] transition-colors cursor-pointer"
                    onClick={() => navigate(`/arrival-tracking/${arrival.id}`)}
                  >
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-white truncate">{arrival.material_name}</div>
                        <div className="text-xs text-slate-500 mt-1 font-mono">{arrival.arrival_no}</div>
                      </div>
                      <Badge variant={arrival.is_delayed ? "danger" : "outline"}>
                        {arrival.is_delayed ? "延迟" : arrivalStatusLabel(arrival.status)}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="text-slate-400">
                        预期日期
                        <div className="text-slate-200 font-medium text-sm mt-1">
                          {arrival.expected_date ? formatDate(arrival.expected_date) : "-"}
                        </div>
                      </div>
                      <div className="text-slate-400">
                        实际日期
                        <div className={`text-sm font-medium mt-1 ${arrival.actual_date ? "text-emerald-400" : "text-slate-300"}`}>
                          {arrival.actual_date ? formatDate(arrival.actual_date) : "未到货"}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between mt-3 text-xs text-slate-500">
                      <span>供应商：{arrival.supplier_name || "-"}</span>
                      <span>延迟天数：{arrival.delay_days || 0}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
          <CardDescription>缺料看板、上报、到货跟踪，一步直达</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-auto py-4 flex-col" onClick={() => navigate("/shortage") }>
              <AlertTriangle className="w-6 h-6 mb-2" />
              <span>缺料管理</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" onClick={() => navigate("/shortage-reports") }>
              <Package className="w-6 h-6 mb-2" />
              <span>缺料上报</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" onClick={() => navigate("/arrival-tracking") }>
              <Clock className="w-6 h-6 mb-2" />
              <span>到货跟踪</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col" onClick={() => navigate("/kit-rate") }>
              <TrendingUp className="w-6 h-6 mb-2" />
              <span>齐套看板</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
