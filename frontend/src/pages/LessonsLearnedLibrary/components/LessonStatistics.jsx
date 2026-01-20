import React from 'react';
import { TrendingUp, TrendingDown, CheckCircle2, BarChart3 } from "lucide-react";
import { Card, CardContent, SkeletonCard, Badge } from "../../../components/ui";

export function LessonStatistics({ statistics }) {
    if (!statistics) {
        return <SkeletonCard />;
    }

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-400">总数</p>
                                <p className="text-2xl font-bold text-white mt-1">
                                    {statistics.total || 0}
                                </p>
                            </div>
                            <BarChart3 className="h-8 w-8 text-primary" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-400">成功经验</p>
                                <p className="text-2xl font-bold text-emerald-400 mt-1">
                                    {statistics.success_count || 0}
                                </p>
                            </div>
                            <TrendingUp className="h-8 w-8 text-emerald-400" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-400">失败教训</p>
                                <p className="text-2xl font-bold text-red-400 mt-1">
                                    {statistics.failure_count || 0}
                                </p>
                            </div>
                            <TrendingDown className="h-8 w-8 text-red-400" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-400">已解决</p>
                                <p className="text-2xl font-bold text-emerald-400 mt-1">
                                    {statistics.resolved_count || 0}
                                </p>
                            </div>
                            <CheckCircle2 className="h-8 w-8 text-emerald-400" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* 按分类统计 */}
                {statistics.by_category &&
                    Object.keys(statistics.by_category).length > 0 && (
                        <Card>
                            <CardContent className="p-6">
                                <h3 className="text-lg font-semibold text-white mb-4">
                                    按分类统计
                                </h3>
                                <div className="space-y-2">
                                    {Object.entries(statistics.by_category).map(([cat, count]) => (
                                        <div key={cat} className="flex items-center justify-between">
                                            <span className="text-slate-300">{cat}</span>
                                            <Badge variant="secondary">{count}</Badge>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                {/* 按状态统计 */}
                {statistics.by_status &&
                    Object.keys(statistics.by_status).length > 0 && (
                        <Card>
                            <CardContent className="p-6">
                                <h3 className="text-lg font-semibold text-white mb-4">
                                    按状态统计
                                </h3>
                                <div className="space-y-2">
                                    {Object.entries(statistics.by_status).map(([status, count]) => (
                                        <div key={status} className="flex items-center justify-between">
                                            <span className="text-slate-300">{status}</span>
                                            <Badge variant="secondary">{count}</Badge>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                {/* 按优先级统计 */}
                {statistics.by_priority &&
                    Object.keys(statistics.by_priority).length > 0 && (
                        <Card>
                            <CardContent className="p-6">
                                <h3 className="text-lg font-semibold text-white mb-4">
                                    按优先级统计
                                </h3>
                                <div className="space-y-2">
                                    {Object.entries(statistics.by_priority).map(
                                        ([priority, count]) => (
                                            <div
                                                key={priority}
                                                className="flex items-center justify-between"
                                            >
                                                <span className="text-slate-300">{priority}</span>
                                                <Badge variant="secondary">{count}</Badge>
                                            </div>
                                        )
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    )}
            </div>
        </div>
    );
}
