



import { formatAmount } from "./utils";

export default function StaleMaterialsTab({ staleMaterialsData, staleThreshold, setStaleThreshold, loading }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        {staleMaterialsData?.summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 flex-1">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-400">呆滞物料数</div>
                    <div className="text-2xl font-bold text-white mt-1">
                      {staleMaterialsData.summary.stale_count || 0}
                    </div>
                  </div>
                  <AlertTriangle className="w-10 h-10 text-amber-500" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-400">呆滞金额</div>
                    <div className="text-2xl font-bold text-white mt-1">
                      {formatAmount(staleMaterialsData.summary.stale_value)}
                    </div>
                  </div>
                  <DollarSign className="w-10 h-10 text-red-500" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-400">总库存价值</div>
                    <div className="text-2xl font-bold text-white mt-1">
                      {formatAmount(staleMaterialsData.summary.total_value_with_stock)}
                    </div>
                  </div>
                  <Warehouse className="w-10 h-10 text-blue-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">库龄阈值:</label>
          <select
            value={staleThreshold ?? 90}
            onChange={(e) => setStaleThreshold(parseInt(e.target.value))}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
          >
            <option value={30}>30天</option>
            <option value={60}>60天</option>
            <option value={90}>90天</option>
            <option value={120}>120天</option>
            <option value={180}>180天</option>
          </select>
        </div>
      </div>

      {/* 库龄分布 */}
      {staleMaterialsData?.age_distribution && (
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle>库龄分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              {(staleMaterialsData.age_distribution || []).map((item, index) => {
                const colors = ['text-emerald-400', 'text-blue-400', 'text-amber-400', 'text-red-400'];
                return (
                  <div key={index} className="text-center">
                    <div className={`text-2xl font-bold ${colors[index]}`}>
                      {formatAmount(item.value)}
                    </div>
                    <div className="text-sm text-slate-400 mt-1">{item.age_range}</div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 呆滞物料列表 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>呆滞物料详情</CardTitle>
          <CardDescription>按库存金额降序排列</CardDescription>
        </CardHeader>
        <CardContent>
          {staleMaterialsData?.stale_materials?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">物料编码</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">物料名称</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">分类</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">当前库存</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">库存价值</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">库龄(天)</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">最后变动</th>
                  </tr>
                </thead>
                <tbody>
                  {(staleMaterialsData.stale_materials || []).map((item, index) => (
                    <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4 font-medium">{item.material_code}</td>
                      <td className="py-3 px-4">{item.material_name}</td>
                      <td className="py-3 px-4 text-slate-400">{item.category_name || '-'}</td>
                      <td className="text-right py-3 px-4">{item.current_stock} {item.unit}</td>
                      <td className="text-right py-3 px-4">{formatAmount(item.inventory_value)}</td>
                      <td className="text-right py-3 px-4">
                        <Badge className={item.stale_days > 180 ? 'bg-red-500' : item.stale_days > 90 ? 'bg-amber-500' : 'bg-blue-500'}>
                          {item.stale_days}天
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{item.last_activity?.split('T')[0]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">
              {loading ? '加载中...' : '暂无呆滞物料'}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
