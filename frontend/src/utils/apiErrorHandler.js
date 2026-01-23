/**
 * API 错误处理工具
 * 统一处理不同类型的 HTTP 错误
 */

/**
 * 错误类型分类
 */
export const ErrorTypes = {
  // 客户端错误 (4xx)
  BAD_REQUEST: 400,      // 请求参数错误
  UNAUTHORIZED: 401,     // 未登录/Token过期
  FORBIDDEN: 403,        // 无权限访问
  NOT_FOUND: 404,        // 资源不存在
  UNPROCESSABLE: 422,    // 参数验证失败
  TOO_MANY_REQUESTS: 429, // 请求过于频繁

  // 服务端错误 (5xx)
  INTERNAL_ERROR: 500,   // 服务器内部错误
  BAD_GATEWAY: 502,      // 网关错误
  SERVICE_UNAVAILABLE: 503, // 服务不可用
  GATEWAY_TIMEOUT: 504,  // 网关超时

  // 网络错误
  NETWORK_ERROR: 0,      // 网络连接失败
  TIMEOUT: 'ETIMEDOUT',  // 请求超时
};

/**
 * 判断错误是否应该使用模拟数据
 * 用于开发环境，当 API 未实现时优雅降级
 */
export function shouldUseMockData(error) {
  if (!error || !error.response) {
    return false;
  }

  const status = error.response?.status;

  // 这些错误通常表示 API 未实现或正在开发中
  // 使用模拟数据而不是显示错误
  const mockableStatuses = [
    ErrorTypes.NOT_FOUND,        // API 端点不存在
    ErrorTypes.UNPROCESSABLE,    // 参数格式不匹配（开发中常见）
    ErrorTypes.INTERNAL_ERROR,   // 服务器正在调试
  ];

  return mockableStatuses.includes(status);
}

/**
 * 判断错误是否需要重新登录
 */
export function shouldRelogin(error) {
  if (!error || !error.response) {
    return false;
  }

  return error.response?.status === ErrorTypes.UNAUTHORIZED;
}

/**
 * 判断是否为网络错误
 */
export function isNetworkError(error) {
  if (!error) {
    return false;
  }

  // 无 response 说明网络层面就失败了
  return !error.response && !!error.request;
}

/**
 * 获取用户友好的错误消息
 */
export function getErrorMessage(error, context = '操作') {
  if (!error) {
    return `${context}失败，请稍后重试`;
  }

  const status = error.response?.status;
  const detail = error.response?.data?.detail || error.response?.data?.message;

  // 根据状态码返回友好提示
  switch (status) {
    case ErrorTypes.BAD_REQUEST:
      return detail || '请求参数有误，请检查输入';
    case ErrorTypes.UNAUTHORIZED:
      return '登录已过期，请重新登录';
    case ErrorTypes.FORBIDDEN:
      return '您没有权限执行此操作';
    case ErrorTypes.NOT_FOUND:
      return detail || '请求的资源不存在';
    case ErrorTypes.UNPROCESSABLE:
      return detail || '数据格式验证失败';
    case ErrorTypes.TOO_MANY_REQUESTS:
      return '请求过于频繁，请稍后再试';
    case ErrorTypes.INTERNAL_ERROR:
      return '服务器出错，我们正在处理中';
    case ErrorTypes.BAD_GATEWAY:
    case ErrorTypes.SERVICE_UNAVAILABLE:
      return '服务暂时不可用，请稍后重试';
    case ErrorTypes.GATEWAY_TIMEOUT:
      return '请求超时，请稍后重试';
    default:
      if (isNetworkError(error)) {
        return '网络连接失败，请检查网络';
      }
      return detail || `${context}失败，请稍后重试`;
  }
}

/**
 * 日志级别
 */
export const LogLevel = {
  DEBUG: 'debug',    // 开发调试信息（静默处理）
  INFO: 'info',      // 一般信息（console.info）
  WARN: 'warn',      // 警告（console.warn）
  ERROR: 'error',    // 错误（console.error）
};

/**
 * 确定错误的日志级别
 */
export function getLogLevel(error) {
  if (!error) {
    return LogLevel.ERROR;
  }

  const status = error.response?.status;

  // 开发中的 API 静默处理
  if (shouldUseMockData(error)) {
    return LogLevel.DEBUG;
  }

  // 客户端错误用警告级别
  if (status >= 400 && status < 500) {
    return LogLevel.WARN;
  }

  // 服务器错误用错误级别
  if (status >= 500) {
    return LogLevel.ERROR;
  }

  // 网络错误用错误级别
  if (isNetworkError(error)) {
    return LogLevel.ERROR;
  }

  return LogLevel.INFO;
}

/**
 * 统一的错误日志输出
 */
export function logApiError(error, context = 'API调用') {
  const level = getLogLevel(error);
  const message = getErrorMessage(error, context);

  switch (level) {
    case LogLevel.DEBUG:
      // 开发模式下可以开启调试日志
      if (import.meta.env.DEV) {
        console.debug(`[API] ${context}:`, message);
      }
      break;
    case LogLevel.INFO:
      console.info(`[API] ${context}:`, message);
      break;
    case LogLevel.WARN:
      console.warn(`[API] ${context}:`, message);
      break;
    case LogLevel.ERROR:
      console.error(`[API] ${context}:`, error);
      break;
  }
}

/**
 * 处理 API 错误的 Hook
 * 返回是否应该使用模拟数据
 */
export function handleApiError(error, context = 'API调用') {
  logApiError(error, context);

  // 判断是否需要重新登录
  if (shouldRelogin(error)) {
    // 清除本地存储的 token
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    // 可以触发重新登录逻辑
    window.location.href = '/login';
    return { useMockData: false, shouldRelogin: true };
  }

  // 判断是否使用模拟数据
  const useMock = shouldUseMockData(error);

  return {
    useMockData: useMock,
    shouldRelogin: false,
    message: getErrorMessage(error, context),
  };
}

export default {
  ErrorTypes,
  shouldUseMockData,
  shouldRelogin,
  isNetworkError,
  getErrorMessage,
  getLogLevel,
  logApiError,
  handleApiError,
};
