/**
 * usePurchaseOrderData - 采购订单数据管理 Hook
 * 处理订单的获取、创建、更新、删除等操作
 */

import { useState, useEffect, useCallback } from "react";
import { purchaseApi, supplierApi, projectApi } from "../../../services/api";
import { toast } from "../../../components/ui/toast";
import { ORDER_STATUS, PurchaseOrderUtils } from "@/lib/constants/procurement";

export const usePurchaseOrderData = (initialFilters = {}) => {
  // 订单数据状态
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 下拉数据状态
  const [suppliers, setSuppliers] = useState([]);
  const [projects, setProjects] = useState([]);

  // 筛选状态
  const [filters, setFilters] = useState({
    status: initialFilters.status || "all",
    search: initialFilters.search || "",
  });

  /**
   * 加载采购订单列表
   */
  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        page_size: 1000,
        ...(filters.status && filters.status !== "all" && { status: filters.status }),
        ...(filters.search && { search: filters.search }),
      };

      const response = await purchaseApi.list(params);
      let ordersData = response.data?.items || response.data?.items || response.data || [];

      // 转换 API 响应为组件格式
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
          urgency: order.urgency || ORDER_STATUS.NORMAL,
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
            received: item.received_qty || 0,
          })),
          _original: order,
        };
      });

      // 计算已收货金额并检查延期订单
      transformedOrders.forEach((order) => {
        order.receivedAmount = PurchaseOrderUtils.calculateReceivedAmount(order.items);

        // 检查延期订单
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
      toast.error("加载采购订单失败");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  /**
   * 加载下拉数据（供应商、项目）
   */
  const loadDropdownData = useCallback(async () => {
    try {
      const [suppliersRes, projectsRes] = await Promise.all([
        supplierApi.list({ page_size: 1000 }),
        projectApi.list({ page_size: 1000 }),
      ]);

      const suppliersData = suppliersRes.data?.items || suppliersRes.data?.items || suppliersRes.data || [];
      const projectsData = projectsRes.data?.items || projectsRes.data?.items || projectsRes.data || [];

      setSuppliers(suppliersData);
      setProjects(projectsData);
    } catch (err) {
      console.error("Failed to load dropdown data:", err);
      setSuppliers([]);
      setProjects([]);
    }
  }, []);

  /**
   * 创建新采购订单
   */
  const createOrder = useCallback(async (orderData) => {
    try {
      const errors = PurchaseOrderUtils.validateOrder(orderData);
      if (errors.length > 0) {
        toast.error(errors.join(", "));
        return { success: false, errors };
      }

      const payload = {
        ...orderData,
        id: PurchaseOrderUtils.generateOrderNumber(),
        total_amount: PurchaseOrderUtils.calculateOrderTotal(orderData.items),
        expected_date: orderData.expected_date,
      };

      await purchaseApi.create(payload);
      toast.success("采购订单创建成功");
      loadOrders();
      return { success: true };
    } catch (err) {
      console.error("Failed to create order:", err);
      toast.error("创建采购订单失败");
      return { success: false, error: err };
    }
  }, [loadOrders]);

  /**
   * 更新采购订单
   */
  const updateOrder = useCallback(async (orderId, orderData) => {
    try {
      const errors = PurchaseOrderUtils.validateOrder(orderData);
      if (errors.length > 0) {
        toast.error(errors.join(", "));
        return { success: false, errors };
      }

      const payload = {
        ...orderData,
        total_amount: PurchaseOrderUtils.calculateOrderTotal(orderData.items),
      };

      await purchaseApi.update(orderId, payload);
      toast.success("采购订单更新成功");
      loadOrders();
      return { success: true };
    } catch (err) {
      console.error("Failed to update order:", err);
      toast.error("更新采购订单失败");
      return { success: false, error: err };
    }
  }, [loadOrders]);

  /**
   * 删除采购订单
   */
  const deleteOrder = useCallback(async (orderId) => {
    try {
      await purchaseApi.delete(orderId);
      toast.success("采购订单删除成功");
      loadOrders();
      return { success: true };
    } catch (err) {
      console.error("Failed to delete order:", err);
      toast.error("删除采购订单失败");
      return { success: false, error: err };
    }
  }, [loadOrders]);

  /**
   * 提交审批
   */
  const submitApproval = useCallback(async (orderId) => {
    try {
      await purchaseApi.submitApproval(orderId);
      toast.success("采购订单已提交审批");
      loadOrders();
      return { success: true };
    } catch (err) {
      console.error("Failed to submit approval:", err);
      toast.error("提交审批失败");
      return { success: false, error: err };
    }
  }, [loadOrders]);

  /**
   * 确认收货
   */
  const receiveGoods = useCallback(async (orderId, receiveData) => {
    try {
      await purchaseApi.receiveGoods(orderId, receiveData);
      toast.success("收货确认成功");
      loadOrders();
      return { success: true };
    } catch (err) {
      console.error("Failed to receive goods:", err);
      toast.error("收货确认失败");
      return { success: false, error: err };
    }
  }, [loadOrders]);

  // 初始加载
  useEffect(() => {
    loadOrders();
    loadDropdownData();
  }, []);

  // 当筛选条件变化时重新加载
  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  // 计算统计数据
  const stats = {
    total: orders.length,
    pending: orders.filter((o) => o.status === ORDER_STATUS.PENDING).length,
    delayed: orders.filter((o) => o.status === ORDER_STATUS.DELAYED).length,
    totalAmount: orders.reduce((sum, o) => sum + (o.totalAmount || 0), 0),
  };

  return {
    // 数据
    orders,
    suppliers,
    projects,
    stats,
    // 状态
    loading,
    error,
    filters,
    // 方法
    setFilters,
    loadOrders,
    loadDropdownData,
    createOrder,
    updateOrder,
    deleteOrder,
    submitApproval,
    receiveGoods,
  };
};
