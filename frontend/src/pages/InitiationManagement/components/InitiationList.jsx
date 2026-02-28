import React from 'react';
import { motion } from "framer-motion";
import { FileText, Eye, XCircle } from "lucide-react";
import { Card, CardContent, Button, SkeletonCard, Badge } from "../../../components/ui";
import { formatCurrency, formatDate } from "../../../lib/utils";
import { getStatusBadge } from '../constants';

const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.05, delayChildren: 0.1 }
    }
};

const staggerChild = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
};

export function InitiationList({
    loading,
    error,
    initiations,
    total,
    page,
    pageSize,
    setPage,
    onRetry,
    onViewDetail,
    onViewProject,
    onSubmitReview
}) {
    if (error) {
        return (
            <Card className="mb-6 border-red-500/30 bg-red-500/10">
                <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-red-400">
                            <XCircle className="h-5 w-5" />
                            <span>{error}</span>
                        </div>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={onRetry}
                            className="border-red-500/30 text-red-400 hover:bg-red-500/20"
                        >
                            重试
                        </Button>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (loading) {
        return (
            <div className="grid grid-cols-1 gap-4">
                {Array(5).fill(null).map((_, i) => (
                    <SkeletonCard key={i} />
                ))}
            </div>
        );
    }

    if (initiations.length === 0) {
        return (
            <Card>
                <CardContent className="p-12 text-center text-slate-500">
                    暂无立项申请
                </CardContent>
            </Card>
        );
    }

    return (
        <>
            <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 gap-4"
            >
                {(initiations || []).map((initiation) => {
                    if (!initiation || !initiation.id) return null;
                    const statusBadge = getStatusBadge(initiation.status);

                    return (
                        <motion.div key={initiation.id} variants={staggerChild}>
                            <Card className="hover:bg-white/[0.02] transition-colors">
                                <CardContent className="p-5">
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-indigo-500/10 ring-1 ring-primary/20">
                                                <FileText className="h-5 w-5 text-primary" />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-white">
                                                    {initiation.project_name}
                                                </h3>
                                                <p className="text-xs text-slate-500">
                                                    {initiation.application_no}
                                                </p>
                                            </div>
                                        </div>
                                        <Badge variant={statusBadge.variant}>
                                            {statusBadge.label}
                                        </Badge>
                                    </div>

                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4 text-sm">
                                        <div>
                                            <span className="text-slate-400">客户名称</span>
                                            <p className="text-white mt-1">
                                                {initiation.customer_name}
                                            </p>
                                        </div>
                                        <div>
                                            <span className="text-slate-400">合同金额</span>
                                            <p className="text-white mt-1">
                                                {initiation.contract_amount
                                                    ? formatCurrency(initiation.contract_amount)
                                                    : "未设置"}
                                            </p>
                                        </div>
                                        <div>
                                            <span className="text-slate-400">申请人</span>
                                            <p className="text-white mt-1">
                                                {initiation.applicant_name || "未知"}
                                            </p>
                                        </div>
                                        <div>
                                            <span className="text-slate-400">申请时间</span>
                                            <p className="text-white mt-1">
                                                {initiation.apply_time
                                                    ? formatDate(initiation.apply_time)
                                                    : "未设置"}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                                        <div className="flex items-center gap-2">
                                            {initiation.status === "DRAFT" && (
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => onSubmitReview(initiation.id)}
                                                >
                                                    提交评审
                                                </Button>
                                            )}
                                            {initiation.status === "APPROVED" && initiation.project_id && (
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => onViewProject(initiation.project_id)}
                                                >
                                                    查看项目
                                                </Button>
                                            )}
                                        </div>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => onViewDetail(initiation.id)}
                                        >
                                            <Eye className="h-4 w-4 mr-2" />
                                            查看详情
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    );
                })}
            </motion.div>

            {total > pageSize && (
                <div className="flex items-center justify-center gap-2 mt-6">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                    >
                        上一页
                    </Button>
                    <span className="text-sm text-slate-400">
                        第 {page} 页，共 {Math.ceil(total / pageSize)} 页
                    </span>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => p + 1)}
                        disabled={page >= Math.ceil(total / pageSize)}
                    >
                        下一页
                    </Button>
                </div>
            )}
        </>
    );
}
