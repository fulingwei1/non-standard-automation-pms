import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import {
    purchaseApi,
    supplierApi,
    projectApi
} from "../../../services/api";
import { toast } from "../../../components/ui/toast";
import { ORDER_STATUS_CONFIGS } from "../../../lib/constants/procurement";
import {
    ORDER_STATUS,
    ORDER_URGENCY,
    PAYMENT_TERMS,
    SHIPPING_METHODS,
    PurchaseOrderUtils
} from "../../../components/purchase-orders";

export function usePurchaseOrders() {
    const [searchParams] = useSearchParams();
    const initialStatus = searchParams.get("status") || "all";

    // States
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState(initialStatus);
    const [sortBy, setSortBy] = useState("expected_date");
    const [sortOrder, setSortOrder] = useState("asc");

    // Modal states
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showDetailModal, setShowDetailModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showReceiveModal, setShowReceiveModal] = useState(false);
    const [selectedOrder, setSelectedOrder] = useState(null);

    // Dropdown data
    const [suppliers, setSuppliers] = useState([]);
    const [projects, setProjects] = useState([]);

    // Form states
    const [newOrder, setNewOrder] = useState({
        supplier_id: "",
        project_id: "",
        items: [],
        payment_terms: PAYMENT_TERMS.NET30,
        shipping_method: SHIPPING_METHODS.STANDARD,
        notes: "",
        urgency: ORDER_URGENCY.NORMAL
    });

    const [editOrder, setEditOrder] = useState({
        id: "",
        supplier_id: "",
        project_id: "",
        items: [],
        payment_terms: PAYMENT_TERMS.NET30,
        shipping_method: SHIPPING_METHODS.STANDARD,
        notes: "",
        urgency: ORDER_URGENCY.NORMAL
    });

    const [receiveData, setReceiveData] = useState({
        received_items: [],
        notes: "",
        received_date: new Date().toISOString().split('T')[0]
    });

    // Load orders
    const loadOrders = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const params = {
                page_size: 1000,
                ...(statusFilter && statusFilter !== "all" && { status: statusFilter }),
                ...(searchQuery && { search: searchQuery })
            };

            const response = await purchaseApi.list(params);
            let ordersData = response.data?.data || response.data?.items || response.data || [];

            if (!Array.isArray(ordersData)) {
                ordersData = [];
            }

            // Transform API response
            const transformedOrders = ordersData.map((order) => {
                const items = order.items || [];
                const itemCount = items.length;
                const receivedCount = items.filter(
                    (item) => (item.received_qty || 0) >= (item.quantity || 0)
                ).length;

                return {
                    id: order.id || order.purchase_order_id || `PO-${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
                    supplierId: order.supplier_id || "",
                    supplierName: order.supplier_name || order.supplier?.name || "未知供应商",
                    projectId: order.project_id || order.project?.id || "",
                    projectName: order.project_name || order.project?.name || "",
                    status: order.status || ORDER_STATUS.DRAFT,
                    urgency: order.urgency || ORDER_URGENCY.NORMAL,
                    buyer: order.buyer_name || order.buyer || "",
                    createdDate: order.created_date || order.createdAt || "",
                    expectedDate: order.expected_date || order.delivery_date || "",
                    delayedDate: order.delayed_date || "",
                    delayReason: order.delay_reason || "",
                    totalAmount: parseFloat(order.total_amount || order.amount_with_tax || 0),
                    receivedAmount: 0,
                    itemCount: itemCount,
                    receivedCount: receivedCount,
                    items: items.map((item) => ({
                        code: item.material_code || "",
                        name: item.material_name || "",
                        qty: item.quantity || 0,
                        price: parseFloat(item.unit_price || 0),
                        received: item.received_qty || 0
                    })),
                    _original: order
                };
            });

            // Calculate received amounts and check delays
            transformedOrders.forEach((order) => {
                order.receivedAmount = PurchaseOrderUtils.calculateReceivedAmount(order.items);

                if (PurchaseOrderUtils.isOrderDelayed(order.expectedDate, order.status)) {
                    order.status = ORDER_STATUS.DELAYED;
                    order.delayedDate = PurchaseOrderUtils.formatDate(new Date());
                }
            });

            setOrders(transformedOrders);
        } catch (err) {
            console.error("Failed to load purchase orders:", err);
            setError(err);
            setOrders([]);
        } finally {
            setLoading(false);
        }
    }, [statusFilter, searchQuery]);

    // Load dropdown data
    useEffect(() => {
        const loadDropdownData = async () => {
            try {
                const [suppliersRes, projectsRes] = await Promise.all([
                    supplierApi.list({ page_size: 1000 }),
                    projectApi.list({ page_size: 1000 })
                ]);

                const suppliersData = suppliersRes.data?.items || suppliersRes.data || [];
                const projectsData = projectsRes.data?.items || projectsRes.data || [];

                setSuppliers(suppliersData);
                setProjects(projectsData);
            } catch (err) {
                console.error("Failed to load dropdown data:", err);
                setSuppliers([]);
                setProjects([]);
            }
        };

        loadDropdownData();
    }, []);

    // Initial load and reload on filter changes
    useEffect(() => {
        loadOrders();
    }, [loadOrders]);

    // Client-side filtering and sorting
    const filteredOrders = PurchaseOrderUtils.searchOrders(orders, searchQuery);
    const sortedOrders = PurchaseOrderUtils.sortOrders(filteredOrders, sortBy, sortOrder);

    // Event handlers
    const handleCreateOrder = async () => {
        try {
            const errors = PurchaseOrderUtils.validateOrder(newOrder);
            if (errors.length > 0) {
                toast.error(errors.join(", "));
                return;
            }

            const orderData = {
                ...newOrder,
                id: PurchaseOrderUtils.generateOrderNumber(),
                total_amount: PurchaseOrderUtils.calculateOrderTotal(newOrder.items),
                expected_date: newOrder.expected_date
            };

            await purchaseApi.create(orderData);
            toast.success("采购订单创建成功");
            setShowCreateModal(false);
            setNewOrder({
                supplier_id: "",
                project_id: "",
                items: [],
                payment_terms: PAYMENT_TERMS.NET30,
                shipping_method: SHIPPING_METHODS.STANDARD,
                notes: "",
                urgency: ORDER_URGENCY.NORMAL
            });
            loadOrders();
        } catch (err) {
            console.error("Failed to create order:", err);
            toast.error("创建采购订单失败");
        }
    };

    const handleEditOrder = async () => {
        try {
            const errors = PurchaseOrderUtils.validateOrder(editOrder);
            if (errors.length > 0) {
                toast.error(errors.join(", "));
                return;
            }

            const orderData = {
                ...editOrder,
                total_amount: PurchaseOrderUtils.calculateOrderTotal(editOrder.items)
            };

            await purchaseApi.update(editOrder.id, orderData);
            toast.success("采购订单更新成功");
            setShowEditModal(false);
            loadOrders();
        } catch (err) {
            console.error("Failed to update order:", err);
            toast.error("更新采购订单失败");
        }
    };

    const handleDeleteOrder = async () => {
        try {
            await purchaseApi.delete(selectedOrder.id);
            toast.success("采购订单删除成功");
            setShowDeleteModal(false);
            setSelectedOrder(null);
            loadOrders();
        } catch (err) {
            console.error("Failed to delete order:", err);
            toast.error("删除采购订单失败");
        }
    };

    const handleSubmitApproval = async (order) => {
        try {
            await purchaseApi.submitApproval(order.id);
            toast.success("采购订单已提交审批");
            setShowDetailModal(false);
            setSelectedOrder(null);
            loadOrders();
        } catch (err) {
            console.error("Failed to submit approval:", err);
            toast.error("提交审批失败");
        }
    };

    const handleReceiveGoods = async () => {
        try {
            await purchaseApi.receiveGoods(selectedOrder.id, receiveData);
            toast.success("收货确认成功");
            setShowReceiveModal(false);
            setSelectedOrder(null);
            setReceiveData({
                received_items: [],
                notes: "",
                received_date: new Date().toISOString().split('T')[0]
            });
            loadOrders();
        } catch (err) {
            console.error("Failed to receive goods:", err);
            toast.error("收货确认失败");
        }
    };

    const handleExportData = () => {
        const csvData = sortedOrders.map((order) => ({
            "订单编号": order.id,
            "供应商": order.supplierName,
            "项目": order.projectName,
            "状态": ORDER_STATUS_CONFIGS[order.status]?.label,
            "金额": order.totalAmount,
            "采购员": order.buyer,
            "预计到货": order.expectedDate
        }));

        const csv = [
            Object.keys(csvData[0]).join(","),
            ...csvData.map((row) => Object.values(row).join(","))
        ].join("\n");

        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `采购订单_${new Date().toISOString().split("T")[0]}.csv`;
        link.click();
    };

    return {
        // State
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

        // Modal states
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

        // Dropdown data
        suppliers,
        projects,

        // Form states
        newOrder,
        setNewOrder,
        editOrder,
        setEditOrder,
        receiveData,
        setReceiveData,

        // Handlers
        handleCreateOrder,
        handleEditOrder,
        handleDeleteOrder,
        handleSubmitApproval,
        handleReceiveGoods,
        handleExportData,
        refresh: loadOrders
    };
}
