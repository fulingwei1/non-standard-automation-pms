/**
 * Purchase Order Constants - 采购订单管理常量配置（统一主文件）
 *
 * 所有采购订单相关常量和工具函数的唯一主源。
 * 包含：订单状态、紧急程度、供应商状态、支付条款、
 * 审批状态、采购类别、运输方式、筛选选项、格式化函数等
 */

import {
 FileText,
 Clock,
 Truck,
 CheckCircle2,
 AlertTriangle,
 Trash2,
} from "lucide-react";

// ==================== 订单状态配置（富 UI 配置，含 lucide 图标） ====================
export const ORDER_STATUS = {
 draft: {
 label: "草稿",
  color: "bg-slate-500",
 textColor: "text-slate-400",
 bgColor: "bg-slate-500/10",
  borderColor: "border-slate-500/30",
  icon: FileText,
  value: "DRAFT",
 },
  pending: {
  label: "待收货",
 color: "bg-blue-500",
  textColor: "text-blue-400",
 bgColor: "bg-blue-500/10",
 borderColor: "border-blue-500/30",
  icon: Clock,
 value: "PENDING",
 },
 partial_received: {
 label: "部分到货",
 color: "bg-amber-500",
  textColor: "text-amber-400",
 bgColor: "bg-amber-500/10",
  borderColor: "border-amber-500/30",
 icon: Truck,
  value: "PARTIAL_RECEIVED",
 },
 completed: {
 label: "已完成",
 color: "bg-emerald-500",
 textColor: "text-emerald-400",
  bgColor: "bg-emerald-500/10",
 borderColor: "border-emerald-500/30",
  icon: CheckCircle2,
  value: "COMPLETED",
 },
 delayed: {
 label: "延期",
 color: "bg-red-500",
  textColor: "text-red-400",
  bgColor: "bg-red-500/10",
 borderColor: "border-red-500/30",
 icon: AlertTriangle,
  value: "DELAYED",
 },
 cancelled: {
 label: "已取消",
  color: "bg-slate-400",
 textColor: "text-slate-400",
 bgColor: "bg-slate-400/10",
 borderColor: "border-slate-400/30",
  icon: Trash2,
 value: "CANCELLED",
  },
};

// 别名：兼容 purchase-orders/PurchaseOrderCard.jsx 的导入
export const PURCHASE_ORDER_STATUS = ORDER_STATUS;

// ==================== 订单状态简化配置（用于统计/报表场景） ====================
export const ORDER_STATUS_CONFIGS = {
 draft: { label: "草稿", color: "bg-slate-500", icon: "FileText" },
 pending: { label: "待收货", color: "bg-blue-500", icon: "Clock" },
 partial_received: { label: "部分到货", color: "bg-amber-500", icon: "Truck" },
 completed: { label: "已完成", color: "bg-emerald-500", icon: "CheckCircle2" },
  delayed: { label: "延期", color: "bg-red-500", icon: "AlertTriangle" },
 cancelled: { label: "已取消", color: "bg-slate-400", icon: "Trash2" },
};

// ==================== 紧急程度配置 ====================
export const ORDER_URGENCY = {
 normal: {
 label: "普通",
 color: "text-slate-400",
  bgColor: "bg-slate-500/10",
  borderColor: "border-slate-500/30",
  value: "NORMAL",
 },
 urgent: {
 label: "加急",
  color: "text-amber-400",
 bgColor: "bg-amber-500/10",
  borderColor: "border-amber-500/30",
   value: "URGENT",
 },
 critical: {
 label: "特急",
  color: "text-red-400",
 bgColor: "bg-red-500/10",
  borderColor: "border-red-500/30",
 value: "CRITICAL",
 },
};

// 别名：兼容 purchase-orders/PurchaseOrderCard.jsx 的导入
export const PURCHASE_ORDER_URGENCY = ORDER_URGENCY;

// ==================== 紧急程度简化配置（用于统计/报表场景） ====================
export const ORDER_URGENCY_CONFIGS = {
 normal: { label: "普通", color: "text-slate-400" },
 urgent: { label: "加急", color: "text-amber-400" },
  critical: { label: "特急", color: "text-red-400" },
};

// ==================== 筛选选项 ====================
export const ORDER_FILTER_OPTIONS = {
 status: [
  { value: "all", label: "全部状态" },
 { value: "draft", label: "草稿" },
  { value: "pending", label: "待收货" },
  { value: "partial_received", label: "部分到货" },
 { value: "completed", label: "已完成" },
 { value: "delayed", label: "延期" },
  { value: "cancelled", label: "已取消" },
 ],
  urgency: [
  { value: "all", label: "全部紧急程度" },
 { value: "normal", label: "普通" },
 { value: "urgent", label: "加急" },
 { value: "critical", label: "特急" },
 ],
};

// 别名：兼容 purchase-orders/PurchaseOrderFilters.jsx 的导入
export const ORDER_STATUS_OPTIONS = ORDER_FILTER_OPTIONS.status;
export const ORDER_URGENCY_OPTIONS = ORDER_FILTER_OPTIONS.urgency;

// ==================== 供应商状态 ====================
export const SUPPLIER_STATUS = {
 ACTIVE: "active",
 INACTIVE: "inactive",
 SUSPENDED: "suspended",
};

export const SUPPLIER_STATUS_CONFIGS = {
 [SUPPLIER_STATUS.ACTIVE]: { label: "活跃", color: "bg-emerald-500" },
 [SUPPLIER_STATUS.INACTIVE]: { label: "非活跃", color: "bg-slate-400" },
  [SUPPLIER_STATUS.SUSPENDED]: { label: "暂停", color: "bg-red-500" },
};

// ==================== 支付条款 ====================
export const PAYMENT_TERMS = {
 NET30: "net30",
 NET60: "net60",
 NET90: "net90",
 COD: "cod",
 IMMEDIATE: "immediate",
};

export const PAYMENT_TERMS_CONFIGS = {
 [PAYMENT_TERMS.NET30]: { label: "30天", description: "30天内付款" },
 [PAYMENT_TERMS.NET60]: { label: "60天", description: "60天内付款" },
 [PAYMENT_TERMS.NET90]: { label: "90天", description: "90天内付款" },
 [PAYMENT_TERMS.COD]: { label: "货到付款", description: "收货时付款" },
 [PAYMENT_TERMS.IMMEDIATE]: { label: "立即付款", description: "下单时付款" },
};

// ==================== 审批状态 ====================
export const APPROVAL_STATUS = {
 PENDING: "pending",
 APPROVED: "approved",
 REJECTED: "rejected",
};

export const APPROVAL_STATUS_CONFIGS = {
  [APPROVAL_STATUS.PENDING]: { label: "待审批", color: "bg-amber-500" },
  [APPROVAL_STATUS.APPROVED]: { label: "已批准", color: "bg-emerald-500" },
 [APPROVAL_STATUS.REJECTED]: { label: "已拒绝", color: "bg-red-500" },
};

// ==================== 采购类别 ====================
export const PROCUREMENT_CATEGORIES = {
 RAW_MATERIALS: "raw_materials",
 COMPONENTS: "components",
 EQUIPMENT: "equipment",
 TOOLS: "tools",
 CONSUMABLES: "consumables",
 SERVICES: "services",
};

export const PROCUREMENT_CATEGORY_CONFIGS = {
 [PROCUREMENT_CATEGORIES.RAW_MATERIALS]: { label: "原材料", icon: "Package" },
 [PROCUREMENT_CATEGORIES.COMPONENTS]: { label: "零部件", icon: "Settings" },
 [PROCUREMENT_CATEGORIES.EQUIPMENT]: { label: "设备", icon: "Cpu" },
 [PROCUREMENT_CATEGORIES.TOOLS]: { label: "工具", icon: "Wrench" },
 [PROCUREMENT_CATEGORIES.CONSUMABLES]: { label: "耗材", icon: "Droplet" },
 [PROCUREMENT_CATEGORIES.SERVICES]: { label: "服务", icon: "Users" },
};

// ==================== 运输方式 ====================
export const SHIPPING_METHODS = {
 STANDARD: "standard",
 EXPRESS: "express",
 OVERNIGHT: "overnight",
 FREIGHT: "freight",
 PICKUP: "pickup",
};

export const SHIPPING_METHOD_CONFIGS = {
 [SHIPPING_METHODS.STANDARD]: { label: "标准快递", days: "3-5天" },
 [SHIPPING_METHODS.EXPRESS]: { label: "加急快递", days: "1-2天" },
 [SHIPPING_METHODS.OVERNIGHT]: { label: "次日达", days: "1天" },
 [SHIPPING_METHODS.FREIGHT]: { label: "货运", days: "5-10天" },
 [SHIPPING_METHODS.PICKUP]: { label: "自提", days: "0天" },
};

// ==================== 工具函数 ====================

/**
 * 获取订单状态配置
 */
export const getOrderStatus = (status) => {
 return ORDER_STATUS[status] || ORDER_STATUS.draft;
};

/**
 * 获取紧急程度配置
 */
export const getOrderUrgency = (urgency) => {
 return ORDER_URGENCY[urgency] || ORDER_URGENCY.normal;
};

/**
 * 格式化订单金额
 */
export const formatOrderAmount = (amount) => {
 if (!amount && amount !== 0) {return "¥0.00";}
 const numAmount = Number(amount);
 if (numAmount >= 10000) {
  return `¥${(numAmount / 10000).toFixed(2)}万`;
 }
 return `¥${numAmount.toFixed(2)}`;
};

/**
 * 格式化订单日期
 */
export const formatOrderDate = (dateStr) => {
 if (!dateStr) {return "--";}
 const date = new Date(dateStr);
 return date.toLocaleDateString("zh-CN");
};

/**
 * 格式化订单日期时间
 */
export const formatOrderDateTime = (dateStr) => {
 if (!dateStr) {return "--";}
 const date = new Date(dateStr);
 return date.toLocaleString("zh-CN");
};

/**
 * 计算到货进度百分比
 */
export const calculateProgress = (receivedCount, itemCount) => {
 if (!itemCount || itemCount === 0) {return 0;}
 return Math.min(100, Math.round((receivedCount / itemCount) * 100));
};

/**
 * 获取订单状态标签
 */
export const getOrderStatusLabel = (status) => {
 return getOrderStatus(status).label;
};

/**
 * 获取紧急程度标签
 */
export const getUrgencyLabel = (urgency) => {
 return getOrderUrgency(urgency).label;
};

/**
 * 判断订单是否可编辑
 */
export const canEditOrder = (status) => {
  return ["draft", "pending"].includes(status);
};

/**
 * 判断订单是否可删除
 */
export const canDeleteOrder = (status) => {
 return status === "draft";
};

/**
 * 判断订单是否可提交
 */
export const canSubmitOrder = (status) => {
 return status === "draft";
};

/**
 * 判断订单是否可审批
 */
export const canApproveOrder = (status) => {
 return status === "pending";
};

/**
 * 判断订单是否可收货
 */
export const canReceiveOrder = (status) => {
 return ["pending", "partial_received"].includes(status);
};

/**
 * 获取进度条颜色
 */
export const getProgressColor = (status, progress) => {
 if (status === "completed") {return "bg-emerald-500";}
  if (status === "delayed") {return "bg-red-500";}
 if (progress >= 80) {return "bg-emerald-500";}
 if (progress >= 50) {return "bg-blue-500";}
 return "bg-amber-500";
};

/**
 * 计算延期天数
 */
export const calculateDelayDays = (expectedDate) => {
 if (!expectedDate) {return 0;}
  const expected = new Date(expectedDate);
 const now = new Date();
 const diffTime = now - expected;
 return Math.max(0, Math.floor(diffTime / (1000 * 60 * 60 * 24)));
};

/**
 * 判断是否延期
 */
export const isDelayed = (expectedDate, status) => {
  if (["completed", "cancelled"].includes(status)) {return false;}
 if (!expectedDate) {return false;}
 return calculateDelayDays(expectedDate) > 0;
};

// ==================== 业务工具函数集 ====================
export const PurchaseOrderUtils = {
 // 获取订单状态配置
 getStatusConfig(status) {
  return ORDER_STATUS_CONFIGS[status] || ORDER_STATUS_CONFIGS.draft;
 },

 // 获取紧急程度配置
 getUrgencyConfig(urgency) {
 return ORDER_URGENCY_CONFIGS[urgency] || ORDER_URGENCY_CONFIGS.normal;
 },

 // 获取供应商状态配置
 getSupplierStatusConfig(status) {
 return SUPPLIER_STATUS_CONFIGS[status] || SUPPLIER_STATUS_CONFIGS[SUPPLIER_STATUS.ACTIVE];
 },

 // 获取支付条款配置
 getPaymentTermsConfig(terms) {
 return PAYMENT_TERMS_CONFIGS[terms] || PAYMENT_TERMS_CONFIGS[PAYMENT_TERMS.NET30];
 },

 // 获取审批状态配置
 getApprovalStatusConfig(status) {
  return APPROVAL_STATUS_CONFIGS[status] || APPROVAL_STATUS_CONFIGS[APPROVAL_STATUS.PENDING];
 },

  // 获取采购类别配置
 getCategoryConfig(category) {
 return PROCUREMENT_CATEGORY_CONFIGS[category] || PROCUREMENT_CATEGORY_CONFIGS[PROCUREMENT_CATEGORIES.RAW_MATERIALS];
  },

 // 获取运输方式配置
 getShippingMethodConfig(method) {
  return SHIPPING_METHOD_CONFIGS[method] || SHIPPING_METHOD_CONFIGS[SHIPPING_METHODS.STANDARD];
 },

 // 计算订单总金额
 calculateOrderTotal(items) {
 if (!items || !Array.isArray(items)) {return 0;}
  return items.reduce((total, item) => {
  return total + (parseFloat(item.price || 0) * parseFloat(item.qty || 0));
 }, 0);
 },

 // 计算已收货金额
 calculateReceivedAmount(items) {
  if (!items || !Array.isArray(items)) {return 0;}
 return items.reduce((total, item) => {
 return total + (parseFloat(item.price || 0) * parseFloat(item.received || 0));
 }, 0);
  },

 // 计算到货率
  calculateDeliveryRate(items) {
 if (!items || !Array.isArray(items)) {return 0;}
  const totalQty = items.reduce((sum, item) => sum + (parseFloat(item.qty || 0)), 0);
  const receivedQty = items.reduce((sum, item) => sum + (parseFloat(item.received || 0)), 0);
 return totalQty > 0 ? (receivedQty / totalQty * 100).toFixed(1) : 0;
 },

  // 判断订单是否延期
 isOrderDelayed(expectedDate, status) {
  if (!expectedDate || status === "completed" || status === "cancelled") {
 return false;
  }
 return new Date(expectedDate) < new Date();
 },

 // 计算延期天数
 getDelayedDays(expectedDate) {
 if (!expectedDate) {return 0;}
 const now = new Date();
 const expected = new Date(expectedDate);
 if (expected > now) {return 0;}
 const diffTime = Math.abs(now - expected);
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
 },

 // 获取订单优先级
 getOrderPriority(urgency, delayedDays) {
 if (urgency === "critical") {return 1;}
 if (urgency === "urgent") {return 2;}
 if (delayedDays > 0) {return 3;}
   return 4;
 },

 // 格式化金额
 formatCurrency(amount) {
  return new Intl.NumberFormat("zh-CN", {
 style: "currency",
  currency: "CNY",
  minimumFractionDigits: 2
 }).format(amount || 0);
 },

 // 格式化日期
 formatDate(date) {
 if (!date) {return "";}
 return new Date(date).toLocaleDateString("zh-CN");
  },

 // 生成订单编号
  generateOrderNumber() {
  const date = new Date();
 const year = date.getFullYear();
 const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
 const random = Math.floor(Math.random() * 1000).toString().padStart(3, "0");
  return `PO${year}${month}${day}${random}`;
 },

 // 验证订单数据
 validateOrder(order) {
  const errors = [];

  if (!order.supplier_id) {
  errors.push("请选择供应商");
 }

  if (!order.items || order.items.length === 0) {
  errors.push("请添加至少一个采购项");
 } else {
 order.items.forEach((item, index) => {
   if (!item.material_code) {
   errors.push(`第${index + 1}项：请选择物料`);
   }
   if (!item.qty || item.qty <= 0) {
  errors.push(`第${index + 1}项：请输入有效数量`);
  }
  if (!item.unit_price || item.unit_price <= 0) {
  errors.push(`第${index + 1}项：请输入有效单价`);
  }
 });
 }

  if (!order.expected_date) {
 errors.push("请选择预期到货日期");
 }

 return errors;
 },

 // 搜索订单
 searchOrders(orders, searchQuery) {
  if (!searchQuery || !orders) {return orders;}

  const query = searchQuery.toLowerCase();
 return orders.filter(order =>
 order.id?.toLowerCase().includes(query) ||
  order.supplierName?.toLowerCase().includes(query) ||
 order.buyer?.toLowerCase().includes(query)
 );
  },

 // 按状态过滤订单
 filterOrdersByStatus(orders, statusFilter) {
 if (!statusFilter || statusFilter === "all") {return orders;}
 return orders.filter(order => order.status === statusFilter);
 },

  // 排序订单
  sortOrders(orders, sortBy, sortOrder = "desc") {
 if (!sortBy) {return orders;}

  return [...orders].sort((a, b) => {
  let aValue = a[sortBy];
  let bValue = b[sortBy];

 // 处理日期类型
 if (sortBy.includes("date")) {
  aValue = new Date(aValue || 0);
 bValue = new Date(bValue || 0);
 }

 // 处理数字类型
 if (typeof aValue === "string" && !isNaN(aValue)) {
  aValue = parseFloat(aValue);
  bValue = parseFloat(bValue);
 }

  if (sortOrder === "asc") {
   return aValue > bValue ? 1 : -1;
  } else {
  return aValue < bValue ? 1 : -1;
  }
 });
 },

 // 获取审批工作流
  getApprovalWorkflow(orderAmount) {
 if (orderAmount >= 100000) {
 return [
   { role: "department_manager", label: "部门经理", required: true },
  { role: "finance_manager", label: "财务经理", required: true },
 { role: "general_manager", label: "总经理", required: true }
   ];
  } else if (orderAmount >= 50000) {
 return [
   { role: "department_manager", label: "部门经理", required: true },
  { role: "finance_manager", label: "财务经理", required: true }
  ];
 } else if (orderAmount >= 10000) {
 return [
   { role: "department_manager", label: "部门经理", required: true }
 ];
  } else {
 return [];
 }
 },

 // 检查是否需要审批
 requiresApproval(orderAmount) {
 return orderAmount >= 10000;
 },

 // 生成采购统计报告
 generateProcurementReport(orders, period = "month") {
  const now = new Date();
 const periodStart = new Date();

  switch (period) {
  case "week":
  periodStart.setDate(now.getDate() - 7);
  break;
  case "month":
 periodStart.setMonth(now.getMonth() - 1);
  break;
  case "quarter":
  periodStart.setMonth(now.getMonth() - 3);
   break;
   case "year":
  periodStart.setFullYear(now.getFullYear() - 1);
  break;
  }

 const filteredOrders = orders.filter(order =>
  new Date(order.created_date || order.createdAt) >= periodStart
 );

 return {
  totalOrders: filteredOrders.length,
  totalAmount: filteredOrders.reduce((sum, order) => sum + (order.totalAmount || 0), 0),
  averageAmount: filteredOrders.length > 0
 ? filteredOrders.reduce((sum, order) => sum + (order.totalAmount || 0), 0) / filteredOrders.length
  : 0,
  completedOrders: filteredOrders.filter(order => order.status === "completed").length,
 delayedOrders: filteredOrders.filter(order => order.status === "delayed").length,
  pendingOrders: filteredOrders.filter(order => order.status === "pending").length,
  byCategory: this.groupByCategory(filteredOrders),
 bySupplier: this.groupBySupplier(filteredOrders),
 };
  },

 // 按类别分组
 groupByCategory(orders) {
 const groups = {};
  orders.forEach(order => {
 const category = order.category || PROCUREMENT_CATEGORIES.RAW_MATERIALS;
  if (!groups[category]) {
  groups[category] = { count: 0, amount: 0 };
 }
  groups[category].count += 1;
  groups[category].amount += order.totalAmount || 0;
 });
 return groups;
 },

 // 按供应商分组
 groupBySupplier(orders) {
 const groups = {};
 orders.forEach(order => {
 const supplier = order.supplierName || "未知供应商";
  if (!groups[supplier]) {
 groups[supplier] = { count: 0, amount: 0 };
  }
 groups[supplier].count += 1;
 groups[supplier].amount += order.totalAmount || 0;
 });
 return groups;
 },
};

// ==================== 默认导出 ====================
export default {
 ORDER_STATUS,
 ORDER_STATUS_CONFIGS,
 ORDER_URGENCY,
 ORDER_URGENCY_CONFIGS,
 ORDER_FILTER_OPTIONS,
 PURCHASE_ORDER_STATUS,
 PURCHASE_ORDER_URGENCY,
 ORDER_STATUS_OPTIONS,
  ORDER_URGENCY_OPTIONS,
 SUPPLIER_STATUS,
 SUPPLIER_STATUS_CONFIGS,
 PAYMENT_TERMS,
 PAYMENT_TERMS_CONFIGS,
 APPROVAL_STATUS,
 APPROVAL_STATUS_CONFIGS,
 PROCUREMENT_CATEGORIES,
  PROCUREMENT_CATEGORY_CONFIGS,
 SHIPPING_METHODS,
 SHIPPING_METHOD_CONFIGS,
  PurchaseOrderUtils,
};
