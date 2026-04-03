import {
  DollarSign,
  PieChart,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { formatAmount } from "./utils";

export default function CostOccupancyTab({ costOccupancyData }) {
  return (
    <div className="space-y-4">
      {costOccupancyData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">库存总值</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {formatAmount(costOccupancyData.summary.total_inventory_value)}
                  </div>
                </div>
                <DollarSign className="w-10 h-10 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">分类数量</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {costOccupancyData.summary.total_categories || 0}
                  </div>
                </div>
                <PieChart className="w-10 h-10 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 分类成本占用 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>分类库存成本占用</CardTitle>
        </CardHeader>
        <CardContent>
          {costOccupancyData?.category_occupancy?.length > 0 ? (
            <div className="space-y-4">
              {(costOccupancyData.category_occupancy || []).map((item, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-40 text-sm truncate">{item.category_name}</div>
                  <div className="flex-1 bg-slate-700 rounded-full h-8 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-600 to-purple-400 flex items-center justify-end pr-3"
                      style={{ width: `${Math.min(item.value_percentage, 100)}%` }}
                    >
                      <span className="text-sm font-medium text-white">
                        {item.value_percentage}%
                      </span>
                    </div>
                  </div>
                  <div className="w-28 text-right font-medium">
                    {formatAmount(item.inventory_value)}
                  </div>
                  <div className="w-16 text-center text-sm text-slate-400">
                    {item.material_count}个
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          )}
        </CardContent>
      </Card>

      {/* 高库存占用物料TOP榜 */}
      {costOccupancyData?.top_materials?.length > 0 && (
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle>高库存占用物料TOP榜</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {(costOccupancyData.top_materials || []).map((item, index) => (
                <div key={index} className="p-4 bg-slate-700/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium truncate">{item.material_name}</div>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${index < 3 ? 'bg-blue-500' : 'bg-slate-600'}`}>
                      {index + 1}
                    </div>
                  </div>
                  <div className="text-sm text-slate-400">{item.material_code}</div>
                  <div className="flex items-center justify-between mt-3">
                    <div className="text-sm">库存: {item.current_stock} {item.unit}</div>
                    <div className="font-medium">{formatAmount(item.inventory_value)}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
