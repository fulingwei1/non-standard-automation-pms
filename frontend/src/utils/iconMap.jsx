/**
 * 图标映射表和动态图标组件
 * 集中管理所有动态图标的渲染，避免 React 大小写警告
 */

import * as LucideIcons from 'lucide-react';

/**
 * 图标映射表：将字符串名称映射到实际的 React 组件
 */
export const iconMap = {
  // 常用图标
  FileText: LucideIcons.FileText,
  CheckCircle2: LucideIcons.CheckCircle2,
  CheckCircle: LucideIcons.CheckCircle,
  XCircle: LucideIcons.XCircle,
  AlertCircle: LucideIcons.AlertCircle,
  AlertTriangle: LucideIcons.AlertTriangle,
  Clock: LucideIcons.Clock,
  Calendar: LucideIcons.Calendar,
  User: LucideIcons.User,
  Users: LucideIcons.Users,
  Building: LucideIcons.Building,
  Building2: LucideIcons.Building2,
  Package: LucideIcons.Package,
  Truck: LucideIcons.Truck,
  DollarSign: LucideIcons.DollarSign,
  TrendingUp: LucideIcons.TrendingUp,
  TrendingDown: LucideIcons.TrendingDown,
  
  // 操作图标
  Search: LucideIcons.Search,
  Filter: LucideIcons.Filter,
  Plus: LucideIcons.Plus,
  Minus: LucideIcons.Minus,
  Edit: LucideIcons.Edit,
  Edit2: LucideIcons.Edit2,
  Edit3: LucideIcons.Edit3,
  Trash: LucideIcons.Trash,
  Trash2: LucideIcons.Trash2,
  Eye: LucideIcons.Eye,
  Copy: LucideIcons.Copy,
  Send: LucideIcons.Send,
  Download: LucideIcons.Download,
  Upload: LucideIcons.Upload,
  Save: LucideIcons.Save,
  X: LucideIcons.X,
  Check: LucideIcons.Check,
  ChevronLeft: LucideIcons.ChevronLeft,
  ChevronRight: LucideIcons.ChevronRight,
  ChevronUp: LucideIcons.ChevronUp,
  ChevronDown: LucideIcons.ChevronDown,
  MoreHorizontal: LucideIcons.MoreHorizontal,
  MoreVertical: LucideIcons.MoreVertical,
  
  // 状态图标
  Circle: LucideIcons.Circle,
  Dot: LucideIcons.Dot,
  Square: LucideIcons.Square,
  Star: LucideIcons.Star,
  Heart: LucideIcons.Heart,
  
  // 通讯图标
  MessageSquare: LucideIcons.MessageSquare,
  MessageCircle: LucideIcons.MessageCircle,
  Mail: LucideIcons.Mail,
  Phone: LucideIcons.Phone,
  
  // 导航图标
  Home: LucideIcons.Home,
  Settings: LucideIcons.Settings,
  Menu: LucideIcons.Menu,
  Grid: LucideIcons.Grid,
  List: LucideIcons.List,
  
  // 其他常用图标
  Info: LucideIcons.Info,
  HelpCircle: LucideIcons.HelpCircle,
  Loader: LucideIcons.Loader,
  Loader2: LucideIcons.Loader2,
  RefreshCw: LucideIcons.RefreshCw,
  ExternalLink: LucideIcons.ExternalLink,
  Link: LucideIcons.Link,
  Archive: LucideIcons.Archive,
  History: LucideIcons.History,
  
  // 按需添加其他图标
};

/**
 * 动态图标组件
 * 根据图标名称动态渲染对应的图标组件
 * 
 * @param {Object} props
 * @param {string} props.name - 图标名称（字符串）
 * @param {Object} props... - 其他传递给图标组件的 props（如 className, size 等）
 * @returns {React.Component|null} - 图标组件或 null
 * 
 * @example
 * // ❌ 之前
 * <{iconName} className="w-4 h-4" />
 * 
 * // ✅ 现在
 * <DynamicIcon name={iconName} className="w-4 h-4" />
 */
export const DynamicIcon = ({ name, ...props }) => {
  if (!name) {
    return null;
  }

  const IconComponent = iconMap[name];
  
  if (!IconComponent) {
    console.warn(`[DynamicIcon] 未找到图标: ${name}`);
    return null;
  }

  return <IconComponent {...props} />;
};

/**
 * 根据图标名称获取图标组件（向后兼容）
 * @param {string} iconName - 图标名称（字符串）
 * @returns {React.Component} - 图标组件，如果未找到则返回 Package
 */
export function getIcon(iconName) {
  if (!iconName || typeof iconName !== 'string') {
    return iconMap.Package;
  }
  return iconMap[iconName] || iconMap.Package;
}

/**
 * 统一解析图标（支持字符串或组件）
 * @param {string|Function|Object|null|undefined} icon
 * @param {Function|null} fallback
 * @returns {Function|null}
 */
export function resolveIcon(icon, fallback = iconMap.Package) {
  if (!icon) {
    return fallback;
  }

  if (typeof icon === "string") {
    return getIcon(icon);
  }

  const iconName = icon.displayName || icon.name;
  if (iconName && typeof iconName === "string") {
    return getIcon(iconName);
  }

  return icon;
}

// 重新导出所有 Lucide 图标供直接使用
export * from 'lucide-react';
