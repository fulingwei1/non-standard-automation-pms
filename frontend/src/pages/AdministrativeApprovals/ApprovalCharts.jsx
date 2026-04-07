



import { MONTHLY_TREND_BASELINE } from "./constants";

/**
 * Charts section rendered inside the Pending tab.
 *
 * Props:
 *   stats — { total, urgent, officeSupplies, vehicle, asset, meeting, leave }
 */
export function ApprovalCharts({ stats }) {
  const pieData = [
    { label: "办公用品", value: stats.officeSupplies, color: "#3b82f6" },
    { label: "车辆", value: stats.vehicle, color: "#06b6d4" },
    { label: "资产", value: stats.asset, color: "#a855f7" },
    { label: "会议", value: stats.meeting, color: "#10b981" },
    { label: "请假", value: stats.leave, color: "#f472b6" },
  ];

  const trendData = [
    ...MONTHLY_TREND_BASELINE,
    { month: "2025-01", amount: stats.total },
  ];

  return (
    <>
      {/* Pie + trend line */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>审批类型分布</CardTitle>
          </CardHeader>
          <CardContent>
            <SimplePieChart data={pieData} size={180} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>月度审批趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <MonthlyTrendChart
              data={trendData}
              valueKey="amount"
              labelKey="month"
              height={150}
            />
          </CardContent>
        </Card>
      </div>

      {/* Trend comparison cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <TrendComparisonCard
          title="待审批总数"
          current={stats.total}
          previous={20}
        />
        <TrendComparisonCard
          title="紧急事项"
          current={stats.urgent}
          previous={5}
        />
        <TrendComparisonCard
          title="办公用品审批"
          current={stats.officeSupplies}
          previous={8}
        />
      </div>
    </>
  );
}
