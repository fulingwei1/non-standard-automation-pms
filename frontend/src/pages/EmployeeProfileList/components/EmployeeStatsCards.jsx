import React from 'react';
import { Users, User, Clock } from "lucide-react";
import { Card, CardContent } from "../../../components/ui/card";

export function EmployeeStatsCards({ stats, activeStatusTab }) {
    return (
        <div className="grid grid-cols-3 gap-4">
            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-blue-500/10">
                            <Users className="h-6 w-6 text-blue-400" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-white">
                                {stats.total}
                            </div>
                            <div className="text-sm text-slate-400">
                                {activeStatusTab === "active"
                                    ? "在职员工"
                                    : activeStatusTab === "regular"
                                        ? "正式员工"
                                        : activeStatusTab === "probation"
                                            ? "试用期员工"
                                            : activeStatusTab === "intern"
                                                ? "实习期员工"
                                                : activeStatusTab === "resigned"
                                                    ? "离职员工"
                                                    : "总员工数"}
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-green-500/10">
                            <User className="h-6 w-6 text-green-400" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-green-400">
                                {stats.available}
                            </div>
                            <div className="text-sm text-slate-400">可用人员 (&lt;80%)</div>
                        </div>
                    </div>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-orange-500/10">
                            <Clock className="h-6 w-6 text-orange-400" />
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-orange-400">
                                {stats.busy}
                            </div>
                            <div className="text-sm text-slate-400">繁忙人员 (≥80%)</div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
