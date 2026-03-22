/**
 * Collapsible 折叠面板组件
 * 纯 Tailwind 实现，提供展开/收起内容区域的功能
 */

import * as React from "react";
import { cn } from "../../lib/utils";

/**
 * Collapsible 容器
 * @param {boolean} open - 控制展开/收起状态
 * @param {Function} onOpenChange - 状态变更回调
 */
const Collapsible = React.forwardRef(
  ({ className, open, onOpenChange, children, ...props }, ref) => (
    <div ref={ref} className={cn(className)} data-state={open ? "open" : "closed"} {...props}>
      {/* 通过 React context 向子组件传递 open 状态 */}
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child)) return child;
        return React.cloneElement(child, { "data-collapsible-open": open });
      })}
    </div>
  ),
);
Collapsible.displayName = "Collapsible";

/**
 * CollapsibleTrigger 触发按钮
 */
const CollapsibleTrigger = React.forwardRef(
  ({ className, children, ...props }, ref) => (
    <button ref={ref} type="button" className={cn(className)} {...props}>
      {children}
    </button>
  ),
);
CollapsibleTrigger.displayName = "CollapsibleTrigger";

/**
 * CollapsibleContent 可折叠内容区域
 * 根据父级传入的 data-collapsible-open 控制显隐
 */
const CollapsibleContent = React.forwardRef(
  ({ className, children, "data-collapsible-open": open, ...props }, ref) => {
    if (!open) return null;

    return (
      <div
        ref={ref}
        className={cn("overflow-hidden", className)}
        {...props}
      >
        {children}
      </div>
    );
  },
);
CollapsibleContent.displayName = "CollapsibleContent";

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
