import React from 'react';
import { Clock, CheckCircle2, XCircle, Calendar } from "lucide-react";
import { Card, CardContent } from "../../../components/ui";

export function LeaveStatsCards({ stats }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">待审批</p>
                            <p className="text-2xl font-bold text-amber-400 mt-1">{stats.pending}</p>
                        </div>
                        <Clock className="h-8 w-8 text-amber-400" />
                    </div>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">已批准</p>
                            <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.approved}</p>
                        </div>
                        <CheckCircle2 className="h-8 w-8 text-emerald-400" />
                    </div>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">已拒绝</p>
                            <p className="text-2xl font-bold text-red-400 mt-1">{stats.rejected}</p>
                        </div>
                        <XCircle className="h-8 w-8 text-red-400" />
                    </div>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-slate-400">已批准天数</p>
                            <p className="text-2xl font-bold text-white mt-1">{stats.totalDays}</p>
                        </div>
                        <Calendar className="h-8 w-8 text-blue-400" />
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
