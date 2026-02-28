/**
 * 仪表板渲染器 (Dashboard Renderer)
 *
 * 根据组件配置动态渲染工作台网格布局
 * 支持懒加载、错误边界、加载状态
 */

import { Suspense, memo } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';
import ErrorBoundary from '../../components/ui/ErrorBoundary';
import { Skeleton } from '../../components/ui/skeleton';
import { Card, CardContent } from '../../components/ui/card';
import { widgetRegistry } from './config/widgetRegistry';
import { cn } from '../../lib/utils';

/**
 * 组件加载骨架屏
 */
function WidgetSkeleton({ size = 'medium' }) {
  const heightClass = {
    small: 'h-32',
    medium: 'h-48',
    large: 'h-64',
    full: 'h-96',
  }[size] || 'h-48';

  return (
    <Card className={cn('animate-pulse', heightClass)}>
      <CardContent className="p-4">
        <Skeleton className="h-4 w-1/3 mb-4" />
        <Skeleton className="h-24 w-full" />
      </CardContent>
    </Card>
  );
}

/**
 * 组件错误回退
 */
function WidgetErrorFallback({ widgetId, error }) {
  return (
    <Card className="border-destructive/50 bg-destructive/5">
      <CardContent className="p-4 flex flex-col items-center justify-center h-48">
        <AlertTriangle className="h-8 w-8 text-destructive mb-2" />
        <p className="text-sm text-muted-foreground text-center">
          组件 "{widgetId}" 加载失败
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {error?.message || '未知错误'}
        </p>
      </CardContent>
    </Card>
  );
}

/**
 * 组件未找到占位
 */
function WidgetNotFound({ widgetId }) {
  return (
    <Card className="border-dashed border-muted-foreground/30">
      <CardContent className="p-4 flex flex-col items-center justify-center h-48 text-muted-foreground">
        <p className="text-sm">组件未注册: {widgetId}</p>
      </CardContent>
    </Card>
  );
}

/**
 * 单个组件渲染器
 */
const WidgetRenderer = memo(function WidgetRenderer({
  widget,
  data,
  index,
}) {
  const { id, props = {}, size } = widget;
  const widgetConfig = widgetRegistry[id];

  // 组件未注册
  if (!widgetConfig) {
    return <WidgetNotFound widgetId={id} />;
  }

  const { component: WidgetComponent, defaultSize } = widgetConfig;
  const finalSize = size || defaultSize || 'medium';

  // 尺寸到 CSS 类的映射
  const sizeClass = {
    small: 'col-span-1',
    medium: 'col-span-1 md:col-span-1',
    large: 'col-span-1 md:col-span-2',
    full: 'col-span-1 md:col-span-2',
  }[finalSize] || 'col-span-1';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className={cn('widget-container', sizeClass)}
    >
      <ErrorBoundary
        fallback={<WidgetErrorFallback widgetId={id} />}
      >
        <Suspense fallback={<WidgetSkeleton size={finalSize} />}>
          <WidgetComponent
            {...props}
            data={data?.[id]}
            widgetId={id}
          />
        </Suspense>
      </ErrorBoundary>
    </motion.div>
  );
});

/**
 * 仪表板骨架屏
 */
export function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
      {[...Array(6)].map((_, i) => (
        <WidgetSkeleton key={i} size={i < 2 ? 'large' : 'medium'} />
      ))}
    </div>
  );
}

/**
 * 仪表板渲染器主组件
 *
 * @param {Object} props
 * @param {Array} props.widgets - 组件配置列表
 * @param {Object} props.data - 组件数据映射 { widgetId: data }
 * @param {boolean} props.loading - 加载状态
 * @param {string} props.layout - 布局模式
 */
export function DashboardRenderer({
  widgets = [],
  data = {},
  loading = false,
  layout = '2-column',
}) {
  // 加载状态
  if (loading) {
    return <DashboardSkeleton />;
  }

  // 无组件
  if (!widgets || widgets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        <p>暂无工作台组件配置</p>
      </div>
    );
  }

  // 布局类映射
  const layoutClass = {
    '1-column': 'grid-cols-1',
    '2-column': 'grid-cols-1 md:grid-cols-2',
    '3-column': 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    'dashboard': 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
  }[layout] || 'grid-cols-1 md:grid-cols-2';

  return (
    <div className={cn('grid gap-4 p-4', layoutClass)}>
      {(widgets || []).map((widget, index) => (
        <WidgetRenderer
          key={`${widget.id}-${index}`}
          widget={widget}
          data={data}
          index={index}
        />
      ))}
    </div>
  );
}

export default DashboardRenderer;
