import { motion, AnimatePresence } from "framer-motion";
import { Package, Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { fadeIn } from "../../lib/animations";
import { ApiIntegrationError } from "../../components/ui";
import { PurchaseOrdersOverview, PAYMENT_TERMS, SHIPPING_METHODS } from "../../components/purchase-orders";
import { usePurchaseOrders } from "./hooks";
import { OrderCard, OrdersControls } from "./components";

// Import dialogs from original location (can be extracted later)
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter
} from "../../components/ui/dialog";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from "../../components/ui/select";
import { PAYMENT_TERMS_CONFIGS } from "../../components/purchase-orders";

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
        selectedOrder,
        setSelectedOrder,
        suppliers,
        projects,
        newOrder,
        setNewOrder,
        editOrder,
        setEditOrder,
        handleCreateOrder,
        handleDeleteOrder,
        handleSubmitApproval,
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
                        {sortedOrders.map((order) => (
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
                                        setSelectedOrder(order);
                                        setEditOrder({
                                            ...order,
                                            payment_terms: order.paymentTerms || PAYMENT_TERMS.NET30,
                                            shipping_method: order.shippingMethod || SHIPPING_METHODS.STANDARD
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
                                    onApprove={(order) => handleSubmitApproval(order)}
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

                {/* Create Order Modal */}
                <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
                    <DialogContent className="sm:max-w-[700px] bg-surface-1 border-border">
                        <DialogHeader>
                            <DialogTitle className="text-white">创建采购订单</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label className="text-text-secondary">供应商</Label>
                                    <Select
                                        value={newOrder.supplier_id}
                                        onValueChange={(value) => setNewOrder({ ...newOrder, supplier_id: value })}
                                    >
                                        <SelectTrigger className="bg-surface-2 border-border">
                                            <SelectValue placeholder="选择供应商" />
                                        </SelectTrigger>
                                        <SelectContent className="bg-surface-2 border-border">
                                            {suppliers.map((supplier) => (
                                                <SelectItem key={supplier.id} value={supplier.id}>
                                                    {supplier.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div>
                                    <Label className="text-text-secondary">项目</Label>
                                    <Select
                                        value={newOrder.project_id}
                                        onValueChange={(value) => setNewOrder({ ...newOrder, project_id: value })}
                                    >
                                        <SelectTrigger className="bg-surface-2 border-border">
                                            <SelectValue placeholder="选择项目" />
                                        </SelectTrigger>
                                        <SelectContent className="bg-surface-2 border-border">
                                            {projects.map((project) => (
                                                <SelectItem key={project.id} value={project.id}>
                                                    {project.name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label className="text-text-secondary">支付条款</Label>
                                    <Select
                                        value={newOrder.payment_terms}
                                        onValueChange={(value) => setNewOrder({ ...newOrder, payment_terms: value })}
                                    >
                                        <SelectTrigger className="bg-surface-2 border-border">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent className="bg-surface-2 border-border">
                                            {Object.entries(PAYMENT_TERMS_CONFIGS).map(([key, config]) => (
                                                <SelectItem key={key} value={key}>
                                                    {config.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div>
                                <Label className="text-text-secondary">备注</Label>
                                <Textarea
                                    value={newOrder.notes}
                                    onChange={(e) => setNewOrder({ ...newOrder, notes: e.target.value })}
                                    className="bg-surface-2 border-border"
                                    rows={3}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                                取消
                            </Button>
                            <Button onClick={handleCreateOrder} className="bg-accent hover:bg-accent/90">
                                创建订单
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* Delete Confirmation Modal */}
                <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
                    <DialogContent className="sm:max-w-[400px] bg-surface-1 border-border">
                        <DialogHeader>
                            <DialogTitle className="text-white">确认删除</DialogTitle>
                        </DialogHeader>
                        <p className="text-text-secondary">
                            确定要删除订单 {selectedOrder?.id} 吗？此操作不可恢复。
                        </p>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
                                取消
                            </Button>
                            <Button variant="destructive" onClick={handleDeleteOrder}>
                                删除
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </div>
    );
}
