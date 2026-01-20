import React from 'react';
import { motion } from "framer-motion";
import { Building2, Briefcase, DollarSign, Calendar } from "lucide-react";
import { Card, CardContent } from "../../../components/ui/card";
import { Progress } from "../../../components/ui/progress";
import { fadeIn } from "../../../lib/animations";

export function SolutionStatsCards({ solution }) {
    return (
        <>
            <motion.div
                variants={fadeIn}
                className="grid grid-cols-1 lg:grid-cols-4 gap-4"
            >
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                                <Building2 className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500">客户</p>
                                <p className="text-sm font-medium text-white">
                                    {solution.customer}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                                <Briefcase className="w-5 h-5 text-violet-400" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500">设备类型</p>
                                <p className="text-sm font-medium text-white">
                                    {solution.deviceTypeName}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                                <DollarSign className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500">方案金额</p>
                                <p className="text-sm font-medium text-emerald-400">
                                    ¥{solution.amount}万
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardContent className="p-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                                <Calendar className="w-5 h-5 text-amber-400" />
                            </div>
                            <div>
                                <p className="text-xs text-slate-500">截止时间</p>
                                <p className="text-sm font-medium text-white">
                                    {solution.deadline}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
                <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
                    <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-slate-400">方案进度</span>
                            <span className="text-sm font-medium text-white">
                                {solution.progress}%
                            </span>
                        </div>
                        <Progress value={solution.progress} className="h-2" />
                    </CardContent>
                </Card>
            </motion.div>
        </>
    );
}
