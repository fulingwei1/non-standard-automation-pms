/**
 * useIntersectionObserver - Intersection Observer Hook
 * 用于实现数据预加载、无限滚动等功能
 */
import { useEffect, useRef, useState, useCallback } from "react";

interface UseIntersectionObserverOptions {
  threshold?: number | number[];
  root?: Element | null;
  rootMargin?: string;
  enabled?: boolean;
}

/**
 * 基础 Intersection Observer Hook
 */
export function useIntersectionObserver(
  options: UseIntersectionObserverOptions = {}
) {
  const {
    threshold = 0,
    root = null,
    rootMargin = "0px",
    enabled = true,
  } = options;

  const elementRef = useRef<Element | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);

  useEffect(() => {
    if (!enabled || !elementRef.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        if (entry.isIntersecting && !hasIntersected) {
          setHasIntersected(true);
        }
      },
      {
        threshold,
        root,
        rootMargin,
      }
    );

    observer.observe(elementRef.current);

    return () => {
      if (elementRef.current) {
        observer.unobserve(elementRef.current);
      }
    };
  }, [threshold, root, rootMargin, enabled, hasIntersected]);

  return { elementRef, isIntersecting, hasIntersected };
}

/**
 * 用于触发加载的 Hook（无限滚动等场景）
 */
export function useInfiniteScroll(
  callback: () => void,
  options: UseIntersectionObserverOptions = {}
) {
  const { elementRef, isIntersecting } = useIntersectionObserver({
    ...options,
    threshold: 0.1,
  });

  useEffect(() => {
    if (isIntersecting) {
      callback();
    }
  }, [isIntersecting, callback]);

  return elementRef;
}

/**
 * 用于预加载数据的 Hook
 */
export function usePreload(
  callback: () => void | Promise<void>,
  options: UseIntersectionObserverOptions & {
    preloadDistance?: number; // 预加载距离（px）
  } = {}
) {
  const { preloadDistance = 200, ...observerOptions } = options;

  const { elementRef, isIntersecting } = useIntersectionObserver({
    ...observerOptions,
    rootMargin: `${preloadDistance}px`,
    threshold: 0,
  });

  const [hasPreloaded, setHasPreloaded] = useState(false);

  useEffect(() => {
    if (isIntersecting && !hasPreloaded) {
      setHasPreloaded(true);
      Promise.resolve(callback()).catch((err) => {
        console.error("Preload error:", err);
      });
    }
  }, [isIntersecting, hasPreloaded, callback]);

  return { elementRef, hasPreloaded };
}
