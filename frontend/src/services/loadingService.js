// Loading Service - 统一的加载状态管理工具
import { Spin, Progress } from 'antd';

/**
 * 显示加载指示器（Spin 组件）
 * @param {boolean} loading - 是否加载中
 * @param {Object} options - 可选配置
 * @returns {JSX.Element} Spin 组件
 */
export const showLoading = (loading, options = {}) => {
  if (loading) {
    return <Spin tip="加载中..." {...options} />;
  }
  return null;
};

/**
 * 显示进度条（Progress 组件）
 * @param {number} percent - 百分比（0-100）
 * @param {string} status - 状态文本
 * @returns {JSX.Element} Progress 组件
 */
export const showProgress = (percent, status) => {
  return <Progress percent={percent} status={status} />;
};

/**
 * 显示全屏加载遮罩
 * @param {boolean} loading - 是否加载中
 * @returns {JSX.Element} 全屏加载组件
 */
export const showFullScreenLoading = (loading) => {
  if (!loading) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(255, 255, 255, 0.7)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
      }}
    >
      <Spin size="large" />
    </div>
  );
};

/**
 * 延迟加载（用于模拟网络延迟）
 * @param {Function} callback - 回调函数
 * @param {number} delay - 延迟毫秒数
 * @returns {Promise<void>}
 */
export const delayLoading = async (callback, delay = 1000) => {
  await new Promise((resolve) => setTimeout(resolve, delay));
  await callback();
};

export default {
  showLoading,
  showProgress,
  showFullScreenLoading,
  delayLoading,
};
