import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { PROJECT_STAGES, HEALTH_CONFIG } from "./constants/index";

/**
 * Merge class names with tailwind-merge
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// formatDate re-exported from formatters
export { formatDate } from './formatters';

/**
 * Format currency value
 */
export function formatCurrency(value, currency = "CNY") {
  if (value === null || value === undefined) {return "";}
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

/**
 * Format amount (short form, e.g., 1.2万, 3.5亿)
 */
export function formatAmount(amount) {
  if (amount === null || amount === undefined) {return "0";}
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)}亿`;
  }
  if (amount >= 10000) {
    return `${(amount / 10000).toFixed(2)}万`;
  }
  return amount.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

/**
 * Format number with thousand separators
 */
export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined) {return "";}
  return new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format percentage
 */
export function formatPercent(value, decimals = 1) {
  if (value === null || value === undefined) {return "";}
  return `${Number(value).toFixed(decimals)}%`;
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text, length = 50) {
  if (!text) {return "";}
  if (text.length <= length) {return text;}
  return text.slice(0, length) + "...";
}

/**
 * Generate initials from name
 */
export function getInitials(name) {
  if (!name) {return "";}
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Sleep utility for async operations
 */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Debounce function
 */
export function debounce(fn, delay) {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * Check if value is empty (null, undefined, empty string, empty array, empty object)
 */
export function isEmpty(value) {
  if (value === null || value === undefined) {return true;}
  if (typeof value === "string") {return value.trim() === "";}
  if (Array.isArray(value)) {return value.length === 0;}
  if (typeof value === "object") {return Object.keys(value).length === 0;}
  return false;
}

/**
 * Get stage name from stage code
 */
export function getStageName(stageCode) {
  if (!stageCode) {return "";}
  const stage = PROJECT_STAGES.find((s) => s.code === stageCode);
  return stage ? stage.name : stageCode;
}

/**
 * Get stage config by code
 */
export function getStageConfig(stageCode) {
  return PROJECT_STAGES.find((s) => s.code === stageCode) || PROJECT_STAGES[0];
}

/**
 * Get health config by code
 */
export function getHealthConfig(healthCode) {
  return HEALTH_CONFIG[healthCode] || HEALTH_CONFIG.H1;
}

/**
 * Get health name from health code
 */
export function getHealthName(healthCode) {
  const config = HEALTH_CONFIG[healthCode];
  return config ? config.name : healthCode;
}

/**
 * Format time string to HH:mm format
 */
export function formatTime(time, options = {}) {
  if (!time) {return "";}

  // If it's a Date object
  if (time instanceof Date) {
    return time.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
      ...options,
    });
  }

  // If it's a string like "14:30" or "14:30:00"
  if (typeof time === "string") {
    // If it's already in HH:mm format
    if (/^\d{2}:\d{2}$/.test(time)) {return time;}
    // If it's in HH:mm:ss format
    if (/^\d{2}:\d{2}:\d{2}$/.test(time)) {return time.slice(0, 5);}
    // Try to parse as date
    const d = new Date(time);
    if (!isNaN(d.getTime())) {
      return d.toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
        ...options,
      });
    }
  }

  return time;
}

/**
 * Format datetime to full datetime string
 */
export function formatDateTime(datetime, options = {}) {
  if (!datetime) {return "";}
  const d = new Date(datetime);
  if (isNaN(d.getTime())) {return datetime;}

  return d.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    ...options,
  });
}

/**
 * Get color class for health status
 */
export function getHealthColor(healthCode) {
  const config = HEALTH_CONFIG[healthCode];
  return config ? config.color : "slate";
}

/**
 * Get stage color class
 */
export function getStageColor(stageCode) {
  const stage = PROJECT_STAGES.find((s) => s.code === stageCode);
  return stage ? stage.color : "slate";
}
