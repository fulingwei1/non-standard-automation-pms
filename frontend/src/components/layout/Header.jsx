import { useMemo } from "react";
import { cn } from "../../lib/utils";
import {
  Search,
  Bell,
  ChevronDown,
  Settings,
  User,
  LogOut,
  Command,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { getRoleInfo } from "../../lib/roleConfig";

export function Header({ sidebarCollapsed = false, user, onLogout }) {
  // Get user from localStorage if not provided
  const currentUser = useMemo(() => {
    try {
      if (user) {return user;}
      const userStr = localStorage.getItem("user");
      if (userStr) {
        return JSON.parse(userStr);
      }
      return null;
    } catch (e) {
      console.warn("Failed to parse user from localStorage:", e);
      return null;
    }
  }, [user]);

  // Get welcome message based on time of day
  const welcomeMessage = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 6) {return "夜深了，注意休息";}
    if (hour < 9) {return "早上好";}
    if (hour < 12) {return "上午好";}
    if (hour < 14) {return "中午好";}
    if (hour < 18) {return "下午好";}
    if (hour < 22) {return "晚上好";}
    return "夜深了，注意休息";
  }, []);

  const roleInfo = useMemo(() => {
    if (!currentUser) {return null;}
    const hasUser =
      currentUser?.id ||
      currentUser?.username ||
      currentUser?.real_name ||
      currentUser?.name;
    if (!hasUser) {
      return getRoleInfo("unknown");
    }
    const role =
      currentUser.role ||
      currentUser.role_code ||
      currentUser.role_name ||
      (Array.isArray(currentUser.roles) && currentUser.roles.length > 0
        ? currentUser.roles[0]
        : "unknown");
    return getRoleInfo(role);
  }, [currentUser]);

  const displayName = currentUser?.real_name || currentUser?.name || currentUser?.username || "用户";
  const displayUsername = currentUser?.username || "";
  const displayRole = roleInfo?.name || "";

  return (
    <header
      className={cn(
        "fixed top-0 right-0 z-30",
        "h-16 flex items-center justify-between px-6",
        "bg-surface-0/80 backdrop-blur-xl",
        "border-b border-white/5",
        "transition-all duration-300",
        sidebarCollapsed ? "left-[72px]" : "left-60",
      )}
    >
      {/* Welcome Message & Search */}
      <div className="flex items-center gap-4 flex-1">
        {/* Welcome Message */}
        <div className="hidden md:block text-sm text-slate-400">
          <span className="text-white font-medium">{welcomeMessage}</span>
          {displayName && displayName !== "用户" && (
            <span className="ml-2">，{displayName}</span>
          )}
        </div>

        {/* Search */}
        <button
          onClick={() => {}}
          className={cn(
            "flex items-center gap-3 px-4 py-2 rounded-xl",
            "bg-white/[0.03] border border-white/10",
            "text-sm text-slate-400",
            "hover:bg-white/[0.05] hover:border-white/15",
            "transition-all duration-200",
            "min-w-[280px]",
          )}
        >
          <Search className="h-4 w-4" />
          <span>搜索项目、设备...</span>
          <div className="ml-auto flex items-center gap-1 text-xs text-slate-500">
            <Command className="h-3 w-3" />
            <span>K</span>
          </div>
        </button>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button
          className={cn(
            "relative p-2.5 rounded-xl",
            "text-slate-400 hover:text-white",
            "hover:bg-white/[0.05]",
            "transition-colors duration-200",
          )}
        >
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500" />
        </button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className={cn(
                "flex items-center gap-3 pl-3 pr-2 py-1.5 rounded-xl",
                "hover:bg-white/[0.05]",
                "transition-colors duration-200",
              )}
            >
              <Avatar className="h-8 w-8">
                {currentUser?.avatar && (
                  <AvatarImage src={currentUser.avatar} />
                )}
                <AvatarFallback className="bg-gradient-to-br from-violet-600 to-indigo-600 text-white text-sm">
                  {displayName[0]?.toUpperCase() || "用"}
                </AvatarFallback>
              </Avatar>
              <div className="text-left">
                <p className="text-sm font-medium text-white">{displayName}</p>
                <p className="text-xs text-slate-500">
                  {displayUsername || displayRole || "用户"}
                </p>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-500" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuItem>
              <User className="h-4 w-4 mr-2" />
              个人信息
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="h-4 w-4 mr-2" />
              账户设置
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-400" onClick={onLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

export default Header;
