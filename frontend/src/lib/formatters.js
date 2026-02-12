/**
 * 统一格式化工具库
 *
 * 提供前端常用的格式化函数，包括：
 * - 货币格式化
 * - 日期格式化
 * - 数字格式化
 * - 状态标签生成
 * - 百分比格式化
 */

/**
 * 格式化货币
 *
 * @param {number|string} amount - 金额
 * @param {string} symbol - 货币符号（默认¥）
 * @param {number} decimals - 小数位数（默认2）
 * @returns {string} 格式化后的货币字符串
 */
export function formatCurrency(amount, symbol = '¥', decimals = 2) {
 if (amount === null || amount === undefined || amount === '') {
  return symbol + '0.00';
 }

 const num = typeof amount === 'string' ? parseFloat(amount) : amount;
 if (isNaN(num)) {
 return symbol + '0.00';
 }

 return symbol + num.toLocaleString('zh-CN', {
 minimumFractionDigits: decimals,
 maximumFractionDigits: decimals
 });
}

/**
 * 格式化货币（紧凑模式，自动转换万/亿单位）
 *
 * @param {number|string} value - 金额
 * @returns {string} 格式化后的货币字符串（如 ¥1.5万、¥2.30亿）
 */
export function formatCurrencyCompact(value) {
 if (value === null || value === undefined || value === '') {
 return '¥0';
 }

 const num = typeof value === 'string' ? parseFloat(value) : value;
 if (isNaN(num)) {
 return '¥0';
 }

 if (num >= 100000000) {
 return `¥${(num / 100000000).toFixed(2)}亿`;
 }
 if (num >= 10000) {
  return `¥${(num / 10000).toFixed(1)}万`;
 }
 return new Intl.NumberFormat('zh-CN', {
  style: 'currency',
 currency: 'CNY',
 minimumFractionDigits: 0,
 }).format(num);
}

/**
 * 格式化百分比
 *
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数（默认1）
 * @returns {string} 格式化后的百分比
 */
export function formatPercentage(value, decimals = 1) {
 if (value === null || value === undefined) {
  return '0%';
 }

  const num = typeof value === 'string' ? parseFloat(value) : value;
 if (isNaN(num)) {
 return '0%';
 }

 return (num * 100).toFixed(decimals) + '%';
}

/**
 * 格式化日期
 *
 * @param {string|Date} date - 日期
 * @param {string} format - 格式化选项（default/datetime/slash/short）
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'default') {
 if (!date) return '-';

 const d = typeof date === 'string' ? new Date(date) : date;
 if (isNaN(d.getTime())) return '-';

 const year = d.getFullYear();
 const month = String(d.getMonth() + 1).padStart(2, '0');
 const day = String(d.getDate()).padStart(2, '0');
 const hours = String(d.getHours()).padStart(2, '0');
 const minutes = String(d.getMinutes()).padStart(2, '0');

 switch (format) {
  case 'datetime':
  return `${year}-${month}-${day} ${hours}:${minutes}`;
  case 'slash':
  return `${year}/${month}/${day}`;
 case 'short':
   return `${month}-${day}`;
  case 'time':
  return `${hours}:${minutes}`;
 default:
 return `${year}-${month}-${day}`;
 }
}

/**
 * 格式化日期时间
 *
 * @param {string|Date} datetime - 日期时间
 * @returns {string} 格式化后的日期时间字符串
 */
export function formatDateTime(datetime) {
 return formatDate(datetime, 'datetime');
}

/**
 * 格式化时间
 *
 * @param {string|Date} time - 时间
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(time) {
 return formatDate(time, 'time');
}

/**
 * 生成状态标签配置
 *
 * @param {string} status - 状态值
 * @param {object} statusMap - 状态映射表（可选）
 * @returns {object} 状态标签配置
 */
export function getStatusBadge(status, statusMap = {}) {
 if (!status) return { variant: 'default', label: status };

 // 使用提供的映射表，否则使用默认映射
 const map = Object.keys(statusMap).length > 0 ? statusMap : DEFAULT_STATUS_MAP;
 return map[status] || { variant: 'default', label: status };
}

/**
 * 默认状态映射表
 */
const DEFAULT_STATUS_MAP = {
 // 项目状态
 'ACTIVE': { variant: 'success', label: '进行中' },
 'PENDING': { variant: 'warning', label: '待处理' },
  'COMPLETED': { variant: 'default', label: '已完成' },
 'CANCELLED': { variant: 'destructive', label: '已取消' },
 'ON_HOLD': { variant: 'secondary', label: '暂停' },

 // 审批状态
 'PENDING_APPROVAL': { variant: 'warning', label: '待审批' },
  'APPROVED': { variant: 'success', label: '已批准' },
 'REJECTED': { variant: 'destructive', label: '已拒绝' },

 // 任务状态
  'TODO': { variant: 'default', label: '待办' },
 'IN_PROGRESS': { variant: 'success', label: '进行中' },
  'DONE': { variant: 'default', label: '完成' },
 'FAILED': { variant: 'destructive', label: '失败' },

 // 工时状态
 'DRAFT': { variant: 'secondary', label: '草稿' },
 'SUBMITTED': { variant: 'primary', label: '已提交' },

 // 订单状态
 'PENDING_PAYMENT': { variant: 'warning', label: '待付款' },
 'PARTIAL_PAYMENT': { variant: 'primary', label: '部分付款' },
 'PAID': { variant: 'success', label: '已付款' },
 'OVERDUE': { variant: 'destructive', label: '逾期' },

 // 项目阶段
 'S1': { variant: 'info', label: '需求进入' },
 'S2': { variant: 'info', label: '方案设计' },
 'S3': { variant: 'info', label: '采购备料' },
 'S4': { variant: 'info', label: '加工制造' },
 'S5': { variant: 'info', label: '装配调试' },
 'S6': { variant: 'success', label: '出厂验收' },
  'S7': { variant: 'success', label: '包装发运' },
 'S8': { variant: 'success', label: '现场安装' },
 'S9': { variant: 'default', label: '质保结项' },

 // 预警级别
 'H1': { variant: 'success', label: '正常' },
 'H2': { variant: 'warning', label: '有风险' },
  'H3': { variant: 'destructive', label: '阻塞' },
 'H4': { variant: 'default', label: '已完结' },
};

/**
 * 格式化数字（千分位分隔）
 *
 * @param {number} num - 数字
 * @returns {string} 格式化后的数字
 */
export function formatNumber(num) {
 if (num === null || num === undefined || num === '') {
  return '0';
 }

 const n = typeof num === 'string' ? parseFloat(num) : num;
 if (isNaN(n)) {
  return '0';
 }

 return n.toLocaleString('zh-CN');
}

/**
 * 格式化文件大小
 *
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
 if (!bytes || bytes === 0) return '0 B';

 const k = 1024;
 const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
 const i = Math.floor(Math.log(bytes) / Math.log(k));

 return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化时长（秒转为可读格式）
 *
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的时长
 */
export function formatDuration(seconds) {
 if (!seconds || seconds === 0) return '0秒';

 const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
 const s = seconds % 60;

 const parts = [];
 if (h > 0) parts.push(`${h}小时`);
 if (m > 0) parts.push(`${m}分钟`);
 if (s > 0) parts.push(`${s}秒`);

  return parts.join('');
}

/**
 * 截断文本
 *
 * @param {string} text - 文本
 * @param {number} maxLength - 最大长度
 * @param {string} suffix - 后缀（默认...）
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 50, suffix = '...') {
 if (!text || text.length <= maxLength) {
  return text || '';
 }

 return text.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * 格式化工时（小时转为可读格式）
 *
 * @param {number} hours - 小时数
 * @returns {string} 格式化后的工时
 */
export function formatHours(hours) {
 if (!hours || hours === 0) return '0小时';

  const h = Math.floor(hours);
 const m = Math.round((hours - h) * 60);

 if (h > 0 && m > 0) {
  return `${h}小时${m}分钟`;
 } else if (h > 0) {
 return `${h}小时`;
 } else {
 return `${m}分钟`;
 }
}

// 导出所有格式化函数
export default {
 formatCurrency,
 formatCurrencyCompact,
 formatPercentage,
 formatDate,
 formatDateTime,
 formatTime,
 formatNumber,
 formatFileSize,
 formatDuration,
 formatHours,
 getStatusBadge,
 truncateText,
 DEFAULT_STATUS_MAP,
};
