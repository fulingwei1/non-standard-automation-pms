/**
 * Purchase Order Components - 统一导出入口
 * 采购订单管理相关组件的集中导出
 */

// ==================== 常量配置 ====================
export {
  ORDER_STATUS,
  ORDER_URGENCY,
  ORDER_FILTER_OPTIONS,
  getOrderStatus,
  getOrderUrgency,
  formatOrderAmount,
  formatOrderDate,
  formatOrderDateTime,
  calculateProgress,
  getOrderStatusLabel,
  getUrgencyLabel,
  canEditOrder,
  canDeleteOrder,
  canSubmitOrder,
  canApproveOrder,
  canReceiveOrder,
  getProgressColor,
  calculateDelayDays,
  isDelayed,
} from "@/lib/constants/procurement";

// ==================== 组件 ====================
export { default as OrderCard } from "./OrderCard";
export { default as PurchaseOrderStats } from "./PurchaseOrderStats";
export { default as PurchaseOrderFilters } from "./PurchaseOrderFilters";
export { default as PurchaseOrderList } from "./PurchaseOrderList";

// ==================== 对话框组件 ====================
export { default as OrderDetailDialog } from "./OrderDetailDialog";
export { default as CreateEditOrderDialog } from "./CreateEditOrderDialog";
export { default as MaterialSelectDialog } from "./MaterialSelectDialog";
export { default as DeleteConfirmDialog } from "../../common/DeleteConfirmDialog";
export { default as ReceiveGoodsDialog } from "./ReceiveGoodsDialog";

// ==================== Hooks ====================
export { usePurchaseOrderData, usePurchaseOrderFilters } from "../hooks";
