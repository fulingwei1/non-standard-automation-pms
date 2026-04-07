import { useState } from "react";


import { fadeIn, staggerContainer } from "../../lib/animations";
import { TIME_RANGE_LABELS } from "./constants";
import { useOperationDashboard } from "./useOperationDashboard";

export default function OperationDashboard() {
  const [timeRange, setTimeRange] = useState("month");
  const { dashboardData, loading, error } = useOperationDashboard(timeRange);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="运营大屏"
        description="实时监控公司运营状况，辅助管理决策"
        actions={
          <div className="flex items-center gap-2">
            {Object.entries(TIME_RANGE_LABELS).map(([range, label]) => (
              <Button
                key={range}
                variant={timeRange === range ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeRange(range)}
              >
                {label}
              </Button>
            ))}
          </div>
        }
      />

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
          运营大屏数据加载失败：{error}
        </div>
      )}
      {loading && (
        <div className="text-sm text-slate-400">数据加载中...</div>
      )}

      {/* KPI Cards */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {(dashboardData.kpis || []).map((kpi, index) => (
          <KpiCard key={index} kpi={kpi} />
        ))}
      </motion.div>

      {/* Project Health + Revenue Trend */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              项目健康度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <HealthDonut data={dashboardData.projectHealth} />
          </CardContent>
        </Card>

        <Card className="bg-surface-1/50 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              产值趋势
            </CardTitle>
            <CardDescription>近6个月产值（万元）</CardDescription>
          </CardHeader>
          <CardContent>
            <MiniBarChart data={dashboardData.monthlyTrend} />
          </CardContent>
        </Card>
      </motion.div>

      {/* Department Performance + Alerts */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        <DepartmentPerformance data={dashboardData.departmentPerformance} />
        <AlertsPanel alerts={dashboardData.alerts} />
      </motion.div>

      {/* Top Projects */}
      <motion.div variants={fadeIn}>
        <TopProjects projects={dashboardData.topProjects} />
      </motion.div>
    </motion.div>
  );
}
