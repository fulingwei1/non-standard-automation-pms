import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  Badge,
  Progress,
  Button,
} from "../ui";
import { costApi } from "../../services/api";
import { formatCurrency } from "../../lib/utils";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  BarChart3,
} from "lucide-react";

const HEALTH_CONFIG = {
  healthy: { label: "健康", color: "bg-green-500", textColor: "text-green-700", bgLight: "bg-green-50" },
  warning: { label: "预警", color: "bg-yellow-500", textColor: "text-yellow-700", bgLight: "bg-yellow-50" },
  critical: { label: "危险", color: "bg-red-500", textColor: "text-red-700", bgLight: "bg-red-50" },
};

export default function ProfitAnalysisCard({ projectId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!projectId) return;
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await costApi.getProfitOptimization(projectId);
      setData(res.data?.data || res.data);
    } catch (err) {
      console.error("利润分析加载失败:", err);
      setError("暂无利润分析数据");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-5 bg-gray-200 rounded w-32" />
            <div className="h-8 bg-gray-200 rounded w-24" />
            <div className="h-3 bg-gray-200 rounded w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="h-5 w-5 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-400">利润分析</h3>
          </div>
          <p className="text-sm text-gray-500">{error || "暂无数据"}</p>
        </CardContent>
      </Card>
    );
  }

  const healthCfg = HEALTH_CONFIG[data.health] || HEALTH_CONFIG.warning;
  const marginPositive = data.current_margin_rate >= 0;
  const forecastPositive = data.forecast_margin_rate >= 0;

  return (
    <Card className="overflow-hidden">
      {/* 顶部健康度指示条 */}
      <div className={`h-1 ${healthCfg.color}`} />

      <CardContent className="p-6 space-y-4">
        {/* 标题行 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold">利润分析</h3>
          </div>
          <Badge className={`${healthCfg.color} text-white`}>
            {healthCfg.label}
          </Badge>
        </div>

        {/* 核心指标 */}
        <div className="grid grid-cols-2 gap-4">
          {/* 当前毛利率 */}
          <div className={`rounded-lg p-3 ${healthCfg.bgLight}`}>
            <p className="text-xs text-gray-500 mb-1">当前毛利率</p>
            <div className="flex items-center gap-1">
              {marginPositive ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <span className={`text-xl font-bold ${marginPositive ? "text-green-700" : "text-red-700"}`}>
                {data.current_margin_rate.toFixed(1)}%
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              毛利 {formatCurrency(data.current_margin)}
            </p>
          </div>

          {/* 预计毛利率 */}
          <div className="rounded-lg p-3 bg-blue-50">
            <p className="text-xs text-gray-500 mb-1">预计毛利率</p>
            <div className="flex items-center gap-1">
              {forecastPositive ? (
                <TrendingUp className="h-4 w-4 text-blue-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <span className={`text-xl font-bold ${forecastPositive ? "text-blue-700" : "text-red-700"}`}>
                {data.forecast_margin_rate.toFixed(1)}%
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              预计毛利 {formatCurrency(data.forecast_margin)}
            </p>
          </div>
        </div>

        {/* 目标对比进度条 */}
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>当前 vs 目标毛利率 ({data.target_margin_rate}%)</span>
            <span className={data.margin_gap >= 0 ? "text-green-600" : "text-red-600"}>
              {data.margin_gap >= 0 ? "+" : ""}{data.margin_gap.toFixed(1)}pp
            </span>
          </div>
          <div className="relative">
            <Progress
              value={Math.min(Math.max(data.current_margin_rate / data.target_margin_rate * 100, 0), 150)}
              className="h-2"
            />
            {/* 目标线标记 */}
            <div
              className="absolute top-0 h-2 w-0.5 bg-gray-800"
              style={{ left: `${Math.min(100, 100)}%` }}
              title={`目标: ${data.target_margin_rate}%`}
            />
          </div>
        </div>

        {/* 成本摘要 */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-xs text-gray-500">合同金额</p>
            <p className="text-sm font-semibold">{formatCurrency(data.contract_amount)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">已发生成本</p>
            <p className="text-sm font-semibold">{formatCurrency(data.actual_cost)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">预计总成本</p>
            <p className="text-sm font-semibold">{formatCurrency(data.forecast_total_cost)}</p>
          </div>
        </div>

        {/* 展开/收起 */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-gray-500 hover:text-gray-700"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <>收起详情 <ChevronUp className="ml-1 h-4 w-4" /></>
          ) : (
            <>查看详情 <ChevronDown className="ml-1 h-4 w-4" /></>
          )}
        </Button>

        {/* 展开内容 */}
        {expanded && (
          <div className="space-y-4 pt-2 border-t">
            {/* 优化建议 */}
            {data.optimization_suggestions?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold flex items-center gap-1 mb-2">
                  <Lightbulb className="h-4 w-4 text-yellow-500" />
                  成本优化建议
                </h4>
                <div className="space-y-2">
                  {data.optimization_suggestions.map((s, i) => (
                    <div
                      key={i}
                      className={`p-2 rounded text-sm border-l-2 ${
                        s.priority === "high"
                          ? "border-red-500 bg-red-50"
                          : "border-yellow-500 bg-yellow-50"
                      }`}
                    >
                      <div className="flex items-start gap-1">
                        {s.priority === "high" ? (
                          <AlertTriangle className="h-3.5 w-3.5 text-red-500 mt-0.5 shrink-0" />
                        ) : (
                          <AlertTriangle className="h-3.5 w-3.5 text-yellow-500 mt-0.5 shrink-0" />
                        )}
                        <span>{s.suggestion}</span>
                      </div>
                      {s.potential_saving > 0 && (
                        <p className="text-xs text-gray-500 mt-1 ml-4">
                          潜在节约: {formatCurrency(s.potential_saving)}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 报价偏差 */}
            {data.quote_variance?.has_quote && (
              <div>
                <h4 className="text-sm font-semibold flex items-center gap-1 mb-2">
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                  报价 vs 实际偏差
                </h4>
                <div className="flex items-center gap-4 text-sm mb-2">
                  <span>总偏差: </span>
                  <span
                    className={
                      data.quote_variance.overall_variance > 0
                        ? "text-red-600 font-medium"
                        : "text-green-600 font-medium"
                    }
                  >
                    {data.quote_variance.overall_variance > 0 ? "+" : ""}
                    {formatCurrency(data.quote_variance.overall_variance)}
                    ({data.quote_variance.overall_variance_pct.toFixed(1)}%)
                  </span>
                </div>
                {data.quote_variance.top_variances?.length > 0 && (
                  <div className="space-y-1">
                    {data.quote_variance.top_variances.map((v, i) => (
                      <div key={i} className="flex justify-between text-xs py-1 border-b border-gray-100">
                        <span className="text-gray-600">{v.item_name || v.cost_category}</span>
                        <span className={v.variance > 0 ? "text-red-600" : "text-green-600"}>
                          {v.variance > 0 ? "+" : ""}{formatCurrency(v.variance)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 无优化建议时 */}
            {(!data.optimization_suggestions || data.optimization_suggestions.length === 0) &&
              !data.quote_variance?.has_quote && (
                <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>当前成本状态良好，暂无优化建议</span>
                </div>
              )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
