/**
 * Delivery Management Components
 * 配送管理组件
 * 物流配送任务管理组件导出
 */

// 主要组件
export { default as DeliveryCard } from './DeliveryCard';
export { default as RouteOptimizer } from './RouteOptimizer';
export { default as TrackingMap } from './TrackingMap';

// 常量配置
export { default as deliveryConstants } from './deliveryConstants';

// 重新导出常量
export {
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
  sortByPriority,
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
  filterByDate
} from './deliveryConstants';

// 配置默认值
export const DEFAULT_DELIVERY_CONFIG = {
  autoRefresh: true,
  refreshInterval: 30000, // 30秒
  mapZoom: 1,
  mapCenter: { lat: 39.9042, lng: 116.4074 }, // 北京坐标
  routeOptimization: {
    algorithm: 'genetic',
    maxDistance: 200,
    maxDeliveries: 10,
    timeWindow: 2 // 小时
  }
};

// 配送任务状态变更
export const DELIVERY_STATUS_TRANSITIONS = {
  PENDING: ['PICKED_UP'],
  PICKED_UP: ['IN_TRANSIT', 'DELIVER_FAILED'],
  IN_TRANSIT: ['DELIVERED', 'DELIVER_FAILED', 'RETURNED'],
  DELIVERED: [],
  DELIVER_FAILED: ['RETURNED', 'CANCELLED'],
  RETURNED: ['DELIVERED', 'CANCELLED'],
  CANCELLED: []
};

// 配送任务优先级映射
export const DELIVERY_PRIORITY_WEIGHTS = {
  LOW: 1,
  NORMAL: 2,
  HIGH: 3,
  URGENT: 4,
  EXPRESS: 5
};

// 配送任务筛选器
export const DELIVERY_FILTERS = {
  status: {
    label: '配送状态',
    options: [
      { value: 'ALL', label: '全部', color: 'bg-slate-500' },
      { value: 'PENDING', label: '待配送', color: 'bg-slate-500' },
      { value: 'PICKED_UP', label: '已取货', color: 'bg-blue-500' },
      { value: 'IN_TRANSIT', label: '运输中', color: 'bg-orange-500' },
      { value: 'DELIVERED', label: '已送达', color: 'bg-green-500' },
      { value: 'DELIVER_FAILED', label: '配送失败', color: 'bg-red-500' }
    ]
  },
  priority: {
    label: '优先级',
    options: [
      { value: 'ALL', label: '全部' },
      { value: 'LOW', label: '低' },
      { value: 'NORMAL', label: '普通' },
      { value: 'HIGH', label: '高' },
      { value: 'URGENT', label: '紧急' },
      { value: 'EXPRESS', label: '特急' }
    ]
  },
  method: {
    label: '配送方式',
    options: [
      { value: 'ALL', label: '全部' },
      { value: 'SELF_PICKUP', label: '自提' },
      { value: 'STANDARD_DELIVERY', label: '标准配送' },
      { value: 'EXPRESS_DELIVERY', label: '快递配送' },
      { value: 'SPECIAL_DELIVERY', label: '专车配送' }
    ]
  },
  dateRange: {
    label: '时间范围',
    options: [
      { value: 'today', label: '今天' },
      { value: 'week', label: '本周' },
      { value: 'month', label: '本月' },
      { value: 'custom', label: '自定义' }
    ]
  }
};

// 配送任务API路径
export const DELIVERY_API_ENDPOINTS = {
  list: '/api/v1/deliveries',
  create: '/api/v1/deliveries',
  update: '/api/v1/deliveries/:id',
  delete: '/api/v1/deliveries/:id',
  track: '/api/v1/deliveries/:id/track',
  optimize: '/api/v1/deliveries/optimize',
  statistics: '/api/v1/deliveries/statistics',
  export: '/api/v1/deliveries/export'
};

// 配送任务导出格式
export const DELIVERY_EXPORT_FORMATS = {
  CSV: {
    label: 'CSV',
    mimeType: 'text/csv',
    extensions: ['.csv'],
    options: ['包含时间戳', '包含GPS坐标', '包含图片']
  },
  EXCEL: {
    label: 'Excel',
    mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    extensions: ['.xlsx'],
    options: ['多sheet', '包含公式', '包含图表']
  },
  PDF: {
    label: 'PDF',
    mimeType: 'application/pdf',
    extensions: ['.pdf'],
    options: ['包含地图', '包含签名', '包含图片']
  }
};