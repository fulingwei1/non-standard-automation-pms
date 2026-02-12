/**
 * 采购申请处理时效分析 Tab 组件
 * 显示采购申请处理统计和时效详情
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import ProcurementStatsCard from './ProcurementStatsCard';
import { STATS_CARD_CONFIGS } from '@/lib/constants/procurementAnalysis';

/**
 * 采购时效 Tab 组件
 * @param {object} props
 * @param {object} props.data - 采购时效数据
 */
export default function RequestEfficiencyTab({ data }) {
  const { summary, efficiency_data } = data || {};

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {STATS_CARD_CONFIGS.requestEfficiency.map(config => (
            <ProcurementStatsCard
              key={config.key}
              label={config.label}
              value={summary[config.key]}
              icon={config.icon}
              color={config.color}
              suffix={config.suffix || ''}
            />
          ))}
        </div>
      )}

      {/* 处理时效详情 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>采购申请处理时效详情</CardTitle>
          <CardDescription>按处理时长降序排列</CardDescription>
        </CardHeader>
        <CardContent>
          {efficiency_data?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">申请单号</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">状态</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">申请金额</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">处理时长</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">申请时间</th>
                  </tr>
                </thead>
                <tbody>
                  {efficiency_data.map((item, index) => (
                    <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4 font-medium">{item.request_no}</td>
                      <td className="py-3 px-4">
                        <Badge className={item.is_pending ? 'bg-amber-500' : 'bg-emerald-500'}>
                          {item.is_pending ? '待处理' : item.status}
                        </Badge>
                      </td>
                      <td className="text-right py-3 px-4">¥{item.amount?.toLocaleString()}</td>
                      <td className="text-right py-3 px-4">
                        {item.is_pending ? (
                          <span className="text-amber-400">{item.processing_days}天 (进行中)</span>
                        ) : (
                          <span>{item.processing_days}天</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-400">{item.requested_at?.split('T')[0]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
