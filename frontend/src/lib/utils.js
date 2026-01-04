import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind CSS classes with conflict resolution
 * @param  {...any} inputs - Class names to merge
 * @returns {string} - Merged class string
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/**
 * Format date to localized string
 * @param {Date|string} date - Date to format
 * @param {Object} options - Intl.DateTimeFormat options
 * @returns {string} - Formatted date string
 */
export function formatDate(date, options = {}) {
  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    ...options,
  }
  return new Date(date).toLocaleDateString('zh-CN', defaultOptions)
}

/**
 * Format date with time
 * @param {Date|string} date - Date to format
 * @returns {string} - Formatted datetime string
 */
export function formatDateTime(date) {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format relative time (e.g., "3 hours ago")
 * @param {Date|string} date - Date to format
 * @returns {string} - Relative time string
 */
export function formatRelativeTime(date) {
  const now = new Date()
  const then = new Date(date)
  const seconds = Math.floor((now - then) / 1000)

  const intervals = [
    { label: '年', seconds: 31536000 },
    { label: '个月', seconds: 2592000 },
    { label: '天', seconds: 86400 },
    { label: '小时', seconds: 3600 },
    { label: '分钟', seconds: 60 },
  ]

  for (const interval of intervals) {
    const count = Math.floor(seconds / interval.seconds)
    if (count >= 1) {
      return `${count} ${interval.label}前`
    }
  }

  return '刚刚'
}

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code
 * @returns {string} - Formatted currency string
 */
export function formatCurrency(amount, currency = 'CNY') {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount)
}

/**
 * Format number with thousand separators
 * @param {number} num - Number to format
 * @returns {string} - Formatted number string
 */
export function formatNumber(num) {
  return new Intl.NumberFormat('zh-CN').format(num)
}

/**
 * Format percentage
 * @param {number} value - Value (0-100)
 * @param {number} decimals - Decimal places
 * @returns {string} - Formatted percentage string
 */
export function formatPercent(value, decimals = 0) {
  return `${value.toFixed(decimals)}%`
}

/**
 * Generate a unique ID
 * @returns {string} - Unique ID
 */
export function generateId() {
  return Math.random().toString(36).substring(2, 9)
}

/**
 * Debounce a function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} - Debounced function
 */
export function debounce(func, wait) {
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
 * Throttle a function
 * @param {Function} func - Function to throttle
 * @param {number} limit - Limit time in ms
 * @returns {Function} - Throttled function
 */
export function throttle(func, limit) {
  let inThrottle
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * Get initials from name
 * @param {string} name - Full name
 * @returns {string} - Initials (1-2 characters)
 */
export function getInitials(name) {
  if (!name) return ''
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) {
    return name.slice(0, 2).toUpperCase()
  }
  return parts
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} length - Max length
 * @returns {string} - Truncated text
 */
export function truncate(text, length = 50) {
  if (!text || text.length <= length) return text
  return text.slice(0, length) + '...'
}

/**
 * Check if value is empty (null, undefined, empty string, empty array, empty object)
 * @param {*} value - Value to check
 * @returns {boolean} - True if empty
 */
export function isEmpty(value) {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

/**
 * Sleep for a specified duration
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise} - Promise that resolves after the duration
 */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Get status color based on health value
 * @param {string} health - Health status (H1, H2, H3, H4)
 * @returns {Object} - Color classes
 */
export function getHealthColor(health) {
  const colors = {
    H1: {
      bg: 'bg-emerald-500/15',
      text: 'text-emerald-400',
      border: 'border-emerald-500/30',
      dot: 'bg-emerald-500',
    },
    H2: {
      bg: 'bg-amber-500/15',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      dot: 'bg-amber-500',
    },
    H3: {
      bg: 'bg-red-500/15',
      text: 'text-red-400',
      border: 'border-red-500/30',
      dot: 'bg-red-500',
    },
    H4: {
      bg: 'bg-slate-500/15',
      text: 'text-slate-400',
      border: 'border-slate-500/30',
      dot: 'bg-slate-500',
    },
  }
  return colors[health] || colors.H1
}

/**
 * Get stage display name
 * @param {string} stage - Stage code (S1-S9)
 * @returns {string} - Stage display name
 */
export function getStageName(stage) {
  const stages = {
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
  return stages[stage] || stage
}

