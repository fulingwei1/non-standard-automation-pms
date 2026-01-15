/**
 * 采购分析组件配置常量
 */

// 时间范围配置
export const TIME_RANGE_OPTIONS = [
  { value: '3month', label: '最近3个月' },
  { value: '6month', label: '最近6个月' },
  { value: 'year', label: '最近1年' }
];

// 时间范围标签映射
export const TIME_RANGE_LABELS = {
  '3month': '最近3个月',
  '6month': '最近6个月',
  'year': '最近1年'
};

// 分析 Tab 配置
export const ANALYSIS_TABS = [
  { value: 'cost-trend', label: '成本趋势' },
  { value: 'price-fluctuation', label: '价格波动' },
  { value: 'delivery-performance', label: '交期准时率' },
  { value: 'request-efficiency', label: '采购时效' },
  { value: 'quality-rate', label: '质量合格率' }
];

// 统计卡片配置
export const STATS_CARD_CONFIGS = {
  // 成本趋势统计卡片
  costTrend: [
    { key: 'total_amount', label: '期间采购总额', icon: 'DollarSign', color: 'emerald' },
    { key: 'total_orders', label: '期间订单数', icon: 'ShoppingCart', color: 'blue' },
    { key: 'avg_monthly_amount', label: '月均采购额', icon: 'BarChart3', color: 'purple' },
    { key: 'max_month_amount', label: '最高月采购额', icon: 'TrendingUp', color: 'amber' }
  ],
  // 价格波动统计卡片
  priceFluctuation: [
    { key: 'total_materials', label: '分析物料数', icon: 'BarChart3', color: 'blue' },
    { key: 'high_volatility_count', label: '高波动物料数', icon: 'AlertTriangle', color: 'amber', subtitle: '波动率 > 20%' },
    { key: 'avg_volatility', label: '平均波动率', icon: 'TrendingUp', color: 'purple', suffix: '%' }
  ],
  // 交期准时率统计卡片
  deliveryPerformance: [
    { key: 'total_suppliers', label: '供应商总数', icon: 'Truck', color: 'blue' },
    { key: 'avg_on_time_rate', label: '平均准时率', icon: 'Award', color: 'emerald', suffix: '%' },
    { key: 'total_delayed_orders', label: '延期订单数', icon: 'AlertTriangle', color: 'amber' },
    { key: 'on_time_rate_rating', label: '准时交货率', icon: 'Clock', color: 'purple', isRating: true }
  ],
  // 采购时效统计卡片
  requestEfficiency: [
    { key: 'total_requests', label: '申请总数', icon: 'ShoppingCart', color: 'blue' },
    { key: 'processed_count', label: '已处理', icon: 'Award', color: 'emerald' },
    { key: 'pending_count', label: '待处理', icon: 'Clock', color: 'amber' },
    { key: 'within_24h_rate', label: '24h处理率', icon: 'TrendingUp', color: 'purple', suffix: '%' }
  ],
  // 质量合格率统计卡片
  qualityRate: [
    { key: 'total_suppliers', label: '供应商总数', icon: 'Truck', color: 'blue' },
    { key: 'avg_pass_rate', label: '平均合格率', icon: 'Award', color: 'emerald', suffix: '%' },
    { key: 'high_quality_suppliers', label: '高质量供应商', icon: 'TrendingUp', color: 'emerald', subtitle: '≥98%' },
    { key: 'low_quality_suppliers', label: '需关注供应商', icon: 'AlertTriangle', color: 'amber', subtitle: '<90%' }
  ]
};

// 图标映射
export const ICON_MAP = {
  DollarSign: 'DollarSign',
  ShoppingCart: 'ShoppingCart',
  Truck: 'Truck',
  Award: 'Award',
  Clock: 'Clock',
  AlertTriangle: 'AlertTriangle',
  BarChart3: 'BarChart3',
  TrendingUp: 'TrendingUp',
  TrendingDown: 'TrendingDown',
  LineChart: 'LineChart',
  PieChart: 'PieChart'
};

// 颜色映射
export const COLOR_MAP = {
  emerald: 'text-emerald-500',
  blue: 'text-blue-500',
  purple: 'text-purple-500',
  amber: 'text-amber-500',
  red: 'text-red-500'
};

/**
 * 根据时间范围获取日期范围
 * @param {string} range - 时间范围 (3month, 6month, year)
 * @param {string} type - 类型 (start, end)
 * @returns {string} YYYY-MM-DD 格式的日期
 */
export function getDateByRange(range, type) {
  const today = new Date();
  if (range === '3month') {
    const start = new Date(today);
    start.setMonth(today.getMonth() - 3);
    return type === 'start' ? start.toISOString().split('T')[0] : today.toISOString().split('T')[0];
  } else if (range === '6month') {
    const start = new Date(today);
    start.setMonth(today.getMonth() - 6);
    return type === 'start' ? start.toISOString().split('T')[0] : today.toISOString().split('T')[0];
  } else if (range === 'year') {
    const start = new Date(today);
    start.setFullYear(today.getFullYear() - 1);
    return type === 'start' ? start.toISOString().split('T')[0] : today.toISOString().split('T')[0];
  }
  return today.toISOString().split('T')[0];
}

/**
 * 格式化金额
 * @param {number} amount - 金额
 * @returns {string} 格式化后的金额字符串
 */
export function formatAmount(amount) {
  if (!amount) return '¥0';
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(1)}万`;
  }
  return `¥${amount.toLocaleString()}`;
}

/**
 * 获取准时率评级
 * @param {number} rate - 准时率百分比
 * @returns {object} { label, color }
 */
export function getOnTimeRateRating(rate) {
  if (rate >= 90) {
    return { label: '优秀', color: 'text-emerald-400' };
  } else if (rate >= 75) {
    return { label: '良好', color: 'text-amber-400' };
  } else {
    return { label: '需改进', color: 'text-red-400' };
  }
}

/**
 * 获取质量合格率 Badge 颜色
 * @param {number} rate - 合格率百分比
 * @returns {string} Tailwind CSS 类名
 */
export function getQualityRateBadgeColor(rate) {
  if (rate >= 98) return 'bg-emerald-500';
  if (rate >= 90) return 'bg-amber-500';
  return 'bg-red-500';
}

/**
 * 获取准时率 Badge 颜色
 * @param {number} rate - 准时率百分比
 * @returns {string} Tailwind CSS 类名
 */
export function getOnTimeRateBadgeColor(rate) {
  if (rate >= 90) return 'bg-emerald-500';
  if (rate >= 75) return 'bg-amber-500';
  return 'bg-red-500';
}
