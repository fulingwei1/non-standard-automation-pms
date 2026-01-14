/**
 * NavGroup - 导航组组件（优化性能）
 * 使用 memo 避免不必要的重渲染
 */
import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import NavItem from "./NavItem";

const NavGroup = memo(function NavGroup({
  group,
  iconMap,
  collapsed = false,
  isGroupCollapsed = false,
  favorites = [],
  onToggleFavorite,
  onToggleCollapse,
  activePath,
}) {
  return (
    <div className="mb-6">
      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center justify-between px-3 mb-2 group/header"
          >
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
              {group.label}
            </p>
            <button
              onClick={() => onToggleCollapse(group.label)}
              className={cn(
                "opacity-0 group-hover/header:opacity-100 transition-opacity",
                "p-1 rounded hover:bg-white/10",
              )}
              title={isGroupCollapsed ? "展开" : "折叠"}
            >
              {isGroupCollapsed ? (
                <ChevronDown className="h-4 w-4 text-slate-500" />
              ) : (
                <ChevronUp className="h-4 w-4 text-slate-500" />
              )}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {(!isGroupCollapsed || collapsed) && (
          <motion.div
            initial={
              !collapsed && isGroupCollapsed
                ? { height: 0, opacity: 0 }
                : { height: "auto", opacity: 1 }
            }
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="space-y-1 overflow-hidden"
          >
            {group.items.map((item) => {
              const isFavorite = favorites.some((fav) => fav.path === item.path);
              return (
                <NavItem
                  key={item.path}
                  item={item}
                  iconMap={iconMap}
                  collapsed={collapsed}
                  isFavorite={isFavorite}
                  onToggleFavorite={onToggleFavorite}
                  activePath={activePath}
                />
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

NavGroup.displayName = "NavGroup";

export default NavGroup;
