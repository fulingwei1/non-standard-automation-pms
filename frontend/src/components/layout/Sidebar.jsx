import { useMemo, useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { roleApi } from "../../services/api";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { useDebounce } from "../../hooks/useDebounce";
import { usePermission } from "../../hooks/usePermission";
import NavGroup from "./NavGroup";
import NavItem from "./NavItem";
import { getRoleInfo } from "../../lib/roleConfig";
import {
  Box,
  ChevronLeft,
  LogOut,
  User,
  Search,
  X
} from "lucide-react";

// Import from extracted modules
import { iconMap } from "./sidebarIcons";
import { filterNavItemsByRole, getNavGroupsForRole } from "./sidebarUtils";

export function Sidebar({ collapsed = false, onToggle, onLogout, user }) {
  const location = useLocation();

  // 获取权限检查函数
  const { hasPermission } = usePermission();

  // State for dynamic menu from backend
  const [dynamicNavGroups, setDynamicNavGroups] = useState(null);
  const [_menuLoading, setMenuLoading] = useState(false);

  // Menu search state with debounce
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearchQuery = useDebounce(searchQuery, 300);

  // Module collapse state (stored in localStorage)
  // Default: all groups expanded (false means not collapsed, i.e., expanded)
  const [collapsedGroups, setCollapsedGroups] = useState(() => {
    try {
      const saved = localStorage.getItem("sidebar_collapsed_groups");
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  // Favorite menu items (stored in localStorage)
  const [favorites, setFavorites] = useState(() => {
    try {
      const saved = localStorage.getItem("sidebar_favorites");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Get user role from localStorage if not provided - memoized
  const currentUser = useMemo(() => {
    try {
      return user || JSON.parse(localStorage.getItem("user") || "{}");
    } catch (e) {
      console.warn("Failed to parse user from localStorage:", e);
      return {};
    }
  }, [user]);

  const role = useMemo(() => {
    const hasUser =
      currentUser?.id ||
      currentUser?.username ||
      currentUser?.real_name ||
      currentUser?.name;
    if (!hasUser) {
      return "unknown";
    }
    if (currentUser?.role) {
      return currentUser.role;
    }
    if (currentUser?.role_code || currentUser?.role_name) {
      return currentUser.role_code || currentUser.role_name;
    }
    const roles = currentUser?.roles;
    if (Array.isArray(roles) && roles.length > 0) {
      const firstRole = roles[0];
      if (typeof firstRole === "string") {
        return firstRole;
      }
      return firstRole?.role_code || firstRole?.role_name || firstRole?.name;
    }
    return "unknown";
  }, [currentUser]);
  const isSuperuser = useMemo(
    () =>
      currentUser?.is_superuser === true || currentUser?.isSuperuser === true,
    [currentUser]
  );
  const roleInfo = useMemo(() => getRoleInfo(role), [role]);

  // Fetch dynamic menu from backend
  useEffect(() => {
    const fetchDynamicMenu = async () => {
      // Skip if no token (not logged in)
      const token = localStorage.getItem("token");
      if (!token) {
        return;
      }

      // 如果是演示账号，不调用真实API，直接使用默认菜单
      if (token.startsWith("demo_token_")) {
        console.log("[Sidebar] 演示账号，使用默认菜单");
        setMenuLoading(false);
        return;
      }

      setMenuLoading(true);
      try {
        const response = await roleApi.getMyNavGroups();
        // 使用统一响应格式处理
        const data = response.formatted || response.data;
        // Only use dynamic menu if it has content
        if (data?.nav_groups && data.nav_groups.length > 0) {
          setDynamicNavGroups(data.nav_groups);
        }
      } catch (error) {
        // Silently fail and use default menu
        console.warn("Failed to fetch dynamic menu, using default:", error);
      } finally {
        setMenuLoading(false);
      }
    };

    fetchDynamicMenu();
  }, [currentUser]);

  // Get navigation groups based on role - memoized
  // Priority: dynamic menu from backend > hardcoded menu based on role
  const navGroups = useMemo(() => {
    // If we have dynamic menu from backend, use it
    if (dynamicNavGroups && dynamicNavGroups.length > 0) {
      return dynamicNavGroups;
    }
    // Otherwise, fall back to hardcoded menu
    const groups = getNavGroupsForRole(role, isSuperuser);
    return filterNavItemsByRole(groups, role, isSuperuser);
  }, [role, isSuperuser, dynamicNavGroups]);

  // Toggle group collapse
  const toggleGroupCollapse = (groupLabel) => {
    setCollapsedGroups((prev) => {
      const newState = { ...prev, [groupLabel]: !prev[groupLabel] };
      localStorage.setItem(
        "sidebar_collapsed_groups",
        JSON.stringify(newState)
      );
      return newState;
    });
  };

  // Toggle favorite
  const toggleFavorite = (itemPath, itemName, itemIcon) => {
    setFavorites((prev) => {
      const isFavorite = prev.some((fav) => fav.path === itemPath);
      let newFavorites;
      if (isFavorite) {
        newFavorites = prev.filter((fav) => fav.path !== itemPath);
      } else {
        newFavorites = [
          ...prev,
          { path: itemPath, name: itemName, icon: itemIcon }
        ];
      }
      localStorage.setItem("sidebar_favorites", JSON.stringify(newFavorites));
      return newFavorites;
    });
  };

  // Filter menu items based on search query (using debounced value)
  const filteredNavGroups = useMemo(() => {
    if (!debouncedSearchQuery.trim()) {
      return navGroups;
    }

    const query = debouncedSearchQuery.toLowerCase();
    return navGroups
      .map((group) => {
        const filteredItems = group.items.filter(
          (item) =>
            item.name.toLowerCase().includes(query) ||
            item.path.toLowerCase().includes(query) ||
            group.label.toLowerCase().includes(query)
        );
        return {
          ...group,
          items: filteredItems
        };
      })
      .filter((group) => group.items.length > 0);
  }, [navGroups, debouncedSearchQuery]);

  // Get favorite items as a group
  const favoriteGroup = useMemo(() => {
    if (favorites.length === 0) {
      return null;
    }
    return {
      label: "我的收藏",
      items: favorites.map((fav) => ({
        name: fav.name,
        path: fav.path,
        icon: fav.icon
      }))
    };
  }, [favorites]);

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen z-40",
        "flex flex-col",
        "bg-surface-50/80 backdrop-blur-xl",
        "border-r border-white/5",
        "transition-all duration-300 ease-out",
        collapsed ? "w-[72px]" : "w-60"
      )}
    >
      {/* Logo */}
      <div
        className={cn("flex items-center h-16 px-4", "border-b border-white/5")}
      >
        <div
          className={cn(
            "flex items-center justify-center",
            "w-10 h-10 rounded-xl",
            "bg-gradient-to-br from-violet-600 to-indigo-600",
            "shadow-lg shadow-violet-500/30"
          )}
        >
          <Box className="h-5 w-5 text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              className="ml-3 text-lg font-semibold text-white whitespace-nowrap overflow-hidden"
            >
              PMS 系统
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Role indicator */}
      {!collapsed && (
        <div className="px-4 py-3 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 flex items-center justify-center">
              <User className="w-4 h-4 text-violet-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {currentUser?.name || "用户"}
              </p>
              <p className="text-xs text-slate-500 truncate">{roleInfo.name}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search box */}
      {!collapsed && (
        <div className="px-3 py-3 border-b border-white/5">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="搜索菜单..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                "w-full pl-9 pr-8 py-2 rounded-lg",
                "bg-surface-100/50 border border-white/10",
                "text-sm text-white placeholder:text-slate-500",
                "focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50",
                "transition-all duration-200"
              )}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-white/10 transition-colors"
              >
                <X className="h-4 w-4 text-slate-500" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto custom-scrollbar py-4 px-3">
        {/* Favorite items section */}
        {!collapsed && favoriteGroup && (
          <div className="mb-6">
            <div className="flex items-center justify-between px-3 mb-2">
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-xs font-medium text-slate-500 uppercase tracking-wider"
              >
                {favoriteGroup.label}
              </motion.p>
            </div>
            <div className="space-y-1">
              {favoriteGroup.items.map((item) => (
                <NavItem
                  key={item.path}
                  item={item}
                  iconMap={iconMap}
                  collapsed={collapsed}
                  isFavorite
                  onToggleFavorite={toggleFavorite}
                  activePath={location.pathname}
                />
              ))}
            </div>
          </div>
        )}

        {/* Regular menu groups */}
        {filteredNavGroups.map((group, gi) => {
          // Default to expanded (false means not collapsed)
          const isGroupCollapsed = collapsedGroups[group.label] === true;
          return (
            <NavGroup
              key={gi}
              group={group}
              iconMap={iconMap}
              collapsed={collapsed}
              isGroupCollapsed={isGroupCollapsed}
              favorites={favorites}
              onToggleFavorite={toggleFavorite}
              onToggleCollapse={toggleGroupCollapse}
              activePath={location.pathname}
              checkPermission={hasPermission}
            />
          );
        })}

        {/* No results message */}
        {!collapsed &&
          debouncedSearchQuery &&
          filteredNavGroups.length === 0 && (
            <div className="px-3 py-8 text-center">
              <p className="text-sm text-slate-500">未找到匹配的菜单项</p>
            </div>
          )}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-white/5 space-y-1">
        {onLogout && (
          <button
            onClick={onLogout}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl",
              "text-sm font-medium text-red-400",
              "hover:text-red-300 hover:bg-red-500/10",
              "transition-all duration-200",
              collapsed && "justify-center"
            )}
          >
            <LogOut className="h-5 w-5" />
            {!collapsed && <span>退出登录</span>}
          </button>
        )}

        {onToggle && (
          <button
            onClick={onToggle}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl",
              "text-sm font-medium text-slate-400",
              "hover:text-white hover:bg-white/[0.04]",
              "transition-all duration-200",
              collapsed && "justify-center"
            )}
          >
            <ChevronLeft
              className={cn(
                "h-5 w-5 transition-transform duration-300",
                collapsed && "rotate-180"
              )}
            />
            {!collapsed && <span>收起侧边栏</span>}
          </button>
        )}
      </div>
    </aside>
  );
}

export default Sidebar;
