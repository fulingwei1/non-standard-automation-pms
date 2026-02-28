import { motion } from "framer-motion";
import { Trash2 } from "lucide-react";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
} from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import { DAY_NAMES, getStatusBadge } from "../constants";
import { formatDate, formatFullDate } from "../utils/dateUtils";

export function TimesheetTable({
    weekDates,
    entries,
    loading,
    dailyTotals,
    weeklyTotal,
    onHoursChange,
    onDeleteEntry,
}) {
    return (
        <motion.div variants={fadeIn}>
            <Card className="bg-surface-1/50 overflow-hidden">
                <CardHeader className="pb-0">
                    <CardTitle className="text-lg">工时明细</CardTitle>
                    <CardDescription>填写每天在各项目任务上投入的工时</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="text-left p-4 text-sm font-medium text-slate-400 min-w-[200px]">
                                        项目 / 任务
                                    </th>
                                    {(weekDates || []).map((date, index) => {
                                        const isToday = formatFullDate(date) === formatFullDate(new Date());
                                        const isWeekend = index >= 5;
                                        return (
                                            <th
                                                key={index}
                                                className={cn(
                                                    "text-center p-4 text-sm font-medium min-w-[80px]",
                                                    isWeekend ? "text-slate-500" : "text-slate-400",
                                                    isToday && "bg-accent/10"
                                                )}
                                            >
                                                <div>{DAY_NAMES[index]}</div>
                                                <div className="text-xs mt-0.5">{formatDate(date)}</div>
                                            </th>
                                        );
                                    })}
                                    <th className="text-center p-4 text-sm font-medium text-slate-400 min-w-[80px]">
                                        小计
                                    </th>
                                    <th className="text-center p-4 text-sm font-medium text-slate-400 min-w-[100px]">
                                        状态
                                    </th>
                                    <th className="text-center p-4 text-sm font-medium text-slate-400 w-[60px]">
                                        操作
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {entries?.length === 0 && !loading ? (
                                    <tr>
                                        <td colSpan={10} className="p-8 text-center text-slate-400">
                                            暂无工时记录，点击"添加记录"开始填报
                                        </td>
                                    </tr>
                                ) : (
                                    (entries || []).map((entry) => {
                                        const entryTotal = Object.values(entry.hours || {}).reduce((a, b) => {
                                            const val = typeof b === "number" ? b : parseFloat(b) || 0;
                                            return a + val;
                                        }, 0);
                                        const isEditable = entry.status === "DRAFT";

                                        return (
                                            <tr
                                                key={entry.id}
                                                className="border-b border-border/50 hover:bg-surface-2/30"
                                            >
                                                <td className="p-4">
                                                    <div>
                                                        <div className="font-medium text-white text-sm">
                                                            {entry.project_name || "未分配项目"}
                                                        </div>
                                                        <div className="text-xs text-slate-400">
                                                            {entry.project_code || entry.project_id}{" "}
                                                            {entry.task_name ? `· ${entry.task_name}` : ""}
                                                        </div>
                                                    </div>
                                                </td>
                                                {(weekDates || []).map((date, index) => {
                                                    const dateStr = formatFullDate(date);
                                                    const hoursValue = entry.hours?.[dateStr];
                                                    const hours =
                                                        typeof hoursValue === "number"
                                                            ? hoursValue
                                                            : parseFloat(hoursValue) || 0;
                                                    const isToday = dateStr === formatFullDate(new Date());
                                                    const isWeekend = index >= 5;

                                                    return (
                                                        <td
                                                            key={index}
                                                            className={cn(
                                                                "p-2 text-center",
                                                                isToday && "bg-blue-500/10",
                                                                isWeekend && "bg-slate-700/30"
                                                            )}
                                                        >
                                                            {isEditable ? (
                                                                <Input
                                                                    type="number"
                                                                    min="0"
                                                                    max="24"
                                                                    step="0.5"
                                                                    value={hours > 0 ? hours : ""}
                                                                    onChange={(e) => onHoursChange(entry.id, dateStr, e.target.value)}
                                                                    className="w-16 h-8 text-center mx-auto bg-slate-700 border-slate-600 text-white"
                                                                    placeholder="0"
                                                                />
                                                            ) : (
                                                                <span
                                                                    className={cn(
                                                                        "text-sm",
                                                                        hours > 0 ? "text-white" : "text-slate-500"
                                                                    )}
                                                                >
                                                                    {hours > 0 ? hours : "-"}
                                                                </span>
                                                            )}
                                                        </td>
                                                    );
                                                })}
                                                <td className="p-4 text-center">
                                                    <span className="font-medium text-white">{entryTotal}h</span>
                                                </td>
                                                <td className="p-4 text-center">{getStatusBadge(entry.status)}</td>
                                                <td className="p-4 text-center">
                                                    {isEditable && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => onDeleteEntry(entry.id)}
                                                            className="h-8 w-8 p-0 text-slate-400 hover:text-red-400"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </Button>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}

                                {/* Daily Totals Row */}
                                <tr className="bg-surface-2/50 border-t-2 border-border">
                                    <td className="p-4 font-medium text-white">每日合计</td>
                                    {(weekDates || []).map((date, index) => {
                                        const dateStr = formatFullDate(date);
                                        const total = dailyTotals[dateStr] || 0;
                                        const isToday = dateStr === formatFullDate(new Date());
                                        const isOvertime = total > 8;

                                        return (
                                            <td
                                                key={index}
                                                className={cn(
                                                    "p-4 text-center font-medium",
                                                    isToday && "bg-accent/10",
                                                    isOvertime ? "text-amber-400" : "text-white"
                                                )}
                                            >
                                                {total}h
                                            </td>
                                        );
                                    })}
                                    <td className="p-4 text-center">
                                        <span
                                            className={cn(
                                                "font-bold text-lg",
                                                weeklyTotal > 40 ? "text-amber-400" : "text-emerald-400"
                                            )}
                                        >
                                            {weeklyTotal}h
                                        </span>
                                    </td>
                                    <td colSpan={2} />
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
