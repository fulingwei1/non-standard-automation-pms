/**
 * 通用工具函数
 */
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * 合并className，支持条件类名
 * @param  {...any} inputs - 类名参数
 * @returns {string} 合并后的类名
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/**
 * 格式化日期
 * @param {string|Date} date - 日期
 * @param {string} format - 格式，默认 'YYYY-MM-DD'
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化货币
 * @param {number} value - 金额
 * @param {string} currency - 货币符号，默认 '¥'
 * @param {number} decimals - 小数位数，默认 2
 * @returns {string} 格式化后的货币字符串
 */
export function formatCurrency(value, currency = '¥', decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) return `${currency}0.00`
  const num = Number(value)
  return `${currency}${num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`
}

/**
 * 格式化时间
 * @param {string|Date} time - 时间
 * @param {string} format - 格式，默认 'HH:mm'
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(time, format = 'HH:mm') {
  if (!time) return ''
  const d = new Date(time)
  if (isNaN(d.getTime())) return time // 如果是纯时间字符串，直接返回

  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化百分比
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数，默认 1
 * @returns {string} 格式化后的百分比字符串
 */
export function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined || isNaN(value)) return '0%'
  return `${Number(value).toFixed(decimals)}%`
}

/**
 * 格式化数字
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数，默认 0
 * @returns {string} 格式化后的数字字符串
 */
export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined || isNaN(value)) return '0'
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/**
 * 截断文本
 * @param {string} text - 文本
 * @param {number} maxLength - 最大长度
 * @returns {string} 截断后的文本
 */
export function truncateText(text, maxLength = 50) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * 延迟执行
 * @param {number} ms - 延迟毫秒数
 * @returns {Promise} Promise对象
 */
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 防抖函数
 * @param {Function} func - 要执行的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait = 300) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 深拷贝对象
 * @param {any} obj - 要拷贝的对象
 * @returns {any} 拷贝后的对象
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  if (typeof obj === 'object') {
    const clonedObj = {}
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
  return obj
}

/**
 * 生成唯一ID
 * @returns {string} 唯一ID
 */
export function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

/**
 * 获取姓名首字母
 * @param {string} name - 姓名
 * @returns {string} 首字母
 */
export function getInitials(name) {
  if (!name) return ''
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) {
    // 中文名或单个词
    return name.slice(0, 2).toUpperCase()
  }
  // 英文名，取首字母
  return parts.map(p => p[0]).join('').toUpperCase().slice(0, 2)
}

/**
 * 项目阶段名称映射
 */
const STAGE_NAMES = {
  S1: '需求进入',
  S2: '方案设计',
  S3: '采购备料',
  S4: '加工制造',
  S5: '装配调试',
  S6: '出厂验收',
  S7: '包装发运',
  S8: '现场安装',
  S9: '质保结项',
}

/**
 * 获取阶段名称
 * @param {string} stageCode - 阶段代码 (S1-S9)
 * @returns {string} 阶段中文名称
 */
export function getStageName(stageCode) {
  if (!stageCode) return ''
  return STAGE_NAMES[stageCode.toUpperCase()] || stageCode
}
