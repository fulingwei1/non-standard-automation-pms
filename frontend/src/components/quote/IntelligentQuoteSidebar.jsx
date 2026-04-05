/**
 * 智能报价侧边栏组件
 * 集成到报价创建/编辑流程，提供AI辅助定价建议
 *
 * 功能：
 * 1. 商机概要展示
 * 2. 历史价格参考
 * 3. AI最优价格建议
 * 4. 价格场景模拟
 * 5. 实时赢单率预测
 */

import { useState, useEffect, useMemo } from "react";




import { cn, formatCurrency } from "../../lib/utils";
import { intelligentQuoteApi } from "../../services/api";

/**
 * 智能报价侧边栏
 * @param {Object} props
 * @param {Object} props.opportunity - 选中的商机对象
 * @param {number} props.currentPrice - 当前报价金额
 * @param {number} props.currentCost - 当前成本
 * @param {Function} props.onApplyPrice - 应用推荐价格的回调
 */
export default function IntelligentQuoteSidebar({
  opportunity,
  currentPrice = 0,
  currentCost = 0,
  onApplyPrice,
}) {
  const [historicalData, setHistoricalData] = useState(null);
  const [loading, setLoading] = useState(false);

  // 根据商机产品类型获取历史价格数据
  useEffect(() => {
    if (opportunity?.product_type || opportunity?.opp_name) {
      fetchHistoricalPrices();
    }
  }, [opportunity?.id]);

  const fetchHistoricalPrices = async () => {
    try {
      setLoading(true);
      // 尝试从商机名称推断产品类型
      const productType = inferProductType(opportunity);
      const res = await intelligentQuoteApi.getHistoricalPrices(productType);
      setHistoricalData(res);
    } catch (error) {
      console.error("获取历史价格失败:", error);
      setHistoricalData(null);
    } finally {
      setLoading(false);
    }
  };

  // 从商机名称推断产品类型
  const inferProductType = (opp) => {
    if (!opp) return "FCT";
    const name = (opp.opp_name || opp.name || "").toUpperCase();
    if (name.includes("FCT")) return "FCT";
    if (name.includes("ICT")) return "ICT";
    if (name.includes("EOL")) return "EOL";
    if (name.includes("视觉") || name.includes("VISION")) return "VISION";
    return "FCT";
  };

  // 计算当前毛利率
  const currentMargin = useMemo(() => {
    if (currentPrice <= 0) return 0;
    return ((currentPrice - currentCost) / currentPrice * 100).toFixed(1);
  }, [currentPrice, currentCost]);

  // 生成价格场景
  const priceScenarios = useMemo(() => {
    if (!historicalData) return [];

    const avgPrice = historicalData.average_price;
    const cost = currentCost || avgPrice * 0.65; // 假设成本约为平均价格的65%

    return [
      {
        price: Math.round(avgPrice * 0.85),
        winRate: 85,
        marginRate: Math.round((1 - cost / (avgPrice * 0.85)) * 100),
        label: "激进低价",
        description: "快速抢占市场",
      },
      {
        price: Math.round(avgPrice * 0.95),
        winRate: 70,
        marginRate: Math.round((1 - cost / (avgPrice * 0.95)) * 100),
        label: "AI推荐",
        description: "平衡方案",
        recommended: true,
      },
      {
        price: Math.round(avgPrice * 1.05),
        winRate: 55,
        marginRate: Math.round((1 - cost / (avgPrice * 1.05)) * 100),
        label: "标准报价",
        description: "行业均价",
      },
      {
        price: Math.round(avgPrice * 1.15),
        winRate: 35,
        marginRate: Math.round((1 - cost / (avgPrice * 1.15)) * 100),
        label: "利润优先",
        description: "风险较高",
      },
    ];
  }, [historicalData, currentCost]);

  // 计算当前报价的预期赢单率
  const estimatedWinRate = useMemo(() => {
    if (!historicalData || currentPrice <= 0) return 0;

    const avgPrice = historicalData.average_price;
    const ratio = currentPrice / avgPrice;

    // 简化的赢单率估算模型
    if (ratio <= 0.85) return 85;
    if (ratio <= 0.95) return 70 + (0.95 - ratio) * 150;
    if (ratio <= 1.05) return 55 + (1.05 - ratio) * 150;
    if (ratio <= 1.15) return 35 + (1.15 - ratio) * 200;
    return Math.max(15, 35 - (ratio - 1.15) * 100);
  }, [historicalData, currentPrice]);

  // 如果没有选择商机，显示提示
  if (!opportunity) {
    return (
      <div className="space-y-4">
        <Card className="border-dashed border-slate-700 bg-slate-900/40">
          <CardContent className="py-8 text-center">
            <Sparkles className="w-12 h-12 mx-auto text-slate-600 mb-4" />
            <p className="text-slate-400 text-sm">
              请先选择商机，AI将自动分析并提供定价建议
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 商机概要 */}
      <Card className="border-slate-700 bg-slate-900/60">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2 text-slate-300">
            <Building2 className="w-4 h-4 text-blue-400" />
            商机概要
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-500">客户</span>
            <span className="text-white font-medium">
              {opportunity.customer_name || opportunity.customer?.name || "未知客户"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">产品</span>
            <span className="text-white">
              {inferProductType(opportunity)} 测试设备
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">预算</span>
            <span className="text-emerald-400">
              {opportunity.est_amount
                ? formatCurrency(opportunity.est_amount)
                : "待确认"}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* 历史价格参考 */}
      <Card className="border-slate-700 bg-slate-900/60">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2 text-slate-300">
            <History className="w-4 h-4 text-purple-400" />
            历史价格参考
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="animate-pulse space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-8 bg-slate-800 rounded" />
              ))}
            </div>
          ) : historicalData ? (
            <div className="space-y-3">
              {/* 汇总统计 */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-800/60 rounded-lg p-2 text-center">
                  <div className="text-slate-500">平均成交价</div>
                  <div className="text-emerald-400 font-bold">
                    {formatCurrency(historicalData.average_price)}
                  </div>
                </div>
                <div className="bg-slate-800/60 rounded-lg p-2 text-center">
                  <div className="text-slate-500">匹配项目</div>
                  <div className="text-blue-400 font-bold">
                    {historicalData.matched_count}个
                  </div>
                </div>
              </div>

              {/* 历史项目列表 */}
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {historicalData.historical_prices.slice(0, 5).map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs bg-slate-800/40 rounded px-2 py-1.5"
                  >
                    <div className="flex-1 truncate">
                      <span className="text-white">{item.project_name}</span>
                      <Badge variant="outline" className="ml-1 text-[10px] border-slate-600">
                        {item.similarity}
                      </Badge>
                    </div>
                    <div className="text-emerald-400 font-medium ml-2">
                      {formatCurrency(item.final_price)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-4">暂无历史数据</p>
          )}
        </CardContent>
      </Card>

      {/* AI最优价格建议 */}
      <Card className="border-purple-500/50 bg-gradient-to-br from-purple-500/10 to-slate-900/60">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2 text-purple-300">
            <Award className="w-4 h-4" />
            AI最优价格建议
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {priceScenarios.find((s) => s.recommended) && (
            <>
              <div className="text-center py-2">
                <div className="text-2xl font-bold text-purple-400">
                  {formatCurrency(priceScenarios.find((s) => s.recommended)?.price || 0)}
                </div>
                <div className="flex justify-center gap-4 mt-2 text-xs">
                  <span className="text-emerald-400">
                    赢单率 {priceScenarios.find((s) => s.recommended)?.winRate}%
                  </span>
                  <span className="text-blue-400">
                    毛利率 {priceScenarios.find((s) => s.recommended)?.marginRate}%
                  </span>
                </div>
              </div>

              {onApplyPrice && (
                <Button
                  size="sm"
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  onClick={() => onApplyPrice(priceScenarios.find((s) => s.recommended)?.price)}
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  应用推荐价格
                </Button>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* 价格场景模拟 */}
      <Card className="border-slate-700 bg-slate-900/60">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2 text-slate-300">
            <BarChart3 className="w-4 h-4 text-amber-400" />
            价格场景模拟
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {priceScenarios.map((scenario, idx) => (
            <div
              key={idx}
              className={cn(
                "flex items-center justify-between text-xs rounded-lg px-3 py-2 cursor-pointer transition-all",
                scenario.recommended
                  ? "bg-purple-500/20 border border-purple-500/50"
                  : "bg-slate-800/60 hover:bg-slate-800",
              )}
              onClick={() => onApplyPrice?.(scenario.price)}
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium">
                    {formatCurrency(scenario.price)}
                  </span>
                  {scenario.recommended && (
                    <Badge className="bg-purple-500 text-[10px]">推荐</Badge>
                  )}
                </div>
                <span className="text-slate-500">{scenario.description}</span>
              </div>
              <div className="text-right">
                <div className={cn(
                  "font-medium",
                  scenario.winRate >= 70 ? "text-emerald-400" :
                  scenario.winRate >= 50 ? "text-amber-400" : "text-red-400"
                )}>
                  {scenario.winRate}%
                </div>
                <div className="text-slate-500">毛利 {scenario.marginRate}%</div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* 当前报价分析 */}
      {currentPrice > 0 && (
        <Card className="border-slate-700 bg-slate-900/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 text-slate-300">
              <Target className="w-4 h-4 text-cyan-400" />
              当前报价分析
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-center">
              <div className="text-lg font-bold text-white">
                {formatCurrency(currentPrice)}
              </div>
              <div className="flex justify-center gap-4 mt-1 text-xs">
                <span className="text-slate-400">
                  毛利率 <span className={cn(
                    "font-medium",
                    parseFloat(currentMargin) >= 30 ? "text-emerald-400" :
                    parseFloat(currentMargin) >= 20 ? "text-amber-400" : "text-red-400"
                  )}>{currentMargin}%</span>
                </span>
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">预期赢单率</span>
                <span className={cn(
                  "font-medium",
                  estimatedWinRate >= 70 ? "text-emerald-400" :
                  estimatedWinRate >= 50 ? "text-amber-400" : "text-red-400"
                )}>
                  {Math.round(estimatedWinRate)}%
                </span>
              </div>
              <Progress value={estimatedWinRate} className="h-2" />
            </div>

            {/* 风险提示 */}
            {estimatedWinRate < 50 && (
              <div className="flex items-start gap-2 text-xs text-amber-400 bg-amber-500/10 rounded-lg p-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>当前报价偏高，赢单概率较低，建议参考AI推荐价格</span>
              </div>
            )}
            {parseFloat(currentMargin) < 20 && (
              <div className="flex items-start gap-2 text-xs text-red-400 bg-red-500/10 rounded-lg p-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>毛利率低于20%，存在盈利风险</span>
              </div>
            )}
            {estimatedWinRate >= 70 && parseFloat(currentMargin) >= 25 && (
              <div className="flex items-start gap-2 text-xs text-emerald-400 bg-emerald-500/10 rounded-lg p-2">
                <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>价格合理，赢单率和利润率均处于健康区间</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
