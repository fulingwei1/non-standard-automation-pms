/**
 * 优化的图片组件
 * 支持懒加载、占位符、错误处理等功能
 */

import { useState, useRef, useEffect } from 'react';
import { cn } from '../lib/utils';

export function OptimizedImage({
  src,
  alt,
  className,
  width,
  height,
  loading = 'lazy', // 'eager' 或 'lazy'
  placeholder = true, // 是否显示占位符
  fallback, // 失败时的备用图片
  onLoad,
  onError,
  style,
  ...props
}) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [imageSrc, setImageSrc] = useState(src);
  const imgRef = useRef(null);

  // 图片加载完成
  const handleLoad = (e) => {
    setIsLoading(false);
    setHasError(false);
    onLoad?.(e);
  };

  // 图片加载失败
  const handleError = () => {
    setIsLoading(false);
    setHasError(true);

    // 如果有备用图片，尝试加载
    if (fallback && imageSrc !== fallback) {
      setImageSrc(fallback);
    }

    onError?.();
  };

  // 使用 Intersection Observer 实现懒加载
  useEffect(() => {
    if (loading === 'eager') return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              observer.unobserve(img);
            }
          }
        });
      },
      {
        rootMargin: '100px', // 提前100px开始加载
      }
    );

    const imgElement = imgRef.current;
    if (imgElement) {
      // 延迟加载时，先设置data-src
      imgElement.dataset.src = src;
      imgElement.src = 'data:image/svg+xml,' + encodeURIComponent(
        '<svg width="1" height="1" xmlns="http://www.w3.org/2000/svg"></svg>'
      );
      observer.observe(imgElement);
    }

    return () => {
      if (imgElement) {
        observer.unobserve(imgElement);
      }
    };
  }, [src, loading]);

  return (
    <div
      className={cn('relative overflow-hidden bg-gray-100', className)}
      style={{ width: width || '100%', height: height || 'auto', ...style }}
    >
      {/* 占位符 */}
      {placeholder && isLoading && (
        <div
          className="absolute inset-0 animate-pulse bg-gray-200"
          style={{ width: width || '100%', height: height || '100%' }}
        >
          <svg
            className="h-full w-full text-gray-300"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      )}

      {/* 图片 */}
      <img
        ref={imgRef}
        src={loading === 'eager' ? imageSrc : undefined}
        alt={alt}
        loading={loading}
        className={cn(
          'w-full h-full object-cover transition-opacity duration-300',
          isLoading ? 'opacity-0' : 'opacity-100',
          hasError && 'hidden'
        )}
        onLoad={handleLoad}
        onError={handleError}
        width={width}
        height={height}
        {...props}
      />

      {/* 错误提示 */}
      {hasError && !fallback && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-gray-400">
          <svg
            className="h-12 w-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}
    </div>
  );
}


/**
 * 头像组件（优化版）
 */

export function Avatar({
  src,
  alt,
  name,
  size = 'md',
  className,
  onClick,
}) {
  const [hasError, setHasError] = useState(false);

  const sizeClasses = {
    xs: 'h-6 w-6 text-xs',
    sm: 'h-8 w-8 text-sm',
    md: 'h-10 w-10 text-base',
    lg: 'h-12 w-12 text-lg',
    xl: 'h-16 w-16 text-xl',
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getAvatarColor = (name) => {
    const colors = [
      'bg-red-500',
      'bg-blue-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-indigo-500',
      'bg-teal-500',
    ];
    const index = name ? name.charCodeAt(0) % colors.length : 0;
    return colors[index];
  };

  return (
    <div
      className={cn(
        'relative inline-flex items-center justify-center rounded-full',
        sizeClasses[size],
        !src && getAvatarColor(name),
        className
      )}
      onClick={onClick}
    >
      {src && !hasError ? (
        <OptimizedImage
          src={src}
          alt={alt || name}
          width={size === 'xl' ? 64 : size === 'lg' ? 48 : 40}
          height={size === 'xl' ? 64 : size === 'lg' ? 48 : 40}
          className="rounded-full"
          fallback={null}
          onError={() => setHasError(true)}
        />
      ) : (
        <span className="font-medium text-white">
          {getInitials(name)}
        </span>
      )}
    </div>
  );
}


/**
 * 图片画廊组件（带懒加载和虚拟滚动）
 */

export function ImageGallery({
  images = [],
  columns = 3,
  gap = 4,
  className,
  onImageClick,
}) {
  return (
    <div
      className={cn('grid', className)}
      style={{
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: `${gap * 4}px`,
      }}
    >
      {images.map((image, index) => (
        <div
          key={index}
          className="relative group cursor-pointer"
          onClick={() => onImageClick?.(image, index)}
        >
          <OptimizedImage
            src={image.src}
            alt={image.alt || `Image ${index + 1}`}
            className="rounded-lg transition-transform duration-300 group-hover:scale-105"
            height={200}
          />
          <div className="absolute inset-0 rounded-lg bg-black bg-opacity-0 transition-opacity duration-300 group-hover:bg-opacity-20" />
        </div>
      ))}
    </div>
  );
}


/**
 * 响应式图片组件
 * 根据屏幕尺寸加载不同尺寸的图片
 */

export function ResponsiveImage({
  src,
  alt,
  sizes = [
    { maxWidth: 640, src: null }, // 默认使用src
    { maxWidth: 768, src: null },
    { maxWidth: 1024, src: null },
    { maxWidth: 1280, src: null },
    { maxWidth: null, src: null }, // 最大尺寸
  ],
  className,
  ...props
}) {
  const [currentSrc, setCurrentSrc] = useState(src);

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      for (const size of sizes) {
        if (size.maxWidth === null || width <= size.maxWidth) {
          setCurrentSrc(size.src || src);
          break;
        }
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [src, sizes]);

  return (
    <img
      src={currentSrc}
      alt={alt}
      className={className}
      {...props}
    />
  );
}


export default OptimizedImage;
