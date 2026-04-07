import { useState, useEffect } from "react";

import { funnelOptimizationApi } from "../../services/api";
import { STAGE_NAME_MAP } from "./constants";

export default function Bottlenecks() {
  const [bottlenecks, setBottlenecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await funnelOptimizationApi.getBottlenecks();
        const responseData = res.formatted || res.data?.data || res.data || {};
        setBottlenecks(responseData?.bottlenecks || responseData || []);
      } catch (err) {
        console.error("加载瓶颈数据失败:", err);
        setError("加载瓶颈数据失败，请稍后重试");
        setBottlenecks([]);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <div className="text-slate-400 p-4">加载中...</div>;

  return (
    <div className="space-y-4">
      {error && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <div className="text-sm">{error}</div>
        </Alert>
      )}

      {bottlenecks.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-slate-400">
            <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>当前没有发现瓶颈问题，销售漏斗运行健康！</p>
          </CardContent>
        </Card>
      ) : (
        bottlenecks.map((bottleneck, idx) => (
          <Card key={idx} className={bottleneck.severity === "HIGH" ? "border-red-500" : "border-orange-500"}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className={`w-5 h-5 ${bottleneck.severity === "HIGH" ? "text-red-500" : "text-orange-500"}`} />
                  {bottleneck.stage_name || STAGE_NAME_MAP[bottleneck.stage] || bottleneck.stage}
                </CardTitle>
                <Badge variant={bottleneck.severity === "HIGH" ? "destructive" : "secondary"}>
                  {bottleneck.severity === "HIGH" ? "严重" : bottleneck.severity === "MEDIUM" ? "中等" : "低"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-400">问题</div>
                  <div className="text-lg font-medium">
                    {bottleneck.issue_type === "low_conversion"
                      ? `转化率 ${bottleneck.current_rate?.toFixed(1) || 0}%（基准${bottleneck.benchmark_rate?.toFixed(1) || 0}%）`
                      : `停留${bottleneck.current_days?.toFixed(1) || 0}天（基准${bottleneck.benchmark_days?.toFixed(1) || 0}天）`}
                  </div>
                </div>

                {bottleneck.impact && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <div className="text-sm">{bottleneck.impact}</div>
                  </Alert>
                )}

                {bottleneck.root_causes && bottleneck.root_causes.length > 0 && (
                  <div>
                    <div className="text-sm text-slate-400 mb-2">根本原因</div>
                    <div className="flex flex-wrap gap-2">
                      {bottleneck.root_causes.map((cause, i) => (
                        <Badge key={i} variant="outline">
                          {cause}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {bottleneck.recommendations && bottleneck.recommendations.length > 0 && (
                  <div>
                    <div className="text-sm text-slate-400 mb-2">改进建议</div>
                    <div className="space-y-2">
                      {bottleneck.recommendations.map((rec, i) => (
                        <div key={i} className="flex items-start gap-2 text-sm">
                          <ArrowRight className="w-4 h-4 text-green-500 mt-0.5" />
                          {rec}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}
