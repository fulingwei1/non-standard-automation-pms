/**
 * 虚拟滚动组件
 * 用于渲染大数据列表，只渲染可视区域内的项目
 *
 * 使用方式：
 * ```jsx
 * <VirtualScroll
 *   items={items}
 *   itemHeight={50}
 *   height={400}
 *   renderItem={(item, index) => <div>{item.name}</div>}
 * />
 * ```
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '../lib/utils';

export function VirtualScroll({
  items = [],
  itemHeight,
  height = 400,
  renderItem,
  overscan = 3, // 可视区域外预渲染的项目数
  className,
}) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef(null);
  const lastItemHeight = useRef(itemHeight);

  // 如果itemHeight发生变化，更新lastItemHeight
  useEffect(() => {
    lastItemHeight.current = itemHeight;
  }, [itemHeight]);

  // 计算可视区域内的项目索引
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.floor((scrollTop + height) / itemHeight) + overscan
  );

  // 可视项目
  const visibleItems = items.slice(startIndex, endIndex + 1);

  // 处理滚动事件
  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);

  // 计算容器的总高度
  const totalHeight = items.length * itemHeight;

  // 计算偏移量
  const offsetY = startIndex * itemHeight;

  return (
    <div
      ref={containerRef}
      className={cn('overflow-auto', className)}
      style={{ height }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map((item, index) => {
          const actualIndex = startIndex + index;
          return (
            <div
              key={actualIndex}
              style={{
                position: 'absolute',
                top: actualIndex * itemHeight,
                height: itemHeight,
                width: '100%',
              }}
            >
              {renderItem(item, actualIndex)}
            </div>
          );
        })}
      </div>
    </div>
  );
}


/**
 * 动态高度虚拟滚动组件
 * 适用于项目高度不一致的情况
 */

export function DynamicVirtualScroll({
  items = [],
  estimateItemHeight = () => 50,
  height = 400,
  renderItem,
  overscan = 3,
  className,
}) {
  const [scrollTop, setScrollTop] = useState(0);
  const [itemPositions, setItemPositions] = useState([]);
  const containerRef = useRef(null);

  // 计算每个项目的位置
  useEffect(() => {
    let currentPosition = 0;
    const positions = items.map((item, index) => {
      const itemHeight = estimateItemHeight(item, index);
      const position = currentPosition;
      currentPosition += itemHeight;
      return { index, position, height: itemHeight };
    });
    setItemPositions(positions);
  }, [items, estimateItemHeight]);

  // 计算可视区域内的项目
  const startIndex = itemPositions.findIndex(
    (pos) => pos.position + pos.height > scrollTop - overscan * 50
  );
  const endIndex = itemPositions.findLastIndex(
    (pos) => pos.position < scrollTop + height + overscan * 50
  );

  const visibleItems = items.slice(
    Math.max(0, startIndex),
    Math.min(items.length, endIndex + 1)
  );

  const totalHeight = itemPositions.length > 0
    ? itemPositions[itemPositions.length - 1].position +
      itemPositions[itemPositions.length - 1].height
    : 0;

  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn('overflow-auto', className)}
      style={{ height }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map((item, index) => {
          const actualIndex = Math.max(0, startIndex) + index;
          const position = itemPositions[actualIndex];
          return (
            <div
              key={actualIndex}
              style={{
                position: 'absolute',
                top: position?.position || 0,
                height: position?.height || 50,
                width: '100%',
              }}
            >
              {renderItem(item, actualIndex)}
            </div>
          );
        })}
      </div>
    </div>
  );
}


/**
 * 简化的虚拟列表组件
 * 使用简单API，自动处理常见情况
 */

export function VirtualList({
  items = [],
  height = 400,
  itemSize = 50,
  renderItem,
  className,
  ...props
}) {
  return (
    <VirtualScroll
      items={items}
      itemHeight={itemSize}
      height={height}
      renderItem={renderItem}
      className={className}
      {...props}
    );
}


export default VirtualScroll;
