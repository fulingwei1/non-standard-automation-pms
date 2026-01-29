/**
 * 图标映射表和动态图标组件
 * 集中管理所有动态图标的渲染，避免 React 大小写警告
 */

import {
  CheckCircle2,
  FileText,
  Clock,
  Truck,
  AlertTriangle,
  Package,
  Trash2,
  Eye,
  Edit3,
  AlertCircle,
  XCircle,
  Info,
  Circle,
  MessageSquare,
  CheckCircle,
  Send,
  // 按需添加其他图标
} from 'lucide-react';

/**
 * 图标映射表：将字符串名称映射到实际的 React 组件
 */
export const iconMap = {
  CheckCircle2,
  FileText,
  Clock,
  Truck,
  AlertTriangle,
  Package,
  Trash2,
  Eye,
  Edit3,
  AlertCircle,
  XCircle,
  Info,
  Circle,
  MessageSquare,
  CheckCircle,
  Send,
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
    return Package;
  }
  return iconMap[iconName] || Package;
}
