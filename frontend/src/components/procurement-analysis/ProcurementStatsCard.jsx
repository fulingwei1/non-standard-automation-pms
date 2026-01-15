/**
 * 采购分析统计卡片组件
 * 用于显示各种统计数据
 */
import { Card, CardContent } from '../ui/card';

// 图标导入
import {
  DollarSign,
  ShoppingCart,
  Truck,
  Award,
  Clock,
  AlertTriangle,
  BarChart3,
  TrendingUp,
} from 'lucide-react';

// 图标映射
const ICON_COMPONENTS = {
  DollarSign,
  ShoppingCart,
  Truck,
  Award,
  Clock,
  AlertTriangle,
  BarChart3,
  TrendingUp,
};

/**
 * 统计卡片组件
 * @param {object} props
 * @param {string} props.label - 标签
 * @param {string|number} props.value - 值
 * @param {string} props.icon - 图标名称
 * @param {string} props.color - 颜色名称 (emerald, blue, purple, amber)
 * @param {string} props.suffix - 后缀
 * @param {string} props.subtitle - 副标题
 * @param {React.ReactNode} props.rating - 评级显示
 */
export default function ProcurementStatsCard({
  label,
  value,
  icon,
  color = 'blue',
  suffix = '',
  subtitle = '',
  rating = null,
}) {
  const IconComponent = ICON_COMPONENTS[icon];

  const colorClasses = {
    emerald: 'text-emerald-500',
    blue: 'text-blue-500',
    purple: 'text-purple-500',
    amber: 'text-amber-500',
    red: 'text-red-500',
  };

  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-slate-400">{label}</div>
            <div className="text-2xl font-bold text-white mt-1">
              {rating || (
                value !== undefined && value !== null
                  ? `${typeof value === 'number' && !isNaN(value) ? value.toLocaleString() : value}${suffix}`
                  : '-'
              )}
            </div>
            {subtitle && (
              <div className="text-xs text-slate-500 mt-1">{subtitle}</div>
            )}
          </div>
          {IconComponent && (
            <IconComponent className={`w-10 h-10 ${colorClasses[color] || colorClasses.blue}`} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
