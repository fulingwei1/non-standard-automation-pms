/**
 * NavItem - 导航项组件（优化性能）
 * 使用 memo 避免不必要的重渲染
 * 支持权限控制：无权限时显示置灰状态和提示
 */
import { memo } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { Star, Lock } from "lucide-react";
import { Box } from "lucide-react";

const NavItem = memo(function NavItem({
  item,
  iconMap,
  collapsed = false,
  isFavorite = false,
  onToggleFavorite,
  activePath,
  disabled = false,
  disabledReason = "",
}) {
  const location = useLocation();
  const isActive = !disabled && (location.pathname === item.path || activePath === item.path);
  const Icon = iconMap[item.icon] || Box;

  // 禁用状态的内容
  const content = (
    <>
      {/* Active indicator */}
      {isActive && (
        <motion.div
          layoutId="activeNav"
          className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-full bg-primary"
          transition={{ type: "spring", duration: 0.5 }}
        />
      )}

      <Icon
        className={cn(
          "h-5 w-5 flex-shrink-0",
          disabled
            ? "text-slate-600"
            : isActive
              ? "text-primary"
              : "text-slate-500 group-hover:text-slate-300",
        )}
      />

      <AnimatePresence>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            className={cn(
              "whitespace-nowrap overflow-hidden flex-1",
              disabled && "text-slate-600"
            )}
          >
            {item.name}
          </motion.span>
        )}
      </AnimatePresence>

      {/* Lock icon for disabled items */}
      {disabled && !collapsed && (
        <Lock className="h-3.5 w-3.5 text-slate-600 ml-auto" />
      )}

      {/* Badge */}
      {item.badge && !collapsed && !disabled && (
        <span className="ml-auto px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400">
          {item.badge}
        </span>
      )}

      {/* Favorite button */}
      {!collapsed && !item.badge && !disabled && onToggleFavorite && (
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onToggleFavorite(item.path, item.name, item.icon);
          }}
          className={cn(
            "opacity-0 group-hover:opacity-100 transition-opacity",
            "p-1 rounded hover:bg-white/10 ml-auto",
          )}
          title={isFavorite ? "取消收藏" : "收藏"}
        >
          <Star
            className={cn(
              "h-4 w-4",
              isFavorite
                ? "text-yellow-400 fill-yellow-400"
                : "text-slate-500 hover:text-yellow-400",
            )}
          />
        </button>
      )}

      {/* Tooltip for collapsed state */}
      {collapsed && (
        <div
          className={cn(
            "absolute left-full ml-2 px-3 py-1.5 rounded-lg",
            "bg-surface-200 text-sm whitespace-nowrap",
            "opacity-0 invisible group-hover:opacity-100 group-hover:visible",
            "transition-all duration-200 z-50",
            disabled ? "text-slate-400" : "text-white"
          )}
        >
          {item.name}
          {disabled && disabledReason && (
            <div className="text-xs text-slate-500 mt-0.5">
              需要「{disabledReason}」权限
            </div>
          )}
          <div className="absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-surface-200 rotate-45" />
        </div>
      )}

      {/* Tooltip for expanded disabled state */}
      {!collapsed && disabled && disabledReason && (
        <div
          className={cn(
            "absolute left-full ml-2 px-3 py-1.5 rounded-lg",
            "bg-surface-200 text-sm whitespace-nowrap text-slate-400",
            "opacity-0 invisible group-hover:opacity-100 group-hover:visible",
            "transition-all duration-200 z-50",
          )}
        >
          需要「{disabledReason}」权限
          <div className="absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-surface-200 rotate-45" />
        </div>
      )}
    </>
  );

  // 禁用状态使用 div，正常状态使用 Link
  if (disabled) {
    return (
      <div className="relative group">
        <div
          className={cn(
            "relative flex items-center gap-3 px-3 py-2.5 rounded-xl",
            "text-sm font-medium transition-all duration-200",
            "text-slate-600 cursor-not-allowed",
            collapsed && "justify-center",
          )}
        >
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="relative group">
      <Link
        to={item.path}
        className={cn(
          "relative flex items-center gap-3 px-3 py-2.5 rounded-xl",
          "text-sm font-medium transition-all duration-200",
          isActive
            ? "text-white bg-white/[0.08]"
            : "text-slate-400 hover:text-white hover:bg-white/[0.04]",
          collapsed && "justify-center",
        )}
      >
        {content}
      </Link>
    </div>
  );
});

NavItem.displayName = "NavItem";

export default NavItem;
