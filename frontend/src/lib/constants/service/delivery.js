// === Migrated from components/delivery-management/deliveryConstants.js ===
/**
 * Delivery Management Configuration Constants
 * 配送管理配置常量
 * 物流配送任务管理配置常量
 *
 * This is the main delivery constants file.
 * deliveryManagementConstants.js re-exports from this file.
 */

// 配送状态配置
export const deliveryStatusConfigs = {
 PENDING: { label: "待配送", color: "bg-slate-500", textColor: "text-slate-50", icon: "📦" },
 PICKED_UP: { label: "已取货", color: "bg-blue-500", textColor: "text-blue-50", icon: "🚚" },
 IN_TRANSIT: { label: "运输中", color: "bg-orange-500", textColor: "text-orange-50", icon: "🛣️" },
 DELIVERED: { label: "已送达", color: "bg-green-500", textColor: "text-green-50", icon: "✅" },
 DELIVER_FAILED: { label: "配送失败", color: "bg-red-500", textColor: "text-red-50", icon: "❌" },
 RETURNED: { label: "已退回", color: "bg-gray-500", textColor: "text-gray-50", icon: "↩️" },
 CANCELLED: { label: "已取消", color: "bg-gray-500", textColor: "text-gray-50", icon: "🚫" },
};

// 配送优先级配置
export const deliveryPriorityConfigs = {
 LOW: { label: "低", color: "bg-slate-500", textColor: "text-slate-50", value: 1 },
 NORMAL: { label: "普通", color: "bg-blue-500", textColor: "text-blue-50", value: 2 },
 HIGH: { label: "高", color: "bg-orange-500", textColor: "text-orange-50", value: 3 },
 URGENT: { label: "紧急", color: "bg-red-500", textColor: "text-red-50", value: 4 },
 EXPRESS: { label: "特急", color: "bg-purple-500", textColor: "text-purple-50", value: 5 },
};

// 配送方式配置
export const deliveryMethodConfigs = {
  SELF_PICKUP: { label: "自提", color: "bg-blue-500", textColor: "text-blue-50", icon: "🏢" },
 STANDARD_DELIVERY: { label: "标准配送", color: "bg-green-500", textColor: "text-green-50", icon: "🚚" },
 EXPRESS_DELIVERY: { label: "快递配送", color: "bg-orange-500", textColor: "text-orange-50", icon: "🏃" },
 SPECIAL_DELIVERY: { label: "专车配送", color: "bg-purple-500", textColor: "text-purple-50", icon: "🚗" },
 OVERNIGHT: { label: "隔夜达", color: "bg-red-500", textColor: "text-red-50", icon: "🌙" },
};

// 配送类型配置
export const deliveryTypeConfigs = {
 NORMAL: { label: "常规配送", color: "bg-blue-500", textColor: "text-blue-50" },
 RETURN: { label: "退货配送", color: "bg-orange-500", textColor: "text-orange-50" },
 EXCHANGE: { label: "换货配送", color: "bg-purple-500", textColor: "text-purple-50" },
 REPLACEMENT: { label: "补货配送", color: "bg-green-500", textColor: "text-green-50" },
 SAMPLE: { label: "样品配送", color: "bg-amber-500", textColor: "text-amber-50" },
  URGENT: { label: "紧急配送", color: "bg-red-500", textColor: "text-red-50" },
};

// 配送阶段配置
export const deliveryStageConfigs = {
 PREPARING: { label: "备货中", color: "bg-slate-500", textColor: "text-slate-50" },
 READY: { label: "已备货", color: "bg-blue-500", textColor: "text-blue-50" },
  DISPATCHED: { label: "已调度", color: "bg-orange-500", textColor: "text-orange-50" },
  LOADING: { label: "装车中", color: "bg-amber-500", textColor: "text-amber-50" },
 TRANSPORTING: { label: "运输中", color: "bg-purple-500", textColor: "text-purple-50" },
 UNLOADING: { label: "卸货中", color: "bg-indigo-500", textColor: "text-indigo-50" },
 COMPLETED: { label: "已完成", color: "bg-green-500", textColor: "text-green-50" },
 FAILED: { label: "已失败", color: "bg-red-500", textColor: "text-red-50" },
};

// 配送车辆状态配置
export const vehicleStatusConfigs = {
 AVAILABLE: { label: "可用", color: "bg-green-500", textColor: "text-green-50" },
 IN_USE: { label: "使用中", color: "bg-blue-500", textColor: "text-blue-50" },
 MAINTENANCE: { label: "维护中", color: "bg-orange-500", textColor: "text-orange-50" },
 REPAIRING: { label: "维修中", color: "bg-red-500", textColor: "text-red-50" },
 OFFLINE: { label: "离线", color: "bg-gray-500", textColor: "text-gray-50" },
};

// 配送司机状态配置
export const driverStatusConfigs = {
 ONLINE: { label: "在线", color: "bg-green-500", textColor: "text-green-50" },
 BUSY: { label: "忙碌", color: "bg-orange-500", textColor: "text-orange-50" },
 OFFLINE: { label: "离线", color: "bg-gray-500", textColor: "text-gray-50" },
 BREAK: { label: "休息", color: "bg-blue-500", textColor: "text-blue-50" },
};

// 配送异常类型配置
export const exceptionTypeConfigs = {
 DELAY: { label: "延迟", color: "bg-orange-500", textColor: "text-orange-50", icon: "⏰" },
 DAMAGE: { label: "损坏", color: "bg-red-500", textColor: "text-red-50", icon: "💥" },
 LOSS: { label: "丢失", color: "bg-red-500", textColor: "text-red-50", icon: "❓" },
 WRONG_ADDRESS: { label: "地址错误", color: "bg-orange-500", textColor: "text-orange-50", icon: "📍" },
 CUSTOMER_UNAVAILABLE: { label: "客户不在", color: "bg-orange-500", textColor: "text-orange-50", icon: "👤" },
 VEHICLE_ISSUE: { label: "车辆问题", color: "bg-red-500", textColor: "text-red-50", icon: "🚗" },
 DRIVER_ISSUE: { label: "司机问题", color: "bg-red-500", textColor: "text-red-50", icon: "🚙" },
  WEATHER: { label: "天气原因", color: "bg-blue-500", textColor: "text-blue-50", icon: "🌧️" },
 TRAFFIC: { label: "交通拥堵", color: "bg-orange-500", textColor: "text-orange-50", icon: "🚦" },
};

// 配送统计类型配置
export const statsTypeConfigs = {
 TOTAL_DELIVERIES: { label: "总配送量", color: "bg-blue-500", textColor: "text-blue-50" },
 SUCCESS_RATE: { label: "成功率", color: "bg-green-500", textColor: "text-green-50" },
 AVG_DELIVERY_TIME: { label: "平均配送时间", color: "bg-amber-500", textColor: "text-amber-50" },
 ON_TIME_RATE: { label: "准时率", color: "bg-purple-500", textColor: "text-purple-50" },
 DELAYED_DELIVERIES: { label: "延迟配送", color: "bg-orange-500", textColor: "text-orange-50" },
 FAILED_DELIVERIES: { label: "失败配送", color: "bg-red-500", textColor: "text-red-50" },
 CUSTOMER_SATISFACTION: { label: "客户满意度", color: "bg-cyan-500", textColor: "text-cyan-50" },
 VEHICLE_UTILIZATION: { label: "车辆利用率", color: "bg-indigo-500", textColor: "text-indigo-50" },
};

// 导出类型配置
export const exportTypeConfigs = {
 CSV: { label: "CSV", color: "bg-green-500", textColor: "text-green-50", icon: "📊" },
 EXCEL: { label: "Excel", color: "bg-blue-500", textColor: "text-blue-50", icon: "📈" },
 PDF: { label: "PDF", color: "bg-red-500", textColor: "text-red-50", icon: "📄" },
 JSON: { label: "JSON", color: "bg-purple-500", textColor: "text-purple-50", icon: "🔧" },
};

// 时间配置
export const timeSlotConfigs = {
 MORNING: { label: "上午 (08:00-12:00)", color: "bg-blue-500", textColor: "text-blue-50" },
 AFTERNOON: { label: "下午 (13:00-17:00)", color: "bg-green-500", textColor: "text-green-50" },
 EVENING: { label: "傍晚 (17:00-20:00)", color: "bg-orange-500", textColor: "text-orange-50" },
 NIGHT: { label: "夜间 (20:00-23:00)", color: "bg-purple-500", textColor: "text-purple-50" },
 ANYTIME: { label: "全天", color: "bg-slate-500", textColor: "text-slate-50" },
};

// Tab 配置
export const tabConfigs = [
 { value: "overview", label: "配送总览", icon: "📊" },
 { value: "tasks", label: "配送任务", icon: "📦" },
 { value: "vehicles", label: "车辆管理", icon: "🚚" },
 { value: "drivers", label: "司机管理", icon: "👨‍💼" },
 { value: "routes", label: "路径优化", icon: "🛣️" },
 { value: "tracking", label: "实时追踪", icon: "📍" },
 { value: "analytics", label: "数据分析", icon: "📈" },
  { value: "exceptions", label: "异常处理", icon: "⚠️" },
];

// 工具函数
export const getStatusConfig = (status) => {
 return deliveryStatusConfigs[status] || deliveryStatusConfigs.PENDING;
};

export const getPriorityConfig = (priority) => {
 return deliveryPriorityConfigs[priority] || deliveryPriorityConfigs.NORMAL;
};

export const getMethodConfig = (method) => {
 return deliveryMethodConfigs[method] || deliveryMethodConfigs.STANDARD_DELIVERY;
};

export const getTypeConfig = (type) => {
 return deliveryTypeConfigs[type] || deliveryTypeConfigs.NORMAL;
};

export const getStageConfig = (stage) => {
 return deliveryStageConfigs[stage] || deliveryStageConfigs.PREPARING;
};

export const getVehicleStatusConfig = (status) => {
 return vehicleStatusConfigs[status] || vehicleStatusConfigs.OFFLINE;
};

export const getDriverStatusConfig = (status) => {
 return driverStatusConfigs[status] || driverStatusConfigs.OFFLINE;
};

export const getExceptionConfig = (type) => {
 return exceptionTypeConfigs[type] || exceptionTypeConfigs.DELAY;
};

export const getStatsConfig = (type) => {
 return statsTypeConfigs[type] || statsTypeConfigs.TOTAL_DELIVERIES;
};

export const getTimeSlotConfig = (slot) => {
 return timeSlotConfigs[slot] || timeSlotConfigs.ANYTIME;
};

export const formatStatus = (status) => {
  return getStatusConfig(status).label;
};

export const formatPriority = (priority) => {
 return getPriorityConfig(priority).label;
};

export const formatMethod = (method) => {
 return getMethodConfig(method).label;
};

export const formatType = (type) => {
 return getTypeConfig(type).label;
};

export const formatStage = (stage) => {
 return getStageConfig(stage).label;
};

export const getPriorityValue = (item) => {
 if (!item.priority) {return 0;}
 return getPriorityConfig(item.priority).value;
};

// 排序函数
export const sortByDeliveryPriority = (a, b) => {
 return getPriorityValue(b) - getPriorityValue(a);
};

export const sortByStatus = (a, b) => {
 const statusOrder = ['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'DELIVER_FAILED', 'RETURNED', 'CANCELLED'];
 const aIndex = statusOrder.indexOf(a.status);
  const bIndex = statusOrder.indexOf(b.status);
  return aIndex - bIndex;
};

export const sortByDeliveryTime = (a, b) => {
 const aTime = a.planned_delivery_time || a.created_at;
 const bTime = b.planned_delivery_time || b.created_at;
 return new Date(bTime) - new Date(aTime);
};

// 验证函数
export const isValidStatus = (status) => {
 return Object.keys(deliveryStatusConfigs).includes(status);
};

export const isValidPriority = (priority) => {
 return Object.keys(deliveryPriorityConfigs).includes(priority);
};

export const isValidMethod = (method) => {
 return Object.keys(deliveryMethodConfigs).includes(method);
};

export const isValidType = (type) => {
 return Object.keys(deliveryTypeConfigs).includes(type);
};

export const isValidStage = (stage) => {
 return Object.keys(deliveryStageConfigs).includes(stage);
};

// 过滤函数
export const filterByStatus = (items, status) => {
 return items.filter(item => item.status === status);
};

export const filterByPriority = (items, priority) => {
 return items.filter(item => item.priority === priority);
};

export const filterByMethod = (items, method) => {
 return items.filter(item => item.delivery_method === method);
};

export const filterByType = (items, type) => {
 return items.filter(item => item.delivery_type === type);
};

export const filterByDate = (items, startDate, endDate) => {
 return items.filter(item => {
 const deliveryDate = new Date(item.planned_delivery_time || item.created_at);
 return deliveryDate >= startDate && deliveryDate <= endDate;
 });
};

// ==================== 兼容导出（来自 deliveryManagementConstants）====================

export const DELIVERY_STATUS = {
  PENDING: { value: 'pending', label: '待发货', color: '#faad14' },
 PREPARING: { value: 'preparing', label: '准备中', color: '#1890ff' },
  SHIPPED: { value: 'shipped', label: '已发货', color: '#722ed1' },
 IN_TRANSIT: { value: 'in_transit', label: '在途', color: '#13c2c2' },
  DELIVERED: { value: 'delivered', label: '已送达', color: '#52c41a' },
 CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' }
};

export const DELIVERY_PRIORITY = {
 URGENT: { value: 'urgent', label: '紧急', color: '#ff4d4f' },
 HIGH: { value: 'high', label: '高', color: '#fa8c16' },
  NORMAL: { value: 'normal', label: '普通', color: '#1890ff' },
 LOW: { value: 'low', label: '低', color: '#52c41a' }
};

export const SHIPPING_METHODS = {
 EXPRESS: { value: 'express', label: '快递', days: '1-3天' },
 STANDARD: { value: 'standard', label: '标准物流', days: '3-7天' },
  FREIGHT: { value: 'freight', label: '货运', days: '7-15天' },
 SELF_PICKUP: { value: 'self_pickup', label: '自提', days: '0天' }
};

export const PACKAGE_TYPES = {
 STANDARD: { value: 'standard', label: '标准包装' },
 FRAGILE: { value: 'fragile', label: '易碎品包装' },
 LIQUID: { value: 'liquid', label: '液体包装' },
 OVERSIZE: { value: 'oversize', label: '超大件包装' }
};

export const DELIVERY_DEFAULT = {
 deliveryStatusConfigs,
 deliveryPriorityConfigs,
 deliveryMethodConfigs,
 deliveryTypeConfigs,
 deliveryStageConfigs,
 vehicleStatusConfigs,
 driverStatusConfigs,
 exceptionTypeConfigs,
 statsTypeConfigs,
 exportTypeConfigs,
  timeSlotConfigs,
 tabConfigs,
 getStatusConfig,
 getPriorityConfig,
 getMethodConfig,
 getTypeConfig,
  getStageConfig,
 getVehicleStatusConfig,
 getDriverStatusConfig,
 getExceptionConfig,
 getStatsConfig,
 getTimeSlotConfig,
 formatStatus,
 formatPriority,
 formatMethod,
 formatType,
  formatStage,
  getPriorityValue,
 sortByDeliveryPriority,
 sortByPriority: sortByDeliveryPriority,
 sortByStatus,
  sortByDeliveryTime,
 isValidStatus,
 isValidPriority,
  isValidMethod,
 isValidType,
 isValidStage,
 filterByStatus,
 filterByPriority,
 filterByMethod,
 filterByType,
 filterByDate,
 // 兼容导出
  DELIVERY_STATUS,
 DELIVERY_PRIORITY,
 SHIPPING_METHODS,
 PACKAGE_TYPES,
};
