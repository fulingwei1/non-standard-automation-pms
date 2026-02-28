/**
 * VirtualizedList - 虚拟滚动列表组件
 * 用于优化长列表的渲染性能，只渲染可见区域的项
 *
 * @param {Object} props
 * @param {Array} props.items - 列表数据
 * @param {number|Function} props.itemHeight - 每项高度或计算函数
 * @param {number} props.containerHeight - 容器高度
 * @param {Function} props.renderItem - 渲染函数 (item, index) => ReactNode
 * @param {number} props.overscan - 额外渲染的项数（上下各渲染多少项）
 * @param {string} props.className - 容器CSS类名
 * @param {Function} props.onScroll - 滚动回调
 */
import { useMemo, useRef, useState } from "react";
import { cn } from "../../lib/utils";

export function VirtualizedList({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 3,
  className,
  onScroll,
}) {
  const containerRef = useRef(null);
  const [scrollTop, setScrollTop] = useState(0);

  // 计算每个项的高度
  const getItemHeight = (index) => {
    if (typeof itemHeight === "function") {
      return itemHeight(index);
    }
    return itemHeight;
  };

  // 计算总高度
  const totalHeight = useMemo(() => {
    return (items || []).reduce((sum, _, index) => sum + getItemHeight(index), 0);
  }, [items, itemHeight]);

  // 计算可见范围
  const { startIndex, endIndex, offsetY } = useMemo(() => {
    let currentTop = 0;
    let start = 0;
    let end = 0;

    // 找到起始索引
    for (let i = 0; i < items?.length; i++) {
      const height = getItemHeight(i);
      if (currentTop + height > scrollTop) {
        start = Math.max(0, i - overscan);
        break;
      }
      currentTop += height;
    }

    // 找到结束索引
    let visibleTop = currentTop;
    for (let i = start; i < items?.length; i++) {
      const height = getItemHeight(i);
      if (visibleTop > scrollTop + containerHeight) {
        end = Math.min(items?.length, i + overscan);
        break;
      }
      visibleTop += height;
      end = i + 1;
    }

    // 计算偏移量
    let offset = 0;
    for (let i = 0; i < start; i++) {
      offset += getItemHeight(i);
    }

    return {
      startIndex: start,
      endIndex: Math.min(items?.length, end + overscan),
      offsetY: offset,
    };
  }, [scrollTop, containerHeight, items, overscan, itemHeight]);

  // 处理滚动
  const handleScroll = (e) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);
    if (onScroll) {
      onScroll(newScrollTop);
    }
  };

  // 可见项
  const visibleItems = useMemo(() => {
    return items.slice(startIndex, endIndex).map((item, index) => ({
      item,
      index: startIndex + index,
    }));
  }, [items, startIndex, endIndex]);

  if (items?.length === 0) {
    return (
      <div
        className={cn("flex items-center justify-center", className)}
        style={{ height: containerHeight }}
      >
        <p className="text-slate-500">暂无数据</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn("overflow-auto", className)}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: "relative" }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {(visibleItems || []).map(({ item, index }) => (
            <div key={index} style={{ height: getItemHeight(index) }}>
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default VirtualizedList;
