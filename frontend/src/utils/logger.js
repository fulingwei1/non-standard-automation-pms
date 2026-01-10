/**
 * 统一日志管理工具
 * 生产环境可通过配置禁用所有日志
 */

const isDevelopment =
  import.meta.env?.DEV ?? process.env?.NODE_ENV !== "production";

const LOG_LEVELS = {
  NONE: 0,
  ERROR: 1,
  WARN: 2,
  INFO: 3,
  DEBUG: 4,
};

// 从环境变量读取日志级别，默认开发环境 DEBUG，生产环境 ERROR
const currentLogLevel = isDevelopment ? LOG_LEVELS.DEBUG : LOG_LEVELS.ERROR;

/**
 * 安全的日志输出 - 仅在开发环境或指定日志级别下输出
 */
export const logger = {
  /**
   * 调试日志 - 仅开发环境
   */
  debug: (...args) => {
    if (isDevelopment && currentLogLevel >= LOG_LEVELS.DEBUG) {
      console.log("[DEBUG]", ...args);
    }
  },

  /**
   * 信息日志 - 仅开发环境
   */
  info: (...args) => {
    if (isDevelopment && currentLogLevel >= LOG_LEVELS.INFO) {
      console.info("[INFO]", ...args);
    }
  },

  /**
   * 警告日志 - 开发环境始终显示，生产环境可配置
   */
  warn: (...args) => {
    if (currentLogLevel >= LOG_LEVELS.WARN) {
      console.warn("[WARN]", ...args);
    }
  },

  /**
   * 错误日志 - 始终显示
   */
  error: (...args) => {
    if (currentLogLevel >= LOG_LEVELS.ERROR) {
      console.error("[ERROR]", ...args);
    }
  },

  /**
   * 性能日志
   */
  perf: (label, fn) => {
    if (isDevelopment && currentLogLevel >= LOG_LEVELS.DEBUG) {
      const start = performance.now();
      const result = fn();
      const end = performance.now();
      console.log(`[PERF] ${label}: ${(end - start).toFixed(2)}ms`);
      return result;
    }
    return fn();
  },
};

/**
 * 用于追踪函数调用
 */
export const trace = (fnName) => {
  logger.debug(`→ ${fnName}`);
  return () => logger.debug(`← ${fnName}`);
};

/**
 * 条件日志 - 仅在条件满足时输出
 */
export const logIf = (condition, ...args) => {
  if (condition && isDevelopment) {
    console.log(...args);
  }
};

/**
 * 分组日志
 */
export const group = (label, fn) => {
  if (isDevelopment && currentLogLevel >= LOG_LEVELS.DEBUG) {
    console.group(label);
    fn();
    console.groupEnd();
  } else {
    fn();
  }
};

export default logger;
