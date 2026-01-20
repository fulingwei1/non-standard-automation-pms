import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui";
import { SimpleBarChart, SimplePieChart, MonthlyTrendChart } from "../../../components/administrative/StatisticsCharts";

export function LeaveStatistics({ leaveTypeChart, leaveStatusChart, monthlyLeaveTrend }) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>统计分析</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="space-y-3">
                        <div className="text-sm font-medium text-white">请假类型分布</div>
                        <SimpleBarChart data={leaveTypeChart} height={180} />
                    </div>
                    <div className="space-y-3">
                        <div className="text-sm font-medium text-white">审批状态分布</div>
                        <SimplePieChart data={leaveStatusChart} size={180} />
                    </div>
                </div>

                <div className="mt-6 space-y-3">
                    <div className="text-sm font-medium text-white">月度请假天数趋势</div>
                    {monthlyLeaveTrend.length === 0 ? (
                        <div className="text-slate-400 text-sm py-6 text-center">
                            暂无已批准请假记录
                        </div>
                    ) : (
                        <MonthlyTrendChart data={monthlyLeaveTrend} valueKey="value" labelKey="month" height={180} />
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
