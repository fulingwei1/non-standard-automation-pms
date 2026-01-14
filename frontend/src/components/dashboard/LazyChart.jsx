/**
 * LazyChart - 懒加载图表组件包装器
 * 使用 React.lazy 和 Suspense 实现图表组件的按需加载
 */
import { Suspense, lazy, ComponentType } from "react";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { Card, CardContent } from "../ui/card";

interface LazyChartProps {
  component: () => Promise<{ default: ComponentType<any> }>;
  fallback?: React.ReactNode;
  className?: string;
  [key: string]: any;
}

/**
 * 创建懒加载的图表组件
 */
export function createLazyChart<T = any>(
  importFn: () => Promise<{ default: ComponentType<T> }>
) {
  const LazyComponent = lazy(importFn);
  
  return function LazyChartWrapper(props: T) {
    return (
      <Suspense
        fallback={
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-center h-64">
                <LoadingSpinner />
              </div>
            </CardContent>
          </Card>
        }
      >
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

/**
 * 通用懒加载图表组件
 */
export function LazyChart({
  component,
  fallback,
  className,
  ...props
}: LazyChartProps) {
  const LazyComponent = lazy(component);

  const defaultFallback = (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <Suspense fallback={fallback || defaultFallback}>
      <LazyComponent {...props} />
    </Suspense>
  );
}

export default LazyChart;
