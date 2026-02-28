import React from 'react';
import { motion } from "framer-motion";
import { Eye, Edit, Trash2, FileCheck, Calendar, AlertCircle, Plus } from "lucide-react";
import { Button, Card, CardContent, Badge, SkeletonCard } from "../../../components/ui";
import { cn, formatDate } from "../../../lib/utils";
import {
    getStatusBadge,
    getReviewTypeLabel,
    getReviewTypeColor,
    getConclusionBadge
} from '../constants';

const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.05, delayChildren: 0.1 },
    },
};

const staggerChild = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
};

export function TechnicalReviewCards({
    loading,
    reviews,
    total,
    page,
    pageSize,
    setPage,
    onCreate,
    onView,
    onEdit,
    onDeleteRequest
}) {
    if (loading) {
        return (
            <div className="grid grid-cols-1 gap-4">
                {[1, 2, 3].map((i) => (
                    <SkeletonCard key={i} />
                ))}
            </div>
        );
    }

    if (reviews.length === 0) {
        return (
            <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="p-12 text-center">
                    <FileCheck className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                    <p className="text-slate-400">暂无技术评审记录</p>
                    <Button onClick={onCreate} className="mt-4 bg-emerald-600 hover:bg-emerald-700">
                        <Plus className="w-4 h-4 mr-2" />
                        创建第一个技术评审
                    </Button>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 gap-4"
            >
                {(reviews || []).map((review) => {
                    const statusBadge = getStatusBadge(review.status);
                    const conclusionBadge = getConclusionBadge(review.conclusion);
                    const totalIssues =
                        (review.issue_count_a || 0) +
                        (review.issue_count_b || 0) +
                        (review.issue_count_c || 0) +
                        (review.issue_count_d || 0);

                    return (
                        <motion.div key={review.id} variants={staggerChild}>
                            <Card className="bg-slate-900/50 border-slate-800 hover:border-slate-700 transition-colors">
                                <CardContent className="p-6">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-3">
                                                <h3 className="text-lg font-semibold text-slate-100">
                                                    {review.review_name}
                                                </h3>
                                                <Badge
                                                    className={cn(
                                                        "px-2 py-0.5 text-xs",
                                                        getReviewTypeColor(review.review_type)
                                                    )}
                                                >
                                                    {getReviewTypeLabel(review.review_type)}
                                                </Badge>
                                                <Badge
                                                    className={cn(
                                                        "px-2 py-0.5 text-xs",
                                                        statusBadge.color
                                                    )}
                                                >
                                                    {statusBadge.label}
                                                </Badge>
                                                {conclusionBadge && (
                                                    <Badge
                                                        className={cn(
                                                            "px-2 py-0.5 text-xs",
                                                            conclusionBadge.color
                                                        )}
                                                    >
                                                        {conclusionBadge.label}
                                                    </Badge>
                                                )}
                                            </div>

                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-400 mb-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-slate-500">评审编号:</span>
                                                    <span className="text-slate-300">{review.review_no}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-slate-500">项目:</span>
                                                    <span className="text-slate-300">{review.project_no}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Calendar className="w-4 h-4" />
                                                    <span>
                                                        {formatDate(review.scheduled_date, "YYYY-MM-DD HH:mm")}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <AlertCircle className="w-4 h-4" />
                                                    <span>
                                                        问题: {totalIssues}个 (A:
                                                        {review.issue_count_a || 0} B:
                                                        {review.issue_count_b || 0} C:
                                                        {review.issue_count_c || 0} D:
                                                        {review.issue_count_d || 0})
                                                    </span>
                                                </div>
                                            </div>

                                            {review.conclusion_summary && (
                                                <p className="text-sm text-slate-400 line-clamp-2">
                                                    {review.conclusion_summary}
                                                </p>
                                            )}
                                        </div>

                                        <div className="flex gap-2 ml-4">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => onView(review)}
                                                className="text-slate-400 hover:text-slate-100"
                                            >
                                                <Eye className="w-4 h-4" />
                                            </Button>
                                            {review.status === "DRAFT" && (
                                                <>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => onEdit(review)}
                                                        className="text-slate-400 hover:text-slate-100"
                                                    >
                                                        <Edit className="w-4 h-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => onDeleteRequest(review)}
                                                        className="text-slate-400 hover:text-red-400"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        </motion.div>
                    );
                })}
            </motion.div>

            {/* 分页 */}
            {total > pageSize && (
                <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-400">
                        共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
                    </p>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="border-slate-700"
                        >
                            上一页
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
                            disabled={page >= Math.ceil(total / pageSize)}
                            className="border-slate-700"
                        >
                            下一页
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
