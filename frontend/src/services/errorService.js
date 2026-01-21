// Error Handling Service - 统一的错误处理工具
import { message, Modal } from 'antd';

/**
 * 错误类型定义
 */
export const ERROR_TYPES = {
  NETWORK: '网络错误',
  VALIDATION: '数据验证错误',
  AUTH: '认证错误',
  PERMISSION: '权限错误',
  NOT_FOUND: '资源未找到',
  SERVER: '服务器错误',
  UNKNOWN: '未知错误',
};

/**
 * 统一的错误消息格式
 * @param {string} type - 错误类型
 * @param {string} message - 错误消息
 * @returns {string} 格式化后的错误消息
 */
export const formatErrorMessage = (type, message) => {
  return `[${type}] ${message}`;
};

/**
 * 显示错误提示（message 组件）
 * @param {string} errorMessage - 错误消息
 * @param {number} duration - 显示时长（秒）
 */
export const showError = (errorMessage, duration = 5) => {
  message.error(errorMessage, duration);
};

/**
 * 显示成功提示（message 组件）
 * @param {string} successMessage - 成功消息
 * @param {number} duration - 显示时长（秒）
 */
export const showSuccess = (successMessage, duration = 3) => {
  message.success(successMessage, duration);
};

/**
 * 显示警告提示（message 组件）
 * @param {string} warningMessage - 警告消息
 * @param {number} duration - 显示时长（秒）
 */
export const showWarning = (warningMessage, duration = 4) => {
  message.warning(warningMessage, duration);
};

/**
 * 显示信息提示（message 组件）
 * @param {string} infoMessage - 信息消息
 * @param {number} duration - 显示时长（秒）
 */
export const showInfo = (infoMessage, duration = 3) => {
  message.info(infoMessage, duration);
};

/**
 * 显示错误弹窗（Modal 组件）
 * @param {string} title - 弹窗标题
 * @param {string} content - 弹窗内容
 * @param {Function} onOk - 确定回调
 */
export const showErrorModal = (title, content, onOk) => {
  Modal.error({
    title,
    content,
    onOk,
  });
};

/**
 * 处理 API 错误响应
 * @param {Error} error - 错误对象
 * @returns {string} 格式化后的错误消息
 */
export const handleApiError = (error) => {
  if (!error) return '未知错误';

  if (error.response) {
    const { status, data } = error.response;

    if (data && data.message) {
      return formatErrorMessage(
        ERROR_TYPES.SERVER,
        data.message
      );
    }

    if (status === 401) {
      return formatErrorMessage(
        ERROR_TYPES.AUTH,
        '未授权，请重新登录'
      );
    }

    if (status === 403) {
      return formatErrorMessage(
        ERROR_TYPES.PERMISSION,
        '权限不足'
      );
    }

    if (status === 404) {
      return formatErrorMessage(
        ERROR_TYPES.NOT_FOUND,
        '资源未找到'
      );
    }

    if (status === 422) {
      return formatErrorMessage(
        ERROR_TYPES.VALIDATION,
        data?.detail || '请求参数错误'
      );
    }

    if (status >= 500) {
      return formatErrorMessage(
        ERROR_TYPES.SERVER,
        '服务器内部错误'
      );
    }
  }

  if (error.message) {
    return error.message;
  }

  return formatErrorMessage(
    ERROR_TYPES.UNKNOWN,
    '发生未知错误'
  );
};

/**
 * 异步错误边界处理器
 * @param {Function} callback - 回调函数
 * @param {Function} errorHandler - 错误处理器
 * @returns {Promise<void>}
 */
export const withErrorHandling = async (callback, errorHandler) => {
  try {
    await callback();
  } catch (error) {
    const errorMessage = handleApiError(error);
    errorHandler(errorMessage);
  }
};

export default {
  ERROR_TYPES,
  formatErrorMessage,
  showError,
  showSuccess,
  showWarning,
  showInfo,
  showErrorModal,
  handleApiError,
  withErrorHandling,
};
