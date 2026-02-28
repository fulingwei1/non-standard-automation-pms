import { TrendingUp, TrendingDown } from "lucide-react";
import { Card, CardContent } from "../../../components/ui";
import { cn, formatCurrency } from "../../../lib/utils";

export function ProjectClosureStats({ closure }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Cost Variance */}
            <Card>
                <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-slate-400">成本偏差</span>
                        {closure.cost_variance !== null &&
                            closure.cost_variance !== undefined && (
                                <div
                                    className={cn(
                                        "flex items-center gap-1",
                                        closure.cost_variance >= 0 ? "text-red-400" : "text-emerald-400"
                                    )}
                                >
                                    {closure.cost_variance >= 0 ? (
                                        <TrendingUp className="h-4 w-4" />
                                    ) : (
                                        <TrendingDown className="h-4 w-4" />
                                    )}
                                    <span className="text-sm font-medium">
                                        {closure.cost_variance >= 0 ? "+" : ""}
                                        {formatCurrency(closure.cost_variance)}
                                    </span>
                                </div>
                            )}
                    </div>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-slate-400">预算</span>
                            <span className="text-white">
                                {closure.final_budget
                                    ? formatCurrency(closure.final_budget)
                                    : "未设置"}
                            </span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-slate-400">实际</span>
                            <span className="text-white">
                                {closure.final_cost
                                    ? formatCurrency(closure.final_cost)
                                    : "未设置"}
                            </span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Hours Variance */}
            <Card>
                <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-slate-400">工时偏差</span>
                        {closure.hours_variance !== null &&
                            closure.hours_variance !== undefined && (
                                <div
                                    className={cn(
                                        "flex items-center gap-1",
                                        closure.hours_variance >= 0 ? "text-red-400" : "text-emerald-400"
                                    )}
                                >
                                    {closure.hours_variance >= 0 ? (
                                        <TrendingUp className="h-4 w-4" />
                                    ) : (
                                        <TrendingDown className="h-4 w-4" />
                                    )}
                                    <span className="text-sm font-medium">
                                        {closure.hours_variance >= 0 ? "+" : ""}
                                        {closure.hours_variance} 小时
                                    </span>
                                </div>
                            )}
                    </div>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-slate-400">计划</span>
                            <span className="text-white">
                                {closure.final_planned_hours || 0} 小时
                            </span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-slate-400">实际</span>
                            <span className="text-white">
                                {closure.final_actual_hours || 0} 小时
                            </span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Schedule Variance */}
            <Card>
                <CardContent className="p-5">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-slate-400">进度偏差</span>
                        {closure.schedule_variance !== null &&
                            closure.schedule_variance !== undefined && (
                                <div
                                    className={cn(
                                        "flex items-center gap-1",
                                        closure.schedule_variance >= 0 ? "text-red-400" : "text-emerald-400"
                                    )}
                                >
                                    {closure.schedule_variance >= 0 ? (
                                        <TrendingUp className="h-4 w-4" />
                                    ) : (
                                        <TrendingDown className="h-4 w-4" />
                                    )}
                                    <span className="text-sm font-medium">
                                        {closure.schedule_variance >= 0 ? "+" : ""}
                                        {closure.schedule_variance} 天
                                    </span>
                                </div>
                            )}
                    </div>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-slate-400">计划工期</span>
                            <span className="text-white">
                                {closure.plan_duration || 0} 天
                            </span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-slate-400">实际工期</span>
                            <span className="text-white">
                                {closure.actual_duration || 0} 天
                            </span>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
