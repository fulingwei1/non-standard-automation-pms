/**
 * 物料质量合格率分析 Tab 组件
 * 显示供应商质量统计和排名
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import ProcurementStatsCard from './ProcurementStatsCard';
import { STATS_CARD_CONFIGS, getQualityRateBadgeColor } from '@/lib/constants/procurementAnalysis';

/**
 * 质量合格率 Tab 组件
 * @param {object} props
 * @param {object} props.data - 质量合格率数据
 */
export default function QualityRateTab({ data }) {
  const { summary, supplier_quality } = data || {};

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {(STATS_CARD_CONFIGS.qualityRate || []).map(config => (
            <ProcurementStatsCard
              key={config.key}
              label={config.label}
              value={summary[config.key]}
              icon={config.icon}
              color={config.color}
              suffix={config.suffix || ''}
              subtitle={config.subtitle || ''}
            />
          ))}
        </div>
      )}

      {/* 供应商质量列表 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>供应商质量合格率排名</CardTitle>
          <CardDescription>按综合合格率降序排列</CardDescription>
        </CardHeader>
        <CardContent>
          {supplier_quality?.length > 0 ? (
            <div className="space-y-4">
              {(supplier_quality || []).map((item, index) => (
                <div key={item.supplier_id} className="p-4 bg-slate-700/30 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${index < 3 ? 'bg-blue-500' : 'bg-slate-600'}`}>
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-medium">{item.supplier_name}</div>
                        <div className="text-xs text-slate-400">物料数: {item.material_count}</div>
                      </div>
                    </div>
                    <Badge className={getQualityRateBadgeColor(item.overall_pass_rate)}>
                      {item.overall_pass_rate}% 合格率
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">合格数量: </span>
                      <span className="font-medium text-emerald-400">{item.total_qualified?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">不合格数量: </span>
                      <span className="font-medium text-red-400">{item.total_rejected?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">检验总数: </span>
                      <span className="font-medium">{item.total_qty?.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
