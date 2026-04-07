import { lazy } from "react";

const Loading = () => (
  <div className="flex items-center justify-center h-64">
    <span className="text-text-secondary">加载中...</span>
  </div>
);

export function lazyLoad(importFn) {
  const LazyComponent = lazy(importFn);
  return function LazyWrapper(props) {
    return (
      <Suspense fallback={<Loading />}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}
