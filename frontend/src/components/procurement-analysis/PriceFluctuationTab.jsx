/**
 * 物料价格波动分析 Tab 组件
 * 显示物料价格波动统计和详情表格
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import ProcurementStatsCard from './ProcurementStatsCard';
import { STATS_CARD_CONFIGS } from './procurementConstants';

/**
 * 价格波动 Tab 组件
 * @param {object} props
 * @param {object} props.data - 价格波动数据
 */
export default function PriceFluctuationTab({ data }) {
  const { summary, materials } = data || {};

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {STATS_CARD_CONFIGS.priceFluctuation.map(config => (
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

      {/* 价格波动列表 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>物料价格波动详情</CardTitle>
          <CardDescription>按波动率排序显示物料价格变化</CardDescription>
        </CardHeader>
        <CardContent>
          {materials?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">物料编码</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">物料名称</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">分类</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">最低价</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">最高价</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">平均价</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">最新价</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">波动率</th>
                  </tr>
                </thead>
                <tbody>
                  {materials.map((item, index) => (
                    <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4 font-medium">{item.material_code}</td>
                      <td className="py-3 px-4">{item.material_name}</td>
                      <td className="py-3 px-4 text-slate-400">{item.category_name || '-'}</td>
                      <td className="text-right py-3 px-4">¥{item.min_price?.toFixed(4)}</td>
                      <td className="text-right py-3 px-4">¥{item.max_price?.toFixed(4)}</td>
                      <td className="text-right py-3 px-4">¥{item.avg_price?.toFixed(4)}</td>
                      <td className="text-right py-3 px-4">¥{item.latest_price?.toFixed(4)}</td>
                      <td className="text-right py-3 px-4">
                        <Badge className={item.price_volatility > 20 ? 'bg-amber-500' : 'bg-slate-600'}>
                          {item.price_volatility}%
                        </Badge>
                      </td>
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
