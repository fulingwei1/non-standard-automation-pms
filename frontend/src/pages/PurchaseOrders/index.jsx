import { motion, AnimatePresence } from "framer-motion";
import { Package, Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
    Dialog,
    DialogBody,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "../../components/ui/dialog";
import { fadeIn } from "../../lib/animations";
import { ApiIntegrationError } from "../../components/ui";
import { PurchaseOrdersOverview, PAYMENT_TERMS, SHIPPING_METHODS } from "../../components/purchase-orders";
import {
    CreateEditOrderDialog,
    OrderDetailDialog,
    ReceiveGoodsDialog,
    DeleteConfirmDialog as PurchaseOrderDeleteConfirmDialog
} from "../../components/purchase/orders";
import { usePurchaseOrders } from "./hooks";
import { OrderCard, OrdersControls } from "./components";

export default function PurchaseOrders() {
    const {
        orders,
        loading,
        error,
        searchQuery,
        setSearchQuery,
        statusFilter,
        setStatusFilter,
        sortBy,
        setSortBy,
        sortOrder,
        setSortOrder,
        sortedOrders,
        showCreateModal,
        setShowCreateModal,
        showDetailModal,
        setShowDetailModal,
        showEditModal,
        setShowEditModal,
        showDeleteModal,
        setShowDeleteModal,
        showReceiveModal,
        setShowReceiveModal,
        showApprovalModal,
        setShowApprovalModal,
        selectedOrder,
        setSelectedOrder,
        suppliers,
        projects,
        newOrder,
        setNewOrder,
        editOrder,
        setEditOrder,
        receiveData,
        setReceiveData,
        approvalData,
        setApprovalData,
        handleCreateOrder,
        handleEditOrder,
        handleDeleteOrder,
        handleSubmitApproval,
        handleApproveOrder,
        handleReceiveGoods,
        handleExportData,
        refresh
    } = usePurchaseOrders();

    if (loading) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4" />
                    <p className="text-text-secondary">加载采购订单...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <ApiIntegrationError
                    error={error}
                    onRetry={refresh}
                    title="加载采购订单失败"
                    description="无法获取采购订单数据，请检查网络连接后重试"
                />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <PageHeader
                title="采购订单管理"
                description="管理采购订单、供应商、审批流程和收货确认"
            />

            <div className="container mx-auto px-4 py-6">
                {/* Overview Section */}
                <PurchaseOrdersOverview orders={orders} />

                {/* Controls Section */}
                <OrdersControls
                    searchQuery={searchQuery}
                    setSearchQuery={setSearchQuery}
                    statusFilter={statusFilter}
                    setStatusFilter={setStatusFilter}
                    sortBy={sortBy}
                    setSortBy={setSortBy}
                    sortOrder={sortOrder}
                    setSortOrder={setSortOrder}
                    onExport={handleExportData}
                    onCreate={() => setShowCreateModal(true)}
                />

                {/* Orders Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    <AnimatePresence>
                        {(sortedOrders || []).map((order) => (
                            <motion.div
                                key={order.id}
                                initial="hidden"
                                animate="visible"
                                exit="hidden"
                                variants={fadeIn}
                                layout
                            >
                                <OrderCard
                                    order={order}
                                    onView={(order) => {
                                        setSelectedOrder(order);
                                        setShowDetailModal(true);
                                    }}
                                    onEdit={(order) => {
                                        const original = order?._original || {};
                                        setSelectedOrder(order);
                                        setEditOrder({
                                            id: order.id,
                                            supplier_id: order.supplierId || original.supplier_id || "",
                                            project_id: order.projectId || original.project_id || "",
                                            items: order.items || original.items || [],
                                            expected_date: order.expectedDate || original.required_date || "",
                                            required_date: order.expectedDate || original.required_date || "",
                                            payment_terms: order.paymentTerms || original.payment_terms || PAYMENT_TERMS.NET30,
                                            shipping_method: order.shippingMethod || original.shipping_method || SHIPPING_METHODS.STANDARD,
                                            notes: order.notes || original.notes || original.remark || "",
                                            urgency: order.urgency || original.urgency || "normal"
                                        });
                                        setShowEditModal(true);
                                    }}
                                    onDelete={(order) => {
                                        setSelectedOrder(order);
                                        setShowDeleteModal(true);
                                    }}
                                    onSubmit={(order) => {
                                        setSelectedOrder(order);
                                        setShowReceiveModal(true);
                                    }}
                                    onSubmitApproval={(order) => handleSubmitApproval(order)}
                                    onApprovalDecision={(order, approved) => {
                                        setSelectedOrder(order);
                                        setApprovalData({
                                            approved,
                                            note: approved ? "同意采购订单执行" : ""
                                        });
                                        setShowApprovalModal(true);
                                    }}
                                />
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>

                {sortedOrders.length === 0 && !loading && (
                    <div className="text-center py-12">
                        <Package className="h-16 w-16 text-text-secondary mx-auto mb-4 opacity-50" />
                        <h3 className="text-lg font-medium text-white mb-2">暂无采购订单</h3>
                        <p className="text-text-secondary mb-4">还没有创建任何采购订单</p>
                        <Button onClick={() => setShowCreateModal(true)} className="bg-accent hover:bg-accent/90">
                            <Plus className="h-4 w-4 mr-2" />
                            创建第一个采购订单
                        </Button>
                    </div>
                )}

                {/* Create / Edit / Detail / Receive / Delete Dialogs */}
                <CreateEditOrderDialog
                    open={showCreateModal}
                    onOpenChange={setShowCreateModal}
                    mode="create"
                    orderData={newOrder}
                    suppliers={suppliers}
                    projects={projects}
                    onChange={setNewOrder}
                    onSubmit={handleCreateOrder}
                />

                <CreateEditOrderDialog
                    open={showEditModal}
                    onOpenChange={(open) => {
                        setShowEditModal(open);
                        if (!open) {
                            setSelectedOrder(null);
                        }
                    }}
                    mode="edit"
                    orderData={editOrder}
                    suppliers={suppliers}
                    projects={projects}
                    onChange={setEditOrder}
                    onSubmit={handleEditOrder}
                />

                <OrderDetailDialog
                    open={showDetailModal}
                    onOpenChange={(open) => {
                        setShowDetailModal(open);
                        if (!open) {
                            setSelectedOrder(null);
                        }
                    }}
                    order={selectedOrder}
                    onSubmitApproval={handleSubmitApproval}
                />

                <ReceiveGoodsDialog
                    open={showReceiveModal}
                    onOpenChange={(open) => {
                        setShowReceiveModal(open);
                        if (!open) {
                            setSelectedOrder(null);
                        }
                    }}
                    order={selectedOrder}
                    receiveData={receiveData}
                    onChangeReceiveData={setReceiveData}
                    onConfirm={handleReceiveGoods}
                />

                <Dialog
                    open={showApprovalModal}
                    onOpenChange={(open) => {
                        setShowApprovalModal(open);
                        if (!open) {
                            setSelectedOrder(null);
                            setApprovalData({ approved: true, note: "" });
                        }
                    }}
                >
                    <DialogContent className="sm:max-w-[520px] bg-slate-800/95 border border-slate-700/50">
                        <DialogHeader>
                            <DialogTitle className="text-white">审批采购订单</DialogTitle>
                            <DialogDescription className="text-slate-400">
                                通过后订单进入可收货状态；驳回后订单退回为已驳回状态。
                            </DialogDescription>
                        </DialogHeader>
                        <DialogBody className="space-y-4">
                            <div className="rounded-lg border border-slate-700/60 bg-slate-900/50 p-4 text-sm">
                                <div className="flex items-center justify-between gap-3">
                                    <span className="text-slate-400">订单编号</span>
                                    <span className="font-mono text-white">
                                        {selectedOrder?.orderNo || selectedOrder?.id || "-"}
                                    </span>
                                </div>
                                <div className="mt-2 flex items-center justify-between gap-3">
                                    <span className="text-slate-400">供应商</span>
                                    <span className="text-white">{selectedOrder?.supplierName || "-"}</span>
                                </div>
                                <div className="mt-2 flex items-center justify-between gap-3">
                                    <span className="text-slate-400">审批动作</span>
                                    <span className={approvalData.approved ? "text-emerald-300" : "text-red-300"}>
                                        {approvalData.approved ? "审批通过" : "审批驳回"}
                                    </span>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label className="text-slate-300">审批意见</Label>
                                <Textarea
                                    value={approvalData.note}
                                    onChange={(event) =>
                                        setApprovalData((prev) => ({ ...prev, note: event.target.value }))
                                    }
                                    placeholder={approvalData.approved ? "填写通过意见（可选）" : "请填写驳回原因"}
                                    className="bg-slate-900 border-slate-700 text-white"
                                    rows={4}
                                />
                            </div>
                        </DialogBody>
                        <DialogFooter>
                            <Button
                                type="button"
                                variant="ghost"
                                onClick={() => setShowApprovalModal(false)}
                            >
                                取消
                            </Button>
                            <Button
                                type="button"
                                onClick={handleApproveOrder}
                                className={
                                    approvalData.approved
                                        ? "bg-emerald-600 hover:bg-emerald-700"
                                        : "bg-red-600 hover:bg-red-700"
                                }
                            >
                                {approvalData.approved ? "审批通过" : "审批驳回"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {selectedOrder && (
                    <PurchaseOrderDeleteConfirmDialog
                        open={showDeleteModal}
                        onOpenChange={(open) => {
                            setShowDeleteModal(open);
                            if (!open) {
                                setSelectedOrder(null);
                            }
                        }}
                        title="确认删除"
                        description={`确定要删除采购订单 ${selectedOrder.id} 吗？此操作不可撤销，请谨慎操作`}
                        onConfirm={handleDeleteOrder}
                    >
                        {selectedOrder.supplierName && (
                            <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-700/50">
                                <p className="text-sm text-slate-400">
                                    供应商：<span className="text-white">{selectedOrder.supplierName}</span>
                                </p>
                                {selectedOrder.projectName && (
                                    <p className="text-sm text-slate-400 mt-1">
                                        项目：<span className="text-white">{selectedOrder.projectName}</span>
                                    </p>
                                )}
                                {selectedOrder.totalAmount && (
                                    <p className="text-sm text-slate-400 mt-1">
                                        金额：<span className="text-white">¥{selectedOrder.totalAmount.toLocaleString()}</span>
                                    </p>
                                )}
                            </div>
                        )}
                    </PurchaseOrderDeleteConfirmDialog>
                )}
            </div>
        </div>
    );
}
