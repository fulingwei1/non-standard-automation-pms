/**
 * 数据钻取容器组件
 * 支持图表点击下钻、面包屑导航、返回上级
 */

import { useState, useCallback, useMemo } from "react";
import {
  ChevronRight,
  ArrowLeft,
  Home,
  Maximize2,
  Minimize2 } from
"lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";

/**
 * DrillDownContainer - 数据钻取容器
 * @param {ReactNode} children - 子组件（图表）
 * @param {Array} levels - 钻取层级配置 [{ key: 'all', label: '全部', component: <Chart /> }, ...]
 * @param {function} onDrillDown - 下钻回调
 * @param {function} onDrillUp - 上钻回调
 * @param {string} title - 容器标题
 * @param {boolean} allowFullscreen - 是否允许全屏
 */
export default function DrillDownContainer({
  children,
  levels: _levels = [],
  onDrillDown,
  onDrillUp,
  title,
  allowFullscreen = true,
  className
}) {
  const [breadcrumb, setBreadcrumb] = useState([
  { key: "root", label: "全部" }]
  );
  const [currentLevel, setCurrentLevel] = useState(0);
  const [drillData, setDrillData] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 下钻
  const handleDrillDown = useCallback(
    (item) => {
      const newBreadcrumb = [
      ...breadcrumb,
      { key: item.key || item.id, label: item.label || item.name }];

      setBreadcrumb(newBreadcrumb);
      setCurrentLevel(currentLevel + 1);
      setDrillData(item);
      onDrillDown?.(item, currentLevel + 1);
    },
    [breadcrumb, currentLevel, onDrillDown]
  );

  // 上钻
  const handleDrillUp = useCallback(() => {
    if (breadcrumb.length > 1) {
      const newBreadcrumb = breadcrumb.slice(0, -1);
      setBreadcrumb(newBreadcrumb);
      setCurrentLevel(currentLevel - 1);
      setDrillData(null);
      onDrillUp?.(currentLevel - 1);
    }
  }, [breadcrumb, currentLevel, onDrillUp]);

  // 跳转到指定层级
  const handleBreadcrumbClick = useCallback(
    (index) => {
      if (index < breadcrumb.length - 1) {
        const newBreadcrumb = breadcrumb.slice(0, index + 1);
        setBreadcrumb(newBreadcrumb);
        setCurrentLevel(index);
        setDrillData(null);
        onDrillUp?.(index);
      }
    },
    [breadcrumb, onDrillUp]
  );

  // 切换全屏
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  // 渲染面包屑
  const renderBreadcrumb = () =>
  <div className="flex items-center gap-1 text-sm">
      {breadcrumb.map((item, index) =>
    <div key={item.key} className="flex items-center">
          {index > 0 &&
      <ChevronRight className="w-4 h-4 text-slate-500 mx-1" />
      }
          <button
        onClick={() => handleBreadcrumbClick(index)}
        className={cn(
          "px-2 py-1 rounded transition-colors",
          index === breadcrumb.length - 1 ?
          "text-white font-medium" :
          "text-slate-400 hover:text-white hover:bg-slate-700"
        )}>

            {index === 0 ? <Home className="w-4 h-4" /> : item.label}
          </button>
    </div>
    )}
  </div>;


  // 容器类名
  const containerClass = cn(
    "bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 rounded-lg overflow-hidden",
    isFullscreen && "fixed inset-4 z-50",
    className
  );

  return (
    <>
      <div className={containerClass}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
          <div className="flex items-center gap-4">
            {breadcrumb.length > 1 &&
            <button
              onClick={handleDrillUp}
              className="p-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors">

                <ArrowLeft className="w-4 h-4" />
            </button>
            }
            {title &&
            <h3 className="text-lg font-semibold text-white">{title}</h3>
            }
            {renderBreadcrumb()}
          </div>

          <div className="flex items-center gap-2">
            {currentLevel > 0 &&
            <span className="text-xs text-slate-400 bg-slate-700 px-2 py-1 rounded">
                第 {currentLevel + 1} 层
            </span>
            }
            {allowFullscreen &&
            <button
              onClick={toggleFullscreen}
              className="p-1.5 rounded-lg hover:bg-slate-700 text-slate-400 transition-colors">

                {isFullscreen ?
              <Minimize2 className="w-4 h-4" /> :

              <Maximize2 className="w-4 h-4" />
              }
            </button>
            }
          </div>
        </div>

        {/* Content */}
        <div className={cn("p-4", isFullscreen && "h-[calc(100%-60px)]")}>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentLevel}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="h-full">

              {typeof children === "function" ?
              children({
                level: currentLevel,
                data: drillData,
                onDrillDown: handleDrillDown
              }) :
              children}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      {/* Fullscreen Overlay */}
      {isFullscreen &&
      <div
        className="fixed inset-0 bg-black/60 z-40"
        onClick={toggleFullscreen} />

      }
    </>);

}

/**
 * DrillDownChart - 可钻取图表包装器
 * @param {object} chartProps - 图表属性
 * @param {ReactElement} chart - 图表组件
 * @param {function} onDrillDown - 下钻回调
 * @param {string} drillField - 钻取字段名
 */
export function DrillDownChart({
  chart: ChartComponent,
  chartProps,
  onDrillDown,
  drillField = "name"
}) {
  const handleClick = useCallback(
    (data) => {
      if (data && onDrillDown) {
        onDrillDown({
          key: data[drillField] || data.id,
          label: data[drillField] || data.name || data.type,
          data
        });
      }
    },
    [onDrillDown, drillField]
  );

  // 注入点击事件
  const enhancedProps = useMemo(
    () => ({
      ...chartProps,
      onPointClick: chartProps.onPointClick || handleClick,
      onBarClick: chartProps.onBarClick || handleClick,
      onSliceClick: chartProps.onSliceClick || handleClick
    }),
    [chartProps, handleClick]
  );

  return <ChartComponent {...enhancedProps} />;
}

/**
 * 使用示例:
 *
 * <DrillDownContainer
 *   title="销售数据分析"
 *   onDrillDown={(item, level) => console.log('Drill to:', item, level)}
 *   onDrillUp={(level) => console.log('Back to level:', level)}
 * >
 *   {({ level, data, onDrillDown }) => {
 *     if (level === 0) {
 *       return <PieChart data={regionData} onSliceClick={onDrillDown} />
 *     }
 *     if (level === 1) {
 *       return <BarChart data={cityData} onBarClick={onDrillDown} />
 *     }
 *     return <LineChart data={detailData} />
 *   }}
 * </DrillDownContainer>
 */