import React from 'react';
import { Card, CardContent, Button, Badge, Input } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { LEAVE_TYPES, LEAVE_STATUSES } from '../constants';

export function LeaveFilters({ searchText, setSearchText, typeFilter, setTypeFilter, statusFilter, setStatusFilter }) {
    return (
        <Card>
            <CardContent className="p-4">
                <div className="flex gap-4">
                    <Input
                        placeholder="搜索员工姓名、部门..."
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        className="flex-1"
                    />

                    <select
                        value={typeFilter}
                        onChange={(e) => setTypeFilter(e.target.value)}
                        className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white"
                    >
                        {LEAVE_TYPES.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white"
                    >
                        {LEAVE_STATUSES.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                </div>
            </CardContent>
        </Card>
    );
}

export function LeaveApplicationList({ applications }) {
    return (
        <div className="space-y-4">
            {applications.map((app) => (
                <Card key={app.id}>
                    <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <h3 className="text-lg font-semibold text-white">{app.employee}</h3>
                                    <Badge variant="outline">{app.department}</Badge>
                                    <Badge variant="outline">{app.type}</Badge>
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            app.status === "pending" && "bg-amber-500/20 text-amber-400 border-amber-500/30",
                                            app.status === "approved" && "bg-green-500/20 text-green-400 border-green-500/30",
                                            app.status === "rejected" && "bg-red-500/20 text-red-400 border-red-500/30"
                                        )}
                                    >
                                        {app.status === "pending" ? "待审批" : app.status === "approved" ? "已批准" : "已拒绝"}
                                    </Badge>
                                </div>
                                <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                                    <div>
                                        <p className="text-slate-400">请假天数</p>
                                        <p className="text-white font-medium">{app.days} 天</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-400">开始日期</p>
                                        <p className="text-white font-medium">{app.startDate}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-400">结束日期</p>
                                        <p className="text-white font-medium">{app.endDate}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-400">审批人</p>
                                        <p className="text-white font-medium">{app.approver}</p>
                                    </div>
                                </div>
                                <div className="text-sm text-slate-400 mb-2">原因: {app.reason}</div>
                                {app.rejectReason && (
                                    <div className="text-sm text-red-400 mb-2">拒绝原因: {app.rejectReason}</div>
                                )}
                                <div className="text-xs text-slate-500">
                                    提交时间: {app.submitTime}
                                    {app.approveTime && ` · 审批时间: ${app.approveTime}`}
                                </div>
                            </div>
                            {app.status === "pending" && (
                                <div className="flex gap-2 ml-4">
                                    <Button size="sm">批准</Button>
                                    <Button size="sm" variant="outline">拒绝</Button>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
