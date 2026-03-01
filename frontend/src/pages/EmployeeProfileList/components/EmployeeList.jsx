import React from 'react';
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, RefreshCw, Search } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Badge } from "../../../components/ui/badge";
import { Progress } from "../../../components/ui/progress";
import { cn } from "../../../lib/utils";
import { getEmployeeStatusBadge, getWorkloadColor } from '../constants';

export function EmployeeList({
    loading,
    filteredProfiles,
    searchKeyword,
    setSearchKeyword,
    filterDepartment,
    setFilterDepartment,
    departments,
    onRefresh
}) {
    const navigate = useNavigate();

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>员工列表</CardTitle>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                        <Input
                            placeholder="搜索姓名/工号..."
                            value={searchKeyword || "unknown"}
                            onChange={(e) => setSearchKeyword(e.target.value)}
                            className="pl-9 w-64"
                        />
                    </div>
                    <select
                        value={filterDepartment || "unknown"}
                        onChange={(e) => setFilterDepartment(e.target.value)}
                        className="h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
                    >
                        <option value="all">全部部门</option>
                        {(departments || []).map((d) => (
                            <option key={d} value={d || "unknown"}>
                                {d}
                            </option>
                        ))}
                    </select>
                    <Button variant="outline" size="icon" onClick={onRefresh}>
                        <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="text-center py-12 text-slate-400">加载中...</div>
                ) : filteredProfiles.length === 0 ? (
                    <div className="text-center py-12 text-slate-400">暂无数据</div>
                ) : (
                    <div className="space-y-3">
                        {(filteredProfiles || []).map((profile, index) => (
                            <motion.div
                                key={profile.employee_id ?? profile.id ?? `profile-${index}`}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 transition-colors"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white font-semibold">
                                            {profile.employee_name?.charAt(0) || "?"}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-medium text-white">
                                                    {profile.employee_name}
                                                </span>
                                                <span className="text-xs text-slate-500">
                                                    {profile.employee_code}
                                                </span>
                                                {/* 员工状态标签 */}
                                                {(() => {
                                                    const statusBadge = getEmployeeStatusBadge(
                                                        profile.employment_status,
                                                        profile.employment_type,
                                                    );
                                                    return (
                                                        <Badge
                                                            variant={statusBadge.variant}
                                                            className={cn("text-xs", statusBadge.className)}
                                                        >
                                                            {statusBadge.label}
                                                        </Badge>
                                                    );
                                                })()}
                                            </div>
                                            <div className="text-sm text-slate-400 mt-1">
                                                {profile.department || "未分配部门"}
                                            </div>
                                            <div className="flex gap-1 mt-2">
                                                {(profile.top_skills || []).slice(0, 4).map((tag) => (
                                                    <Badge
                                                        key={tag}
                                                        variant="secondary"
                                                        className="text-xs"
                                                    >
                                                        {tag}
                                                    </Badge>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-8">
                                        {/* 综合得分 */}
                                        <div className="text-center">
                                            <div className="text-xl font-bold text-primary">
                                                {profile.avg_performance_score
                                                    ? Math.round(profile.avg_performance_score)
                                                    : "--"}
                                            </div>
                                            <div className="text-xs text-slate-500">绩效评分</div>
                                        </div>

                                        {/* 工作负载 */}
                                        <div className="w-32">
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="text-slate-400">工作负载</span>
                                                <span
                                                    className={getWorkloadColor(
                                                        profile.current_workload_pct || 0,
                                                    )}
                                                >
                                                    {profile.current_workload_pct || 0}%
                                                </span>
                                            </div>
                                            <Progress
                                                value={profile.current_workload_pct || 0}
                                                className="h-2"
                                            />
                                        </div>

                                        {/* 项目数 */}
                                        <div className="text-center">
                                            <div className="text-lg font-semibold text-white">
                                                {profile.total_projects || 0}
                                            </div>
                                            <div className="text-xs text-slate-500">参与项目</div>
                                        </div>

                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() =>
                                                navigate(
                                                    `/staff-matching/profiles/${profile.employee_id}`,
                                                )
                                            }
                                        >
                                            <Eye className="h-4 w-4 mr-1" />
                                            详情
                                        </Button>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
