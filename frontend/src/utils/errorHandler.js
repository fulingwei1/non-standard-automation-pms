/**
 * Centralized error handling utilities
 * 
 * Combines pure error logic + UI notification helpers (antd)
 */
import { message as antdMessage, Modal } from 'antd';

// ==================== Error Types ====================

export const ERROR_TYPES = {
  NETWORK: '网络错误',
  VALIDATION: '数据验证错误',
  AUTH: '认证错误',
  PERMISSION: '权限错误',
  NOT_FOUND: '资源未找到',
  SERVER: '服务器错误',
  UNKNOWN: '未知错误',
};

// ==================== Error Detection ====================

/**
 * Extract error message from various error formats
 */
export function getErrorMessage(error) {
  if (!error) return '未知错误';

  // Axios error with response
  if (error.response) {
    const { data, status } = error.response;
    if (data?.detail) return data.detail;
    if (data?.message) return data.message;

    const statusMessages = {
      400: '请求参数错误',
      401: '未授权，请重新登录',
      403: '没有权限访问此资源',
      404: '请求的资源不存在',
      409: '资源冲突',
      422: '数据验证失败',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务暂时不可用',
      504: '网关超时',
    };
    return statusMessages[status] || `请求失败 (${status})`;
  }

  // Network error (no response)
  if (error.request) return '网络连接失败，请检查网络设置';
  if (error.message) return error.message;
  return '未知错误';
}

export function isNetworkError(error) {
  return !error.response && !!error.request;
}

export function isAuthError(error) {
  return error.response?.status === 401;
}

export function isPermissionError(error) {
  return error.response?.status === 403;
}

export function isValidationError(error) {
  return error.response?.status === 400 || error.response?.status === 422;
}

export function getValidationErrors(error) {
  if (!isValidationError(error)) return {};
  const { data } = error.response;
  if (data?.errors) return data.errors;
  if (data?.detail && typeof data.detail === 'object') return data.detail;
  return {};
}

// ==================== Error Formatting ====================

export const formatErrorMessage = (type, msg) => `[${type}] ${msg}`;

// ==================== UI Notification Helpers ====================

export const showError = (errorMessage, duration = 5) => {
  antdMessage.error(errorMessage, duration);
};

export const showSuccess = (successMessage, duration = 3) => {
  antdMessage.success(successMessage, duration);
};

export const showWarning = (warningMessage, duration = 4) => {
  antdMessage.warning(warningMessage, duration);
};

export const showInfo = (infoMessage, duration = 3) => {
  antdMessage.info(infoMessage, duration);
};

export const showErrorModal = (title, content, onOk) => {
  Modal.error({ title, content, onOk });
};

// ==================== Error Handling ====================

/**
 * Handle API error with appropriate action (callback-based)
 */
export function handleApiError(error, options = {}) {
  const {
    onAuthError,
    onPermissionError,
    onNetworkError,
    onValidationError,
    onOtherError,
  } = options;

  if (isAuthError(error)) {
    const token = localStorage.getItem('token');
    const isDemoAccount = token && token.startsWith('demo_token_');
    if (isDemoAccount) {
      console.log('演示账号 API 调用失败，将使用 mock 数据');
      return;
    }
    if (onAuthError) {
      onAuthError(error);
    } else {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return;
  }

  if (isPermissionError(error)) {
    if (onPermissionError) {
      onPermissionError(error);
    } else {
      console.warn('Permission denied:', getErrorMessage(error));
    }
    return;
  }

  if (isNetworkError(error)) {
    if (onNetworkError) onNetworkError(error);
    return;
  }

  if (isValidationError(error)) {
    if (onValidationError) onValidationError(error, getValidationErrors(error));
    return;
  }

  if (onOtherError) onOtherError(error);
}

/**
 * Get formatted API error message (string return version)
 */
export const getApiErrorMessage = (error) => {
  if (!error) return '未知错误';

  if (error.response) {
    const { status, data } = error.response;
    if (data?.message) return formatErrorMessage(ERROR_TYPES.SERVER, data.message);
    if (status === 401) return formatErrorMessage(ERROR_TYPES.AUTH, '未授权，请重新登录');
    if (status === 403) return formatErrorMessage(ERROR_TYPES.PERMISSION, '权限不足');
    if (status === 404) return formatErrorMessage(ERROR_TYPES.NOT_FOUND, '资源未找到');
    if (status === 422) return formatErrorMessage(ERROR_TYPES.VALIDATION, data?.detail || '请求参数错误');
    if (status >= 500) return formatErrorMessage(ERROR_TYPES.SERVER, '服务器内部错误');
  }

  if (error.message) return error.message;
  return formatErrorMessage(ERROR_TYPES.UNKNOWN, '发生未知错误');
};

/**
 * Async error boundary handler
 */
export const withErrorHandling = async (callback, errorHandler) => {
  try {
    await callback();
  } catch (error) {
    const errorMessage = getApiErrorMessage(error);
    errorHandler(errorMessage);
  }
};

export default {
  ERROR_TYPES,
  formatErrorMessage,
  getErrorMessage,
  getApiErrorMessage,
  getValidationErrors,
  isNetworkError,
  isAuthError,
  isPermissionError,
  isValidationError,
  showError,
  showSuccess,
  showWarning,
  showInfo,
  showErrorModal,
  handleApiError,
  withErrorHandling,
};
