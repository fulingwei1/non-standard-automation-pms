import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui";
import { BarChart3, TrendingUp } from "lucide-react";

export default function KeyMetricsCard() {
  return (
    <Card className="bg-surface-50 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          关键指标
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-sm text-slate-400 mb-2">本月订单数</p>
            <p className="text-2xl font-bold text-white">92</p>
            <div className="mt-2 flex items-center justify-center gap-1 text-sm">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">+8 较上月</span>
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm text-slate-400 mb-2">供应商评分</p>
            <p className="text-2xl font-bold text-white">4.55</p>
            <div className="mt-2 flex items-center justify-center gap-1 text-sm">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">+0.12 较上月</span>
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm text-slate-400 mb-2">成本节省率</p>
            <p className="text-2xl font-bold text-white">4.2%</p>
            <div className="mt-2 flex items-center justify-center gap-1 text-sm">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">+0.5% 较上月</span>
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm text-slate-400 mb-2">订单完成率</p>
            <p className="text-2xl font-bold text-white">96.8%</p>
            <div className="mt-2 flex items-center justify-center gap-1 text-sm">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">+1.2% 较上月</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
