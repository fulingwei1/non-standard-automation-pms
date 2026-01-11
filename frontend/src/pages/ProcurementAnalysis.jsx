/**
 * 采购分析页面
 * Features: 采购成本趋势、物料价格波动、供应商交期准时率、采购申请处理时效、物料质量合格率
 */
import { useState, useEffect, useCallback } from "react";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  ShoppingCart,
  Truck,
  Award,
  Clock,
  AlertTriangle,
  BarChart3,
  LineChart,
  PieChart,
  Download,
  Calendar,
  Filter,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { api, procurementApi } from "../services/api";

export default function ProcurementAnalysis() {
  const [activeTab, setActiveTab] = useState("cost-trend");
  const [loading, setLoading] = useState(false);

  // 各分析模块数据
  const [costTrendData, setCostTrendData] = useState(null);
  const [priceFluctuationData, setPriceFluctuationData] = useState(null);
  const [deliveryPerformanceData, setDeliveryPerformanceData] = useState(null);
  const [requestEfficiencyData, setRequestEfficiencyData] = useState(null);
  const [qualityRateData, setQualityRateData] = useState(null);

  // 时间范围筛选
  const [timeRange, setTimeRange] = useState("6month"); // 3month, 6month, year

  // 获取采购成本趋势
  const loadCostTrend = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/procurement-analysis/cost-trend", {
        params: {
          start_date: getDateByRange(timeRange, "start"),
          end_date: getDateByRange(timeRange, "end"),
          group_by: "month"
        }
      });
      setCostTrendData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load cost trend:", error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取物料价格波动
  const loadPriceFluctuation = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/procurement-analysis/price-fluctuation", {
        params: {
          start_date: getDateByRange(timeRange, "start"),
          end_date: getDateByRange(timeRange, "end"),
          limit: 20
        }
      });
      setPriceFluctuationData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load price fluctuation:", error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取供应商交期准时率
  const loadDeliveryPerformance = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/procurement-analysis/delivery-performance", {
        params: {
          start_date: getDateByRange(timeRange, "start"),
          end_date: getDateByRange(timeRange, "end")
        }
      });
      setDeliveryPerformanceData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load delivery performance:", error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取采购申请处理时效
  const loadRequestEfficiency = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/procurement-analysis/request-efficiency", {
        params: {
          start_date: getDateByRange(timeRange, "start"),
          end_date: getDateByRange(timeRange, "end")
        }
      });
      setRequestEfficiencyData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load request efficiency:", error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取物料质量合格率
  const loadQualityRate = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/procurement-analysis/quality-rate", {
        params: {
          start_date: getDateByRange(timeRange, "start"),
          end_date: getDateByRange(timeRange, "end")
        }
      });
      setQualityRateData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load quality rate:", error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 根据时间范围获取日期
  function getDateByRange(range, type) {
    const today = new Date();
    if (range === "3month") {
      const start = new Date(today);
      start.setMonth(today.getMonth() - 3);
      return type === "start" ? start.toISOString().split('T')[0] : today.toISOString().split('T')[0];
    } else if (range === "6month") {
      const start = new Date(today);
      start.setMonth(today.getMonth() - 6);
      return type === "start" ? start.toISOString().split('T')[0] : today.toISOString().split('T')[0];
    } else if (range === "year") {
      const start = new Date(today);
      start.setFullYear(today.getFullYear() - 1);
      return type === "start" ? start.toISOString().split('T')[0] : today.toISOString().split('T')[0];
    }
    return today.toISOString().split('T')[0];
  }

  // 根据时间范围标签
  const timeRangeLabels = {
    "3month": "最近3个月",
    "6month": "最近6个月",
    "year": "最近1年"
  };

  // 初始加载
  useEffect(() => {
    loadCostTrend();
  }, []);

  // Tab切换时加载对应数据
  useEffect(() => {
    if (activeTab === 'cost-trend') loadCostTrend();
    else if (activeTab === 'price-fluctuation') loadPriceFluctuation();
    else if (activeTab === 'delivery-performance') loadDeliveryPerformance();
    else if (activeTab === 'request-efficiency') loadRequestEfficiency();
    else if (activeTab === 'quality-rate') loadQualityRate();
  }, [activeTab]);

  // 格式化金额
  const formatAmount = (amount) => {
    if (!amount) return "¥0";
    if (amount >= 10000) {
      return `¥${(amount / 10000).toFixed(1)}万`;
    }
    return `¥${amount.toLocaleString()}`;
  };

  // 导出报表
  const handleExport = () => {
    try {
      const exportData = [
        ["采购分析报表"],
        ["统计周期", timeRangeLabels[timeRange] || timeRange],
        ["导出日期", new Date().toLocaleDateString("zh-CN")],
        [""],
      ];

      // 根据当前Tab添加数据
      if (activeTab === 'cost-trend' && costTrendData) {
        exportData.push(
          ["=== 采购成本趋势 ==="],
          ["期间采购总额", `¥${costTrendData.summary?.total_amount?.toLocaleString() || 0}`],
          ["期间订单总数", costTrendData.summary?.total_orders || 0],
          ["月均采购额", `¥${costTrendData.summary?.avg_monthly_amount?.toLocaleString() || 0}`],
          [""],
          ["月份", "采购金额", "订单数量", "环比增长率(%)"]
        );
        costTrendData.trend_data?.forEach(t => {
          exportData.push([t.period, t.amount, t.order_count, t.mom_rate]);
        });
      } else if (activeTab === 'delivery-performance' && deliveryPerformanceData) {
        exportData.push(
          ["=== 供应商交期准时率 ==="],
          ["供应商总数", deliveryPerformanceData.summary?.total_suppliers || 0],
          ["平均准时率", `${deliveryPerformanceData.summary?.avg_on_time_rate || 0}%`],
          ["延期订单数", deliveryPerformanceData.summary?.total_delayed_orders || 0],
          [""],
          ["供应商名称", "交货总数", "准时交货", "延期交货", "准时率(%)", "平均延期天数"]
        );
        deliveryPerformanceData.supplier_performance?.forEach(s => {
          exportData.push([
            s.supplier_name,
            s.total_deliveries,
            s.on_time_deliveries,
            s.delayed_deliveries,
            s.on_time_rate,
            s.avg_delay_days
          ]);
        });
      } else if (activeTab === 'quality-rate' && qualityRateData) {
        exportData.push(
          ["=== 物料质量合格率 ==="],
          ["供应商总数", qualityRateData.summary?.total_suppliers || 0],
          ["平均合格率", `${qualityRateData.summary?.avg_pass_rate || 0}%`],
          ["高质量供应商数(≥98%)", qualityRateData.summary?.high_quality_suppliers || 0],
          ["低质量供应商数(<90%)", qualityRateData.summary?.low_quality_suppliers || 0]
        );
      }

      const csvContent = exportData
        .map((row) => row.map((cell) => `"${cell}"`).join(","))
        .join("\n");

      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", `采购分析_${activeTab}_${new Date().toISOString().split("T")[0]}.csv`);
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("导出失败:", error);
      alert("导出失败: " + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="container mx-auto space-y-6">
        {/* 页头 */}
        <div className="flex items-center justify-between">
          <PageHeader
            title="采购分析"
            description="采购成本、价格波动、供应商绩效全面分析"
          />
          <div className="flex items-center gap-3">
            {/* 时间范围筛选 */}
            <div className="flex items-center gap-2 bg-slate-800/50 rounded-lg px-3 py-2">
              <Calendar className="w-4 h-4 text-slate-400" />
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="bg-transparent text-sm text-slate-300 outline-none"
              >
                <option value="3month">最近3个月</option>
                <option value="6month">最近6个月</option>
                <option value="year">最近1年</option>
              </select>
            </div>
            <Button onClick={handleExport} variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              导出报表
            </Button>
          </div>
        </div>

        {/* Tab内容 */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800/50">
            <TabsTrigger value="cost-trend">成本趋势</TabsTrigger>
            <TabsTrigger value="price-fluctuation">价格波动</TabsTrigger>
            <TabsTrigger value="delivery-performance">交期准时率</TabsTrigger>
            <TabsTrigger value="request-efficiency">采购时效</TabsTrigger>
            <TabsTrigger value="quality-rate">质量合格率</TabsTrigger>
          </TabsList>

          {/* 成本趋势 */}
          <TabsContent value="cost-trend" className="space-y-4">
            {costTrendData?.summary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">期间采购总额</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {formatAmount(costTrendData.summary.total_amount)}
                        </div>
                      </div>
                      <DollarSign className="w-10 h-10 text-emerald-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">期间订单数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {costTrendData.summary.total_orders || 0}
                        </div>
                      </div>
                      <ShoppingCart className="w-10 h-10 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">月均采购额</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {formatAmount(costTrendData.summary.avg_monthly_amount)}
                        </div>
                      </div>
                      <BarChart3 className="w-10 h-10 text-purple-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">最高月采购额</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {formatAmount(costTrendData.summary.max_month_amount)}
                        </div>
                      </div>
                      <TrendingUp className="w-10 h-10 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* 成本趋势图表 */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle>采购成本趋势</CardTitle>
                <CardDescription>按月统计采购金额变化</CardDescription>
              </CardHeader>
              <CardContent>
                {costTrendData?.trend_data?.length > 0 ? (
                  <div className="space-y-4">
                    {/* 简单趋势图 */}
                    <div className="h-64 flex items-end gap-2">
                      {costTrendData.trend_data.map((item, index) => {
                        const maxValue = Math.max(...costTrendData.trend_data.map(d => d.amount));
                        const height = (item.amount / maxValue) * 100;
                        return (
                          <div key={index} className="flex-1 flex flex-col items-center">
                            <div
                              className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t hover:from-blue-500 hover:to-blue-300 transition-all cursor-pointer relative group"
                              style={{ height: `${height}%`, minHeight: height > 0 ? '20px' : '0' }}
                            >
                              <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-900 px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                ¥{item.amount.toLocaleString()}
                              </div>
                            </div>
                            <div className="text-xs text-slate-400 mt-2">{item.period}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">暂无数据</div>
                )}
              </CardContent>
            </Card>

            {/* 成本趋势表格 */}
            {costTrendData?.trend_data?.length > 0 && (
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle>月度明细</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">月份</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">采购金额</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">订单数量</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">平均订单额</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">环比增长率</th>
                        </tr>
                      </thead>
                      <tbody>
                        {costTrendData.trend_data.map((item, index) => (
                          <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                            <td className="py-3 px-4">{item.period}</td>
                            <td className="text-right py-3 px-4 font-medium">¥{item.amount?.toLocaleString()}</td>
                            <td className="text-right py-3 px-4">{item.order_count}</td>
                            <td className="text-right py-3 px-4">¥{item.avg_amount?.toLocaleString()}</td>
                            <td className="text-right py-3 px-4">
                              {item.mom_rate !== undefined ? (
                                <span className={`flex items-center justify-end gap-1 ${item.mom_rate >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                  {item.mom_rate >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                  {item.mom_rate}%
                                </span>
                              ) : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* 价格波动 */}
          <TabsContent value="price-fluctuation" className="space-y-4">
            {priceFluctuationData?.summary && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">分析物料数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {priceFluctuationData.summary.total_materials || 0}
                        </div>
                      </div>
                      <BarChart3 className="w-10 h-10 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">高波动物料数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {priceFluctuationData.summary.high_volatility_count || 0}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">波动率 > 20%</div>
                      </div>
                      <AlertTriangle className="w-10 h-10 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">平均波动率</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {priceFluctuationData.summary.avg_volatility || 0}%
                        </div>
                      </div>
                      <TrendingUp className="w-10 h-10 text-purple-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* 价格波动列表 */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle>物料价格波动详情</CardTitle>
                <CardDescription>按波动率排序显示物料价格变化</CardDescription>
              </CardHeader>
              <CardContent>
                {priceFluctuationData?.materials?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">物料编码</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">物料名称</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">分类</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">最低价</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">最高价</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">平均价</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">最新价</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">波动率</th>
                        </tr>
                      </thead>
                      <tbody>
                        {priceFluctuationData.materials.map((item, index) => (
                          <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                            <td className="py-3 px-4 font-medium">{item.material_code}</td>
                            <td className="py-3 px-4">{item.material_name}</td>
                            <td className="py-3 px-4 text-slate-400">{item.category_name || '-'}</td>
                            <td className="text-right py-3 px-4">¥{item.min_price?.toFixed(4)}</td>
                            <td className="text-right py-3 px-4">¥{item.max_price?.toFixed(4)}</td>
                            <td className="text-right py-3 px-4">¥{item.avg_price?.toFixed(4)}</td>
                            <td className="text-right py-3 px-4">¥{item.latest_price?.toFixed(4)}</td>
                            <td className="text-right py-3 px-4">
                              <Badge className={item.price_volatility > 20 ? 'bg-amber-500' : 'bg-slate-600'}>
                                {item.price_volatility}%
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">暂无数据</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 交期准时率 */}
          <TabsContent value="delivery-performance" className="space-y-4">
            {deliveryPerformanceData?.summary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">供应商总数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {deliveryPerformanceData.summary.total_suppliers || 0}
                        </div>
                      </div>
                      <Truck className="w-10 h-10 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">平均准时率</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {deliveryPerformanceData.summary.avg_on_time_rate || 0}%
                        </div>
                      </div>
                      <Award className="w-10 h-10 text-emerald-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">延期订单数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {deliveryPerformanceData.summary.total_delayed_orders || 0}
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
                        <div className="text-sm text-slate-400">准时交货率</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {deliveryPerformanceData.summary.avg_on_time_rate >= 90 ? (
                            <span className="text-emerald-400">优秀</span>
                          ) : deliveryPerformanceData.summary.avg_on_time_rate >= 75 ? (
                            <span className="text-amber-400">良好</span>
                          ) : (
                            <span className="text-red-400">需改进</span>
                          )}
                        </div>
                      </div>
                      <Clock className="w-10 h-10 text-purple-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* 供应商绩效表格 */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle>供应商交期绩效排名</CardTitle>
                <CardDescription>按准时率降序排列</CardDescription>
              </CardHeader>
              <CardContent>
                {deliveryPerformanceData?.supplier_performance?.length > 0 ? (
                  <div className="space-y-3">
                    {deliveryPerformanceData.supplier_performance.map((item, index) => (
                      <div key={item.supplier_id} className="flex items-center gap-4 p-4 bg-slate-700/30 rounded-lg">
                        <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center font-bold">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium">{item.supplier_name}</div>
                          <div className="text-xs text-slate-400">{item.supplier_code}</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-slate-400">交货总数</div>
                          <div className="font-medium">{item.total_deliveries}</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-slate-400">准时交货</div>
                          <div className="font-medium text-emerald-400">{item.on_time_deliveries}</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-slate-400">延期交货</div>
                          <div className="font-medium text-red-400">{item.delayed_deliveries}</div>
                        </div>
                        <div className="text-center">
                          <div className="text-sm text-slate-400">准时率</div>
                          <Badge className={item.on_time_rate >= 90 ? 'bg-emerald-500' : item.on_time_rate >= 75 ? 'bg-amber-500' : 'bg-red-500'}>
                            {item.on_time_rate}%
                          </Badge>
                        </div>
                        {item.avg_delay_days > 0 && (
                          <div className="text-center">
                            <div className="text-sm text-slate-400">平均延期</div>
                            <div className="font-medium text-amber-400">{item.avg_delay_days}天</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">暂无数据</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 采购时效 */}
          <TabsContent value="request-efficiency" className="space-y-4">
            {requestEfficiencyData?.summary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">申请总数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {requestEfficiencyData.summary.total_requests || 0}
                        </div>
                      </div>
                      <ShoppingCart className="w-10 h-10 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">已处理</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {requestEfficiencyData.summary.processed_count || 0}
                        </div>
                      </div>
                      <Award className="w-10 h-10 text-emerald-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">待处理</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {requestEfficiencyData.summary.pending_count || 0}
                        </div>
                      </div>
                      <Clock className="w-10 h-10 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">24h处理率</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {requestEfficiencyData.summary.within_24h_rate || 0}%
                        </div>
                      </div>
                      <TrendingUp className="w-10 h-10 text-purple-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* 处理时效详情 */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle>采购申请处理时效详情</CardTitle>
                <CardDescription>按处理时长降序排列</CardDescription>
              </CardHeader>
              <CardContent>
                {requestEfficiencyData?.efficiency_data?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">申请单号</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">状态</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">申请金额</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">处理时长</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">申请时间</th>
                        </tr>
                      </thead>
                      <tbody>
                        {requestEfficiencyData.efficiency_data.map((item, index) => (
                          <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                            <td className="py-3 px-4 font-medium">{item.request_no}</td>
                            <td className="py-3 px-4">
                              <Badge className={item.is_pending ? 'bg-amber-500' : 'bg-emerald-500'}>
                                {item.is_pending ? '待处理' : item.status}
                              </Badge>
                            </td>
                            <td className="text-right py-3 px-4">¥{item.amount?.toLocaleString()}</td>
                            <td className="text-right py-3 px-4">
                              {item.is_pending ? (
                                <span className="text-amber-400">{item.processing_days}天 (进行中)</span>
                              ) : (
                                <span>{item.processing_days}天</span>
                              )}
                            </td>
                            <td className="py-3 px-4 text-slate-400">{item.requested_at?.split('T')[0]}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">暂无数据</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 质量合格率 */}
          <TabsContent value="quality-rate" className="space-y-4">
            {qualityRateData?.summary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">供应商总数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {qualityRateData.summary.total_suppliers || 0}
                        </div>
                      </div>
                      <Truck className="w-10 h-10 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">平均合格率</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {qualityRateData.summary.avg_pass_rate || 0}%
                        </div>
                      </div>
                      <Award className="w-10 h-10 text-emerald-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">高质量供应商</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {qualityRateData.summary.high_quality_suppliers || 0}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">≥98%</div>
                      </div>
                      <TrendingUp className="w-10 h-10 text-emerald-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">需关注供应商</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {qualityRateData.summary.low_quality_suppliers || 0}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">&lt;90%</div>
                      </div>
                      <AlertTriangle className="w-10 h-10 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* 供应商质量列表 */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle>供应商质量合格率排名</CardTitle>
                <CardDescription>按综合合格率降序排列</CardDescription>
              </CardHeader>
              <CardContent>
                {qualityRateData?.supplier_quality?.length > 0 ? (
                  <div className="space-y-4">
                    {qualityRateData.supplier_quality.map((item, index) => (
                      <div key={item.supplier_id} className="p-4 bg-slate-700/30 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${index < 3 ? 'bg-blue-500' : 'bg-slate-600'}`}>
                              {index + 1}
                            </div>
                            <div>
                              <div className="font-medium">{item.supplier_name}</div>
                              <div className="text-xs text-slate-400">物料数: {item.material_count}</div>
                            </div>
                          </div>
                          <Badge className={item.overall_pass_rate >= 98 ? 'bg-emerald-500' : item.overall_pass_rate >= 90 ? 'bg-amber-500' : 'bg-red-500'}>
                            {item.overall_pass_rate}% 合格率
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-slate-400">合格数量: </span>
                            <span className="font-medium text-emerald-400">{item.total_qualified?.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-slate-400">不合格数量: </span>
                            <span className="font-medium text-red-400">{item.total_rejected?.toLocaleString()}</span>
                          </div>
                          <div>
                            <span className="text-slate-400">检验总数: </span>
                            <span className="font-medium">{item.total_qty?.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">暂无数据</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
