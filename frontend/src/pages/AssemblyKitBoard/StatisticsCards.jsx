/**
 * Statistics Cards - 统计卡片
 */
import {
  BarChart3,
  CheckCircle2,
  TrendingUp,
  Package,
} from "lucide-react";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { getKitRateColor } from "./constants";

export default function StatisticsCards({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-500 mb-1">项目总数</div>
              <div className="text-2xl font-bold text-slate-800">
                {stats.total_projects || 0}
              </div>
            </div>
            <BarChart3 className="w-8 h-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-500 mb-1">可开工</div>
              <div className="text-2xl font-bold text-emerald-600">
                {stats.can_start_count || 0}
              </div>
            </div>
            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-500 mb-1">平均齐套率</div>
              <div
                className={cn(
                  "text-2xl font-bold",
                  getKitRateColor(stats.avg_kit_rate || 0)
                )}>
                {stats.avg_kit_rate || 0}%
              </div>
            </div>
            <TrendingUp className="w-8 h-8 text-blue-500" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-500 mb-1">阻塞齐套率</div>
              <div
                className={cn(
                  "text-2xl font-bold",
                  getKitRateColor(stats.avg_blocking_rate || 0)
                )}>
                {stats.avg_blocking_rate || 0}%
              </div>
            </div>
            <Package className="w-8 h-8 text-amber-500" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
