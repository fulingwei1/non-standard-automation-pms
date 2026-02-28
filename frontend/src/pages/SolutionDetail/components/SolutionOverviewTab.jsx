import React from 'react';
import { Target, Briefcase, ExternalLink, MessageSquare, Users } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { Avatar, AvatarFallback } from "../../../components/ui/avatar";
import { Badge } from "../../../components/ui/badge";
import { cn } from "../../../lib/utils";

export function SolutionOverviewTab({ solution }) {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧 - 描述和标签 */}
            <div className="lg:col-span-2 space-y-6">
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg">方案描述</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm text-slate-300 leading-relaxed">
                            {solution.description}
                        </p>
                        <div className="flex flex-wrap gap-2 mt-4">
                            {(solution.tags || []).map((tag, index) => (
                                <span
                                    key={index}
                                    className="px-3 py-1 bg-primary/10 text-primary text-xs rounded-full"
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* 关联商机 */}
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Target className="w-5 h-5 text-primary" />
                            关联商机
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-between p-3 bg-surface-50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                    <Briefcase className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                    <p className="text-sm font-medium text-white">
                                        {solution.opportunity}
                                    </p>
                                    <p className="text-xs text-slate-500">
                                        销售：{solution.salesPerson}
                                    </p>
                                </div>
                            </div>
                            <Button variant="ghost" size="sm">
                                <ExternalLink className="w-4 h-4" />
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* 评审状态 */}
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <MessageSquare className="w-5 h-5 text-primary" />
                            评审记录
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {(solution.reviews || []).map((review) => (
                            <div key={review.id} className="flex gap-3">
                                <Avatar className="w-8 h-8">
                                    <AvatarFallback className="bg-primary/20 text-primary text-sm">
                                        {review.avatar}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-sm font-medium text-white">
                                            {review.reviewer}
                                        </span>
                                        <span className="text-xs text-slate-500">
                                            {review.date}
                                        </span>
                                        <Badge
                                            className={cn(
                                                "text-xs",
                                                review.status === "approved"
                                                    ? "bg-emerald-500"
                                                    : review.status === "pending"
                                                        ? "bg-amber-500"
                                                        : "bg-red-500",
                                            )}
                                        >
                                            {review.status === "approved"
                                                ? "已通过"
                                                : review.status === "pending"
                                                    ? "待审核"
                                                    : "需修改"}
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-slate-400">{review.comments}</p>
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            </div>

            {/* 右侧 - 协作人员和元数据 */}
            <div className="space-y-6">
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Users className="w-5 h-5 text-primary" />
                            协作人员
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {(solution.collaborators || []).map((person, index) => (
                            <div key={index} className="flex items-center gap-3">
                                <Avatar className="w-8 h-8">
                                    <AvatarFallback className="bg-primary/20 text-primary text-sm">
                                        {person.avatar}
                                    </AvatarFallback>
                                </Avatar>
                                <div>
                                    <p className="text-sm font-medium text-white">
                                        {person.name}
                                    </p>
                                    <p className="text-xs text-slate-500">{person.role}</p>
                                </div>
                            </div>
                        ))}
                    </CardContent>
                </Card>

                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardHeader>
                        <CardTitle className="text-lg">详细信息</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3 text-sm">
                        <div className="flex justify-between">
                            <span className="text-slate-500">创建人</span>
                            <span className="text-white">{solution.creator}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500">创建时间</span>
                            <span className="text-white">{solution.createdAt}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500">更新时间</span>
                            <span className="text-white">{solution.updatedAt}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-slate-500">当前版本</span>
                            <span className="text-white">{solution.version}</span>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
