/**
 * BaseDashboard - 统一Dashboard基类组件
 * 
 * 提供所有Dashboard页面的标准结构和通用功能
 * 包括：数据加载、错误处理、加载状态、刷新功能等
 * 
 * @example
 * ```jsx
 * function MyDashboard() {
 *   return (
 *     <BaseDashboard
 *       title="我的工作台"
 *       description="查看我的工作概览"
 *       queryKey={['dashboard', 'my']}
 *       queryFn={() => api.getMyDashboard()}
 *       renderContent={(data) => (
 *         <div>
 *           <StatCards stats={data.stats} />
 *           <Charts charts={data.charts} />
 *         </div>
 *       )}
 *     />
 *   );
 * }
 * ```
 */

import { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { PageHeader } from '../layout/PageHeader';
import { Button } from '../ui/button';
import { SkeletonCard } from '../ui/skeleton';
import { useDashboardData } from './useDashboardData';
import { cn } from '../../lib/utils';

// Stagger animation variants
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  }
};

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

/**
 * BaseDashboard组件Props
 * @typedef {Object} BaseDashboardProps
 * @property {string} title - Dashboard标题
 * @property {string} [description] - Dashboard描述
 * @property {Array<string|number>} queryKey - React Query的查询Key
 * @property {Function} queryFn - 数据查询函数，返回Promise
 * @property {Function} renderContent - 内容渲染函数，接收data参数
 * @property {React.ReactNode} [actions] - 额外的操作按钮
 * @property {number} [cacheTime] - 缓存时间（毫秒），默认5分钟
 * @property {boolean} [enabled] - 是否启用查询，默认true
 * @property {number} [refetchInterval] - 自动刷新间隔（毫秒）
 * @property {Function} [onSuccess] - 查询成功回调
 * @property {Function} [onError] - 查询失败回调
 * @property {string} [className] - 自定义样式类名
 * @property {boolean} [showRefresh] - 是否显示刷新按钮，默认true
 * @property {boolean} [showError] - 是否显示错误信息，默认true
 */

/**
 * 统一Dashboard基类组件
 * 
 * @param {BaseDashboardProps} props
 */
export function BaseDashboard({
  title,
  description,
  queryKey,
  queryFn,
  renderContent,
  actions,
  cacheTime = 5 * 60 * 1000, // 默认5分钟缓存
  enabled = true,
  refetchInterval,
  onSuccess,
  onError,
  className,
  showRefresh = true,
  showError = true,
}) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  // 使用统一的数据加载Hook
  const {
    data,
    loading,
    error,
    refetch,
  } = useDashboardData({
    fetchFn: queryFn,
    cacheKey: Array.isArray(queryKey) ? queryKey.join('_') : String(queryKey),
    cacheTime,
    enabled,
    refetchInterval,
    onSuccess,
    onError,
  });

  // 手动刷新处理
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refetch();
    } finally {
      setIsRefreshing(false);
    }
  }, [refetch]);

  // 渲染操作按钮
  const renderActions = () => {
    const actionButtons = [];

    if (showRefresh) {
      actionButtons.push(
        <Button
          key="refresh"
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={loading || isRefreshing}
        >
          <RefreshCw className={cn(
            "h-4 w-4 mr-2",
            (loading || isRefreshing) && "animate-spin"
          )} />
          刷新
        </Button>
      );
    }

    if (actions) {
      actionButtons.push(actions);
    }

    return actionButtons.length > 0 ? (
      <div className="flex items-center gap-2">
        {actionButtons}
      </div>
    ) : null;
  };

  // 渲染加载状态
  const renderLoading = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <SkeletonCard key={i} className="h-32" />
        ))}
      </div>
      <SkeletonCard className="h-64" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard className="h-64" />
        <SkeletonCard className="h-64" />
      </div>
    </div>
  );

  // 渲染错误状态
  const renderError = () => {
    if (!error || !showError) return null;

    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-4 mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg"
      >
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <div className="flex-1">
            <p className="text-sm font-medium text-destructive">
              加载失败
            </p>
            <p className="text-sm text-destructive/80 mt-1">
              {error.message || '无法加载数据，请稍后重试'}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
          >
            重试
          </Button>
        </div>
      </motion.div>
    );
  };

  // 渲染内容
  const renderDashboardContent = () => {
    if (loading) {
      return renderLoading();
    }

    if (error) {
      return renderError();
    }

    if (!data) {
      return (
        <div className="text-center py-12 text-muted-foreground">
          暂无数据
        </div>
      );
    }

    return (
      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
        className="space-y-6"
      >
        {renderContent ? renderContent(data) : (
          <div className="text-center py-12 text-muted-foreground">
            请提供 renderContent 函数来渲染内容
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <div className={cn("base-dashboard min-h-screen bg-background", className)}>
      <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
        className="space-y-6"
      >
        {/* 页面头部 */}
        <motion.div variants={staggerChild}>
          <PageHeader
            title={title}
            description={description}
            actions={renderActions()}
          />
        </motion.div>

        {/* 错误提示 */}
        {renderError()}

        {/* Dashboard内容 */}
        <motion.div variants={staggerChild}>
          {renderDashboardContent()}
        </motion.div>
      </motion.div>
    </div>
  );
}

export default BaseDashboard;
