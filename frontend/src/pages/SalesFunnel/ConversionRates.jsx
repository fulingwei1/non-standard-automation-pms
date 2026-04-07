import { useState, useEffect } from "react";

import { funnelOptimizationApi } from "../../services/api";
import { STAGE_NAME_MAP } from "./constants";

export default function ConversionRates() {
  const [funnelData, setFunnelData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await funnelOptimizationApi.getConversionRates();
        setFunnelData(res.formatted || res.data?.data || res.data);
      } catch (err) {
        console.error("加载转化率数据失败:", err);
        setError("加载转化率数据失败，请稍后重试");
        setFunnelData(null);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <div className="text-slate-400 p-4">加载中...</div>;
  if (!funnelData) return <div className="text-slate-400 p-4">暂无数据</div>;

  return (
    <div className="space-y-6">
      {error && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <div className="text-sm">{error}</div>
        </Alert>
      )}

      {/* 整体指标 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">总线索数</div>
            <div className="text-2xl font-bold">{funnelData.overall_metrics?.total_leads || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">赢单数</div>
            <div className="text-2xl font-bold text-green-500">{funnelData.overall_metrics?.total_won || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">整体转化率</div>
            <div className="text-2xl font-bold">{funnelData.overall_metrics?.overall_conversion_rate?.toFixed(1) || 0}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">平均销售周期</div>
            <div className="text-2xl font-bold">{funnelData.overall_metrics?.avg_sales_cycle_days?.toFixed(1) || 0}天</div>
          </CardContent>
        </Card>
      </div>

      {/* 漏斗可视化 */}
      <Card>
        <CardHeader>
          <CardTitle>销售漏斗转化率</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(funnelData.stages || []).map((stage) => (
              <div key={stage.stage} className="flex items-center gap-4">
                <div className="w-32 text-sm font-medium">{stage.stage_name || STAGE_NAME_MAP[stage.stage] || stage.stage}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-slate-400">{stage.count}个商机</span>
                    {stage.conversion_to_next != null && (
                      <span className={`text-sm ${stage.conversion_to_next < 55 ? "text-red-500" : "text-green-500"}`}>
                        转化率 {stage.conversion_to_next.toFixed(1)}%
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress value={(stage.count / (funnelData.overall_metrics?.total_leads || 1)) * 100} className="h-3 flex-1" />
                    {stage.trend === "up" && <TrendingUp className="w-4 h-4 text-green-500" />}
                    {stage.trend === "down" && <TrendingDown className="w-4 h-4 text-red-500" />}
                    {stage.trend === "stable" && <Activity className="w-4 h-4 text-slate-400" />}
                  </div>
                </div>
                {stage.avg_days_in_stage != null && (
                  <div className="w-24 text-sm text-slate-400 text-right">平均{stage.avg_days_in_stage.toFixed(1)}天</div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
