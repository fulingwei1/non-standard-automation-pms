import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui";
import { SimplePieChart, MonthlyTrendChart, TrendComparisonCard } from "../../../components/administrative/StatisticsCharts";

export function LeaveOverview({ leaveApplications, stats, monthlyLeaveTrend }) {
    return (
        <div className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                    <CardHeader>
                        <CardTitle>请假类型分布</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <SimplePieChart
                            data={[
                                {
                                    label: "年假",
                                    value: leaveApplications.filter((a) => a.type === "年假").length,
                                    color: "#3b82f6"
                                },
                                {
                                    label: "病假",
                                    value: leaveApplications.filter((a) => a.type === "病假").length,
                                    color: "#10b981"
                                },
                                {
                                    label: "事假",
                                    value: leaveApplications.filter((a) => a.type === "事假").length,
                                    color: "#f59e0b"
                                }
                            ]}
                            size={180}
                        />
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle>月度请假趋势</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {/* Note: Original code had hardcoded data for first 3 months and then length for Jan. 
                 I'll replace with the calculated monthlyLeaveTrend if available, or keep similar logic if desired.
                 The original logic [lines 290-294] was weird/mock-like. 
                 I'll use the real calculated monthlyLeaveTrend passed as prop for consistency. */}
                        <MonthlyTrendChart
                            data={monthlyLeaveTrend.length > 0 ? monthlyLeaveTrend : [{ month: '暂无数据', value: 0 }]}
                            valueKey="value"
                            labelKey="month"
                            height={150}
                        />
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <TrendComparisonCard title="待审批" current={stats.pending} previous={5} />
                <TrendComparisonCard title="已批准" current={stats.approved} previous={10} />
                <TrendComparisonCard title="已批准天数" current={stats.totalDays} previous={25} />
            </div>
        </div>
    );
}
