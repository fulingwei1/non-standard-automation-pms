import {
  DollarSign,
  Activity,
  TrendingUp,
  Package,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { formatAmount } from "./utils";

export default function TurnoverRateTab({ turnoverData }) {
  return (
    <div className="space-y-4">
      {turnoverData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">库存总值</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {formatAmount(turnoverData.summary.total_inventory_value)}
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
                  <div className="text-sm text-slate-400">周转率</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {turnoverData.summary.turnover_rate || 0}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">次/年</div>
                </div>
                <Activity className="w-10 h-10 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">周转天数</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {turnoverData.summary.turnover_days || 0}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">天</div>
                </div>
                <TrendingUp className="w-10 h-10 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-400">物料总数</div>
                  <div className="text-2xl font-bold text-white mt-1">
                    {turnoverData.summary.total_materials || 0}
                  </div>
                </div>
                <Package className="w-10 h-10 text-amber-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 分类周转率图表 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>分类库存占用</CardTitle>
          <CardDescription>各物料分类的库存金额分布</CardDescription>
        </CardHeader>
        <CardContent>
          {turnoverData?.category_breakdown?.length > 0 ? (
            <div className="space-y-4">
              {(turnoverData.category_breakdown || []).map((item, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="w-32 text-sm text-slate-400 truncate">{item.category_name}</div>
                  <div className="flex-1 bg-slate-700 rounded-full h-6 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-600 to-blue-400 flex items-center justify-end pr-2"
                      style={{ width: `${Math.min(item.value_percentage, 100)}%` }}
                    >
                      <span className="text-xs font-medium text-white">
                        {item.value_percentage}%
                      </span>
                    </div>
                  </div>
                  <div className="w-24 text-right text-sm">
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
    </div>
  );
}
