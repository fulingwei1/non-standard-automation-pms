import { motion, AnimatePresence } from "framer-motion";
import { Search, Bell, FileText, Eye, List, LayoutGrid } from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
    Card, CardContent, CardHeader, CardTitle, Button, Badge, Input,
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from "../../components/ui";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../components/ui/tabs";
import { cn } from "../../lib/utils";
import { staggerContainer, fadeIn } from "../../lib/animations";
import { PaymentTimeline } from "../../components/sales";
import {
    PaymentStatsOverview, PAYMENT_TYPES, PAYMENT_STATUS, getPaymentType, getPaymentStatus, formatCurrency
} from "../../components/payment-management";
import { usePaymentManagement } from "./hooks";
import { PaymentCard, AgingAnalysis } from "./components";

export default function PaymentManagement() {
    const {
        viewMode, setViewMode,
        searchTerm, setSearchTerm,
        selectedType, setSelectedType,
        selectedStatus, setSelectedStatus,
        selectedPayment, setSelectedPayment,
        showInvoiceDialog, setShowInvoiceDialog,
        showCollectionDialog: _showCollectionDialog, setShowCollectionDialog,
        showDetailDialog: _showDetailDialog, setShowDetailDialog,
        showReminders, setShowReminders,
        payments, filteredPayments,
        loading, page, setPage, total, pageSize,
        reminders, statistics, agingData,
        refresh
    } = usePaymentManagement();

    if (loading && payments?.length === 0) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
            </div>
        );
    }

    return (
        <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
            <PageHeader
                title="支付管理"
                description="应收账款跟踪、账龄分析、发票管理和催收提醒"
                action={
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2">
                            <span className="text-sm text-slate-400">应收总额:</span>
                            <span className="text-lg font-bold text-white">{formatCurrency(statistics?.total_receivables || 0)}</span>
                        </div>
                        <Button variant="outline" onClick={() => setShowCollectionDialog(true)}>
                            <Bell className="w-4 h-4 mr-2" />
                            批量催收
                        </Button>
                    </div>
                }
            />

            <Tabs value={viewMode} onValueChange={setViewMode} className="space-y-6">
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="overview">统计概览</TabsTrigger>
                    <TabsTrigger value="list">付款列表</TabsTrigger>
                    <TabsTrigger value="timeline">时间轴</TabsTrigger>
                    <TabsTrigger value="aging">账龄分析</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-6">
                    <PaymentStatsOverview
                        payments={payments}
                        invoices={(payments || []).filter((p) => p.invoiceNo)}
                        reminders={reminders}
                        loading={loading}
                        onRefresh={refresh}
                    />
                </TabsContent>

                <TabsContent value="list" className="space-y-6">
                    {/* Reminders */}
                    {reminders.length > 0 && (
                        <motion.div variants={fadeIn}>
                            <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
                                <CardHeader className="pb-3">
                                    <div className="flex items-center justify-between">
                                        <CardTitle className="text-lg flex items-center gap-2">
                                            <Bell className="w-5 h-5 text-amber-400" />
                                            回款提醒
                                        </CardTitle>
                                        <Button variant="ghost" size="sm" onClick={() => setShowReminders(!showReminders)}>
                                            {showReminders ? "收起" : "展开"}
                                        </Button>
                                    </div>
                                </CardHeader>
                                {showReminders && (
                                    <CardContent>
                                        <div className="space-y-2 max-h-64 overflow-y-auto">
                                            {(reminders || []).map((reminder) => (
                                                <div
                                                    key={reminder.id}
                                                    className={cn(
                                                        "p-3 rounded-lg border",
                                                        reminder.reminder_level === "urgent" ? "bg-red-500/10 border-red-500/20" :
                                                            reminder.reminder_level === "warning" ? "bg-amber-500/10 border-amber-500/20" :
                                                                "bg-blue-500/10 border-blue-500/20"
                                                    )}
                                                >
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex-1">
                                                            <div className="flex items-center gap-2">
                                                                <span className="font-medium text-white">{reminder.customer_name || "未知客户"}</span>
                                                                <Badge variant={reminder.reminder_level === "urgent" ? "destructive" : reminder.reminder_level === "warning" ? "default" : "secondary"}>
                                                                    {reminder.is_overdue ? `逾期${reminder.overdue_days}天` : `还有${reminder.days_until_due}天到期`}
                                                                </Badge>
                                                            </div>
                                                            <div className="mt-1 text-sm text-slate-400">
                                                                {reminder.contract_code && `合同：${reminder.contract_code} | `}
                                                                未收金额：¥{((reminder.unpaid_amount || 0) / 10000).toFixed(2)}万
                                                            </div>
                                                        </div>
                                                        <div className="text-right text-sm font-medium text-white">{reminder.due_date}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                )}
                            </Card>
                        </motion.div>
                    )}

                    {/* Search & Filters */}
                    <Card className="bg-slate-800/50 border-slate-700/50">
                        <CardContent className="p-6">
                            <div className="flex flex-col md:flex-row gap-4">
                                <div className="flex-1">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                                        <Input
                                            placeholder="搜索客户、项目或合同..."
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                            className="pl-10 bg-slate-900 border-slate-700 text-white"
                                        />
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)} className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2">
                                        <option value="all">全部类型</option>
                                        {Object.values(PAYMENT_TYPES).map((type) => <option key={type.key} value={type.key}>{type.label}</option>)}
                                    </select>
                                    <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2">
                                        <option value="all">全部状态</option>
                                        {Object.values(PAYMENT_STATUS).map((status) => <option key={status.key} value={status.key}>{status.label}</option>)}
                                    </select>
                                    <div className="flex items-center gap-1">
                                        <Button variant={viewMode === "list" ? "default" : "ghost"} size="sm" onClick={() => setViewMode("list")}><List className="w-4 h-4" /></Button>
                                        <Button variant={viewMode === "grid" ? "default" : "ghost"} size="sm" onClick={() => setViewMode("grid")}><LayoutGrid className="w-4 h-4" /></Button>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Payment List */}
                    <div className="space-y-4">
                        {filteredPayments.length === 0 ? (
                            <Card className="bg-slate-800/50 border-slate-700/50">
                                <CardContent className="p-12 text-center">
                                    <div className="text-slate-400">
                                        {searchTerm || selectedType !== "all" || selectedStatus !== "all" ? "没有找到匹配的付款记录" : "暂无付款记录"}
                                    </div>
                                </CardContent>
                            </Card>
                        ) : (
                            <>
                                {viewMode === "list" ? (
                                    <Card className="bg-slate-800/50 border-slate-700/50">
                                        <div className="overflow-x-auto">
                                            <table className="w-full">
                                                <thead>
                                                    <tr className="border-b border-slate-700">
                                                        <th className="text-left p-4 text-slate-400">客户</th>
                                                        <th className="text-left p-4 text-slate-400">项目</th>
                                                        <th className="text-left p-4 text-slate-400">类型</th>
                                                        <th className="text-right p-4 text-slate-400">金额</th>
                                                        <th className="text-left p-4 text-slate-400">到期日</th>
                                                        <th className="text-left p-4 text-slate-400">状态</th>
                                                        <th className="text-right p-4 text-slate-400">操作</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <AnimatePresence>
                                                        {(filteredPayments || []).map((payment) => (
                                                            <motion.tr key={payment.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="border-b border-slate-700/50">
                                                                <td className="p-4">
                                                                    <div className="text-white font-medium">{payment.customerName}</div>
                                                                    <div className="text-slate-400 text-sm">{payment.contractNo}</div>
                                                                </td>
                                                                <td className="p-4 text-white">{payment.projectName}</td>
                                                                <td className="p-4"><Badge variant="outline" className={cn("border", getPaymentType(payment.type).borderColor, getPaymentType(payment.type).textColor)}>{getPaymentType(payment.type).label}</Badge></td>
                                                                <td className="p-4 text-right font-medium text-white">{formatCurrency(payment.amount)}</td>
                                                                <td className="p-4 text-white">{payment.dueDate ? new Date(payment.dueDate).toLocaleDateString() : "-"}</td>
                                                                <td className="p-4"><Badge variant="outline" className={cn("border", getPaymentStatus(payment.status).borderColor, getPaymentStatus(payment.status).textColor)}>{getPaymentStatus(payment.status).label}</Badge></td>
                                                                <td className="p-4">
                                                                    <div className="flex items-center justify-end gap-2">
                                                                        {payment.status !== "paid" && (
                                                                            <Button variant="outline" size="sm" onClick={() => { setSelectedPayment(payment); setShowInvoiceDialog(true); }}>
                                                                                <FileText className="w-3 h-3 mr-1" />开票
                                                                            </Button>
                                                                        )}
                                                                        <Button variant="ghost" size="sm" onClick={() => { setSelectedPayment(payment); setShowDetailDialog(true); }}>
                                                                            <Eye className="w-3 h-3" />
                                                                        </Button>
                                                                    </div>
                                                                </td>
                                                            </motion.tr>
                                                        ))}
                                                    </AnimatePresence>
                                                </tbody>
                                            </table>
                                        </div>
                                    </Card>
                                ) : (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {(filteredPayments || []).map((payment) => (
                                            <PaymentCard
                                                key={payment.id}
                                                payment={payment}
                                                onInvoice={(p) => { setSelectedPayment(p); setShowInvoiceDialog(true); }}
                                                onViewDetail={(p) => { setSelectedPayment(p); setShowDetailDialog(true); }}
                                            />
                                        ))}
                                    </div>
                                )}

                                {total > pageSize && (
                                    <div className="flex items-center justify-center gap-2 mt-6">
                                        <Button variant="outline" onClick={() => setPage(page - 1)} disabled={page === 1}>上一页</Button>
                                        <span className="text-slate-400">第 {page} 页，共 {Math.ceil(total / pageSize)} 页</span>
                                        <Button variant="outline" onClick={() => setPage(page + 1)} disabled={page >= Math.ceil(total / pageSize)}>下一页</Button>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="timeline" className="space-y-6">
                    <PaymentTimeline payments={payments} />
                </TabsContent>

                <TabsContent value="aging" className="space-y-6">
                    <AgingAnalysis agingData={agingData} />
                </TabsContent>
            </Tabs>

            {/* Invoice Dialog */}
            <Dialog open={showInvoiceDialog} onOpenChange={setShowInvoiceDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>申请开票</DialogTitle>
                        <DialogDescription>为选中的付款申请开具发票</DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                        <p className="text-sm text-slate-400">客户: {selectedPayment?.customerName}</p>
                        <p className="text-sm text-slate-400">金额: {formatCurrency(selectedPayment?.amount || 0)}</p>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowInvoiceDialog(false)}>取消</Button>
                        <Button onClick={() => setShowInvoiceDialog(false)}>确认开票</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </motion.div>
    );
}
