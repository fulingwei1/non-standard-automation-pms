/**
 * 物料详情卡片组件
 * 显示单个物料的详细分析信息
 */
import { Package, Truck, Clock, AlertTriangle, CheckCircle2, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { cn, formatDate } from '../../lib/utils';

/**
 * 物料详情卡片
 * @param {object} props
 * @param {object} props.material - 物料数据
 * @param {function} props.onClick - 点击回调
 */
export default function MaterialDetailCard({ material, onClick }) {
  const {
    material_code,
    material_name,
    specification,
    category_name,
    quantity,
    arrived_quantity,
    in_transit_quantity,
    status,
    supplier_name,
    planned_arrival_date,
    actual_arrival_date,
    is_delayed,
    delay_days,
  } = material;

  const totalQty = quantity || 0;
  const arrivedQty = arrived_quantity || 0;
  const inTransitQty = in_transit_quantity || 0;
  const notOrderedQty = totalQty - arrivedQty - inTransitQty;

  const progress = totalQty > 0 ? ((arrivedQty / totalQty) * 100).toFixed(1) : 0;

  const getStatusConfig = () => {
    if (is_delayed) {
      return {
        icon: AlertTriangle,
        label: `延期 ${delay_days || 0} 天`,
        color: 'bg-red-500/20 text-red-400 border-red-500/30',
      };
    }
    if (status === 'arrived') {
      return {
        icon: CheckCircle2,
        label: '已到货',
        color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      };
    }
    if (status === 'in_transit') {
      return {
        icon: Truck,
        label: '运输中',
        color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      };
    }
    if (status === 'not_ordered') {
      return {
        icon: Clock,
        label: '未采购',
        color: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      };
    }
    return {
      icon: Package,
      label: '未知',
      color: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    };
  };

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  return (
    <Card
      className={cn(
        'bg-slate-800/50 border transition-all hover:shadow-lg cursor-pointer',
        is_delayed ? 'border-red-500/30' : 'border-slate-700/50'
      )}
      onClick={() => onClick && onClick(material)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <CardTitle className="text-base text-white">{material_code}</CardTitle>
              <Badge className={statusConfig.color}>
                <StatusIcon className="w-3 h-3 mr-1" />
                {statusConfig.label}
              </Badge>
            </div>
            <div className="text-sm text-slate-400">{material_name}</div>
            {specification && (
              <div className="text-xs text-slate-500 mt-1">{specification}</div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* 分类和供应商 */}
        <div className="flex items-center justify-between text-sm">
          <div className="text-slate-400">
            {category_name && <span>分类: {category_name}</span>}
          </div>
          {supplier_name && (
            <div className="text-slate-400">
              供应商: {supplier_name}
            </div>
          )}
        </div>

        {/* 数量进度 */}
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-slate-400">到货进度</span>
            <span className="text-white font-medium">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
          <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
            <div>
              <span className="text-slate-500">计划: </span>
              <span className="text-white">{totalQty}</span>
            </div>
            <div>
              <span className="text-slate-500">已到: </span>
              <span className="text-emerald-400">{arrivedQty}</span>
            </div>
            <div>
              <span className="text-slate-500">在途: </span>
              <span className="text-blue-400">{inTransitQty}</span>
            </div>
          </div>
        </div>

        {/* 时间信息 */}
        <div className="flex items-center justify-between text-xs text-slate-400">
          {planned_arrival_date && (
            <div>
              计划到货: {formatDate(planned_arrival_date)}
            </div>
          )}
          {actual_arrival_date && (
            <div>
              实际到货: {formatDate(actual_arrival_date)}
            </div>
          )}
        </div>

        {/* 未采购提示 */}
        {notOrderedQty > 0 && (
          <div className="flex items-center gap-2 p-2 rounded bg-amber-500/10 border border-amber-500/20 text-xs">
            <Clock className="w-3 h-3 text-amber-400" />
            <span className="text-amber-400">还有 {notOrderedQty} 个未采购</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
