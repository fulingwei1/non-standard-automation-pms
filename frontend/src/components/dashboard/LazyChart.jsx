/**
 * LazyChart - 懒加载图表组件包装器
 * 使用 React.lazy 和 Suspense 实现图表组件的按需加载
 */
import { Suspense, lazy } from "react";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { Card, CardContent } from "../ui/card";

/**
 * 创建懒加载的图表组件
 * @param {Function} importFn - 动态导入函数
 */
export function createLazyChart(importFn) {
  const LazyComponent = lazy(importFn);

  return function LazyChartWrapper(props) {
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
 * @param {Object} props
 * @param {Function} props.component - 动态导入函数
 * @param {React.ReactNode} props.fallback - 加载中显示的内容
 * @param {string} props.className - CSS类名
 */
export function LazyChart({ component, fallback, className, ...props }) {
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
