




export default function SafetyStockTab({ safetyStockData }) {
  return (
    <div className="space-y-4">
      {safetyStockData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">物料总数</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {safetyStockData.summary.total_materials || 0}
                  </div>
                </div>
                <Package className="w-10 h-10 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">达标率</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {safetyStockData.summary.compliant_rate || 0}%
                  </div>
                </div>
                <Shield className="w-10 h-10 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">预警数</div>
                  <div className="text-2xl font-bold text-amber-400 mt-1">
                    {safetyStockData.summary.warning || 0}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">低于安全库存</div>
                </div>
                <AlertTriangle className="w-10 h-10 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">缺货数</div>
                  <div className="text-2xl font-bold text-red-400 mt-1">
                    {safetyStockData.summary.out_of_stock || 0}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">库存为0</div>
                </div>
                <TrendingDown className="w-10 h-10 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 缺货预警列表 */}
      {safetyStockData?.out_of_stock_materials?.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700/50 border-red-900/30">
        <CardHeader>
          <CardTitle className="text-red-400">缺货物料</CardTitle>
          <CardDescription>当前库存为0的物料</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {safetyStockData.out_of_stock_materials.slice(0, 12).map((item, index) => (
              <div key={index} className="p-3 bg-red-950/30 rounded border border-red-900/50">
                <div className="font-medium">{item.material_name}</div>
                <div className="text-xs text-slate-400 mt-1">{item.material_code}</div>
                <div className="text-xs text-red-400 mt-1">安全库存: {item.safety_stock} {item.unit}</div>
              </div>
            ))}
          </div>
        </CardContent>
        </Card>
      )}

      {/* 低库存预警列表 */}
      {safetyStockData?.warning_materials?.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-amber-400">低库存预警</CardTitle>
            <CardDescription>当前库存低于安全库存的物料</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">物料编码</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">物料名称</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">当前库存</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">安全库存</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">缺口</th>
                  </tr>
                </thead>
                <tbody>
                  {safetyStockData.warning_materials.slice(0, 20).map((item, index) => (
                    <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4 font-medium">{item.material_code}</td>
                      <td className="py-3 px-4">{item.material_name}</td>
                      <td className="text-right py-3 px-4 text-amber-400">{item.current_stock} {item.unit}</td>
                      <td className="text-right py-3 px-4">{item.safety_stock} {item.unit}</td>
                      <td className="text-right py-3 px-4 text-red-400">-{item.shortage_qty} {item.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
