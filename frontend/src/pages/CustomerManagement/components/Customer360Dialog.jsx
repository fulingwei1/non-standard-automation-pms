import React from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription
} from "../../../components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import { formatCurrency, formatDate, cn } from "../../../lib/utils";

export function Customer360Dialog({ open, onOpenChange, data, loading }) {
    return (
        <Dialog
            open={open}
            onOpenChange={(open) => {
                onOpenChange(open);
            }}
        >
            <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>客户360视图</DialogTitle>
                    <DialogDescription>
                        {data?.basic_info?.customer_name ||
                            "聚合客户信息、项目、商机与财务数据"}
                    </DialogDescription>
                </DialogHeader>
                {loading ? (
                    <div className="py-10 text-center text-muted-foreground">
                        正在加载客户画像...
                    </div>
                ) : data ? (
                    <div className="space-y-6">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <Card>
                                <CardContent className="pt-4">
                                    <div className="text-xs text-muted-foreground">项目总数</div>
                                    <div className="text-2xl font-semibold">
                                        {data.summary?.total_projects || 0}
                                    </div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="pt-4">
                                    <div className="text-xs text-muted-foreground">活跃项目</div>
                                    <div className="text-2xl font-semibold text-emerald-600">
                                        {data.summary?.active_projects || 0}
                                    </div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="pt-4">
                                    <div className="text-xs text-muted-foreground">在途金额</div>
                                    <div className="text-xl font-semibold">
                                        {formatCurrency(data.summary?.pipeline_amount)}
                                    </div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardContent className="pt-4">
                                    <div className="text-xs text-muted-foreground">未回款</div>
                                    <div className="text-xl font-semibold text-red-500">
                                        {formatCurrency(data.summary?.open_receivables)}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>项目概览</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    {(data.projects || []).slice(0, 5).map((project) => (
                                        <div
                                            key={project.project_id}
                                            className="border rounded-md p-3 bg-muted/30"
                                        >
                                            <div className="flex items-center justify-between text-sm font-medium">
                                                <span>{project.project_name}</span>
                                                <Badge variant="outline">{project.status || "-"}</Badge>
                                            </div>
                                            <div className="text-xs text-muted-foreground mt-1 flex justify-between">
                                                <span>进度 {project.progress_pct || 0}%</span>
                                                <span>{formatCurrency(project.contract_amount)}</span>
                                            </div>
                                        </div>
                                    ))}
                                    {(data.projects || []).length === 0 && (
                                        <div className="text-sm text-muted-foreground">
                                            暂无项目记录
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader>
                                    <CardTitle>商机与赢率</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    {(data.opportunities || []).slice(0, 5).map((opportunity) => (
                                        <div
                                            key={opportunity.opportunity_id}
                                            className="border rounded-md p-3"
                                        >
                                            <div className="flex items-center justify-between text-sm font-medium">
                                                <span>{opportunity.opp_name}</span>
                                                <Badge variant="outline">{opportunity.stage}</Badge>
                                            </div>
                                            <div className="text-xs text-muted-foreground mt-1 flex justify-between">
                                                <span>{opportunity.owner_name || "-"}</span>
                                                <span>{formatCurrency(opportunity.est_amount)}</span>
                                            </div>
                                        </div>
                                    ))}
                                    {(data.opportunities || []).length === 0 && (
                                        <div className="text-sm text-muted-foreground">
                                            暂无商机数据
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <Card>
                                <CardHeader>
                                    <CardTitle>报价 / 合同</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    <div>
                                        <div className="text-xs text-muted-foreground mb-1">
                                            最新报价
                                        </div>
                                        {(data.quotes || []).slice(0, 3).map((quote) => (
                                            <div
                                                key={quote.quote_id}
                                                className="flex items-center justify-between text-sm py-1 border-b last:border-0"
                                            >
                                                <span>{quote.quote_code}</span>
                                                <span className="text-muted-foreground">
                                                    {quote.status}
                                                </span>
                                            </div>
                                        ))}
                                        {(data.quotes || []).length === 0 && (
                                            <div className="text-sm text-muted-foreground">
                                                暂无报价记录
                                            </div>
                                        )}
                                    </div>
                                    <div>
                                        <div className="text-xs text-muted-foreground mb-1">
                                            最新合同
                                        </div>
                                        {(data.contracts || []).slice(0, 3).map((contract) => (
                                            <div
                                                key={contract.contract_id}
                                                className="flex items-center justify-between text-sm py-1 border-b last:border-0"
                                            >
                                                <span>{contract.contract_code}</span>
                                                <span>{formatCurrency(contract.contract_amount)}</span>
                                            </div>
                                        ))}
                                        {(data.contracts || []).length === 0 && (
                                            <div className="text-sm text-muted-foreground">
                                                暂无合同记录
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader>
                                    <CardTitle>发票 / 收款节点</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    <div>
                                        <div className="text-xs text-muted-foreground mb-1">
                                            发票
                                        </div>
                                        {(data.invoices || []).slice(0, 3).map((invoice) => (
                                            <div
                                                key={invoice.invoice_id}
                                                className="flex items-center justify-between text-sm py-1 border-b last:border-0"
                                            >
                                                <span>{invoice.invoice_code}</span>
                                                <span className="text-muted-foreground">
                                                    {formatCurrency(invoice.total_amount)}
                                                </span>
                                            </div>
                                        ))}
                                        {(data.invoices || []).length === 0 && (
                                            <div className="text-sm text-muted-foreground">
                                                暂无发票记录
                                            </div>
                                        )}
                                    </div>
                                    <div>
                                        <div className="text-xs text-muted-foreground mb-1">
                                            收款节点
                                        </div>
                                        {(data.payment_plans || []).slice(0, 3).map((plan) => (
                                            <div
                                                key={plan.plan_id}
                                                className="flex items-center justify-between text-sm py-1 border-b last:border-0"
                                            >
                                                <span>{plan.payment_name}</span>
                                                <span
                                                    className={cn(
                                                        "text-xs",
                                                        plan.status === "PENDING"
                                                            ? "text-amber-600"
                                                            : plan.status === "COMPLETED"
                                                                ? "text-emerald-600"
                                                                : "text-slate-600"
                                                    )}
                                                >
                                                    {formatCurrency(plan.planned_amount)}
                                                </span>
                                            </div>
                                        ))}
                                        {(data.payment_plans || []).length === 0 && (
                                            <div className="text-sm text-muted-foreground">
                                                暂无收款计划
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                        <Card>
                            <CardHeader>
                                <CardTitle>沟通记录</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                {(data.communications || []).slice(0, 5).map((item) => (
                                    <div
                                        key={item.communication_id}
                                        className="border rounded-md p-3 bg-muted/30"
                                    >
                                        <div className="flex items-center justify-between text-sm font-medium">
                                            <span>{item.topic}</span>
                                            <span className="text-xs text-muted-foreground">
                                                {item.communication_date
                                                    ? formatDate(item.communication_date)
                                                    : "-"}
                                            </span>
                                        </div>
                                        <div className="text-xs text-muted-foreground mt-1 flex justify-between">
                                            <span>{item.owner_name || "-"}</span>
                                            <span>{item.communication_type || "-"}</span>
                                        </div>
                                    </div>
                                ))}
                                {(data.communications || []).length === 0 && (
                                    <div className="text-sm text-muted-foreground">
                                        暂无沟通记录
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                ) : (
                    <div className="py-10 text-center text-muted-foreground">
                        请选择客户查看360视图。
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
