/**
 * NavItem - 导航项组件（优化性能）
 * 使用 memo 避免不必要的重渲染
 */
import { memo } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { Star } from "lucide-react";
import { Box } from "lucide-react";

const NavItem = memo(function NavItem({
  item,
  iconMap,
  collapsed = false,
  isFavorite = false,
  onToggleFavorite,
  activePath,
}) {
  const location = useLocation();
  const isActive = location.pathname === item.path || activePath === item.path;
  const Icon = iconMap[item.icon] || Box;

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
            isActive
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
              className="whitespace-nowrap overflow-hidden flex-1"
            >
              {item.name}
            </motion.span>
          )}
        </AnimatePresence>

        {/* Badge */}
        {item.badge && !collapsed && (
          <span className="ml-auto px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400">
            {item.badge}
          </span>
        )}

        {/* Favorite button */}
        {!collapsed && !item.badge && onToggleFavorite && (
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
              "bg-surface-200 text-white text-sm whitespace-nowrap",
              "opacity-0 invisible group-hover:opacity-100 group-hover:visible",
              "transition-all duration-200 z-50",
            )}
          >
            {item.name}
            <div className="absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-surface-200 rotate-45" />
          </div>
        )}
      </Link>
    </div>
  );
});

NavItem.displayName = "NavItem";

export default NavItem;
