/**
 * Centralized error handling utilities
 */

/**
 * Extract error message from various error formats
 * @param {Error|Object} error - Error object
 * @returns {string} - Human-readable error message
 */
export function getErrorMessage(error) {
  if (!error) {return "未知错误";}

  // Axios error
  if (error.response) {
    const { data, status } = error.response;

    // Backend error with detail
    if (data?.detail) {
      return data.detail;
    }

    // Backend error with message
    if (data?.message) {
      return data.message;
    }

    // HTTP status messages
    const statusMessages = {
      400: "请求参数错误",
      401: "未授权，请重新登录",
      403: "没有权限访问此资源",
      404: "请求的资源不存在",
      409: "资源冲突",
      422: "数据验证失败",
      500: "服务器内部错误",
      502: "网关错误",
      503: "服务暂时不可用",
      504: "网关超时",
    };

    return statusMessages[status] || `请求失败 (${status})`;
  }

  // Network error
  if (error.request) {
    return "网络连接失败，请检查网络设置";
  }

  // Standard error
  if (error.message) {
    return error.message;
  }

  return "未知错误";
}

/**
 * Check if error is a network error
 * @param {Error|Object} error - Error object
 * @returns {boolean}
 */
export function isNetworkError(error) {
  return !error.response && error.request;
}

/**
 * Check if error is an authentication error (401)
 * @param {Error|Object} error - Error object
 * @returns {boolean}
 */
export function isAuthError(error) {
  return error.response?.status === 401;
}

/**
 * Check if error is a permission error (403)
 * @param {Error|Object} error - Error object
 * @returns {boolean}
 */
export function isPermissionError(error) {
  return error.response?.status === 403;
}

/**
 * Check if error is a validation error
 * @param {Error|Object} error - Error object
 * @returns {boolean}
 */
export function isValidationError(error) {
  return error.response?.status === 400 || error.response?.status === 422;
}

/**
 * Extract validation errors from error response
 * @param {Error|Object} error - Error object
 * @returns {Object} - Field errors object
 */
export function getValidationErrors(error) {
  if (!isValidationError(error)) {return {};}

  const { data } = error.response;
  if (data?.errors) {
    return data.errors;
  }

  if (data?.detail && typeof data.detail === "object") {
    return data.detail;
  }

  return {};
}

/**
 * Handle API error with appropriate action
 * @param {Error|Object} error - Error object
 * @param {Object} options - Handling options
 * @param {Function} options.onAuthError - Callback for auth errors
 * @param {Function} options.onNetworkError - Callback for network errors
 * @param {Function} options.onValidationError - Callback for validation errors
 * @param {Function} options.onOtherError - Callback for other errors
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
    // 检查是否是演示账号，演示账号的 401 错误不应该导致登出
    const token = localStorage.getItem("token");
    const isDemoAccount = token && token.startsWith("demo_token_");

    if (isDemoAccount) {
      // 演示账号的 401 错误是预期的，不处理
      console.log("演示账号 API 调用失败，将使用 mock 数据");
      return;
    }

    if (onAuthError) {
      onAuthError(error);
    } else {
      // Default: redirect to login
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/";
    }
    return;
  }

  if (isPermissionError(error)) {
    if (onPermissionError) {
      onPermissionError(error);
    } else {
      // Default: show permission error message
      // Component should handle displaying the error
      console.warn("Permission denied:", getErrorMessage(error));
    }
    return;
  }

  if (isNetworkError(error)) {
    if (onNetworkError) {
      onNetworkError(error);
    }
    return;
  }

  if (isValidationError(error)) {
    if (onValidationError) {
      onValidationError(error, getValidationErrors(error));
    }
    return;
  }

  if (onOtherError) {
    onOtherError(error);
  }
}
