import { motion } from "framer-motion";
import { CheckCircle2, FileText, Eye, XCircle } from "lucide-react";
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

const normalizeRiskFactors = (value) => {
    if (Array.isArray(value)) {
        return value.filter(Boolean);
    }
    if (typeof value === "string" && value.trim()) {
        try {
            const parsed = JSON.parse(value);
            if (Array.isArray(parsed)) {
                return parsed.filter(Boolean);
            }
        } catch {
            // Plain comma or Chinese-comma separated text is accepted below.
        }
        return value
            .split(/[、,，]/)
            .map((item) => item.trim())
            .filter(Boolean);
    }
    return [];
};

const formatRiskLevel = (riskLevel) => {
    if (!riskLevel) {
        return "风险待判";
    }
    const text = String(riskLevel);
    return text.includes("风险") ? text : `${text}风险`;
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
    onSubmitReview,
    onApprove,
    onReject
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
                    const canReview = ["SUBMITTED", "REVIEWING"].includes(initiation.status);
                    const handover = initiation.presale_handover_context;
                    const presaleSolution = handover?.presale_solution;
                    const presaleTicket = handover?.presale_ticket;
                    const handoverStatus = handover?.handover_status;
                    const riskFactors = normalizeRiskFactors(
                        presaleTicket?.pm_involvement_risk_factors,
                    );
                    const riskFactorsText = riskFactors.join("、");
                    const pmAssignmentLabel = presaleTicket?.pm_assigned
                        ? "PM已分配"
                        : "PM未分配";

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

                                    {handover && (
                                        <div className="mb-4 rounded-xl border border-white/10 bg-white/[0.02] p-4">
                                            <div className="flex items-center justify-between gap-3">
                                                <p className="text-sm font-medium text-white">
                                                    售前交接包
                                                </p>
                                                <Badge variant={handoverStatus?.ready ? "success" : "secondary"}>
                                                    {handoverStatus?.ready ? "已齐套" : "待补齐"}
                                                </Badge>
                                            </div>
                                            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
                                                <div>
                                                    <span className="text-xs text-slate-400">售前方案</span>
                                                    <p className="mt-1 text-sm text-white">
                                                        {presaleSolution?.name || "未关联"}
                                                    </p>
                                                    <p className="mt-1 text-xs text-slate-500">
                                                        {presaleSolution?.estimated_cost != null
                                                            ? formatCurrency(presaleSolution.estimated_cost)
                                                            : "成本未估算"}
                                                    </p>
                                                </div>
                                                <div>
                                                    <span className="text-xs text-slate-400">售前工单</span>
                                                    <p className="mt-1 text-sm text-white">
                                                        {presaleTicket?.ticket_no || "未关联"}
                                                    </p>
                                                    <p className="mt-1 text-xs text-slate-500">
                                                        {presaleTicket?.actual_hours != null
                                                            ? `${presaleTicket.actual_hours} 小时`
                                                            : "未记录工时"}
                                                    </p>
                                                </div>
                                                <div>
                                                    <span className="text-xs text-slate-400">审批风险</span>
                                                    {presaleTicket?.pm_involvement_required ? (
                                                        <div className="mt-1 flex flex-wrap gap-2">
                                                            <Badge variant="warning">PM提前介入</Badge>
                                                            <Badge variant="outline">
                                                                {formatRiskLevel(
                                                                    presaleTicket.pm_involvement_risk_level,
                                                                )}
                                                            </Badge>
                                                            <Badge variant="outline">{pmAssignmentLabel}</Badge>
                                                        </div>
                                                    ) : (
                                                        <p className="mt-1 text-sm text-slate-500">未触发PM提前介入</p>
                                                    )}
                                                </div>
                                            </div>
                                            {riskFactorsText && (
                                                <p className="mt-3 text-xs text-amber-200">
                                                    {riskFactorsText}
                                                </p>
                                            )}
                                        </div>
                                    )}

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
                                            {canReview && (
                                                <>
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => onApprove(initiation.id)}
                                                    >
                                                        <CheckCircle2 className="h-4 w-4 mr-2" />
                                                        审批通过
                                                    </Button>
                                                    <Button
                                                        size="sm"
                                                        variant="ghost"
                                                        onClick={() => onReject(initiation.id)}
                                                    >
                                                        驳回
                                                    </Button>
                                                </>
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
