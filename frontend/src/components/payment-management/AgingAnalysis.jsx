/**
 * 账龄分析组件
 * 显示应收账款的账龄分布
 */
import { Card, CardContent, Progress } from '../ui';
import { cn } from '../../lib/utils';
import { formatCurrency } from './paymentManagementConstants';

/**
 * 账龄分析组件
 * @param {object} props
 * @param {object} props.agingData - 账龄数据
 */
export default function AgingAnalysis({ agingData }) {
  const agingItems = [
    { key: 'current', label: '当前', ...agingData.current },
    { key: 'days_1_30', label: '1-30天', ...agingData.days_1_30 },
    { key: 'days_31_60', label: '31-60天', ...agingData.days_31_60 },
    { key: 'days_61_90', label: '61-90天', ...agingData.days_61_90 },
    { key: 'days_over_90', label: '90天以上', ...agingData.days_over_90 },
  ];

  const totalAmount = Object.values(agingData).reduce((sum, d) => sum + (d.amount || 0), 0);

  return (
    <div className="space-y-4">
      {agingItems.map((item) => (
        <Card
          key={item.key}
          className={cn(
            'bg-slate-800/50 border',
            item.key === 'days_over_90'
              ? 'border-red-500/30'
              : item.key === 'days_61_90'
              ? 'border-orange-500/30'
              : 'border-slate-700/50'
          )}
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-white font-medium">{item.label}</h4>
                <p className="text-slate-400 text-sm">
                  {item.count || 0} 笔付款
                </p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-white">
                  {formatCurrency(item.amount || 0)}
                </div>
                <Progress
                  value={totalAmount > 0 ? ((item.amount || 0) / totalAmount) * 100 : 0}
                  className="w-24 h-2 mt-1"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
