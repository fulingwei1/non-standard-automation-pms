/**
 * 库存分析页面
 * Features: 库存周转率、呆滞物料预警、安全库存达标率、ABC分类、库存成本占用
 */
import { useState, useEffect, useCallback } from "react";
import {
  TrendingUp,
  TrendingDown,
  Package,
  AlertTriangle,
  Shield,
  BarChart3,
  PieChart,
  Download,
  Warehouse,
  Activity,
  DollarSign,
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
import { api } from "../services/api";

export default function InventoryAnalysis() {
  const [activeTab, setActiveTab] = useState("turnover-rate");
  const [loading, setLoading] = useState(false);

  // 各分析模块数据
  const [turnoverData, setTurnoverData] = useState(null);
  const [staleMaterialsData, setStaleMaterialsData] = useState(null);
  const [safetyStockData, setSafetyStockData] = useState(null);
  const [abcAnalysisData, setAbcAnalysisData] = useState(null);
  const [costOccupancyData, setCostOccupancyData] = useState(null);

  // 呆滞物料阈值
  const [staleThreshold, setStaleThreshold] = useState(90);

  // 获取库存周转率
  const loadTurnoverRate = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/inventory-analysis/turnover-rate");
      setTurnoverData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load turnover rate:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取呆滞物料
  const loadStaleMaterials = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/inventory-analysis/stale-materials", {
        params: { threshold_days: staleThreshold }
      });
      setStaleMaterialsData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load stale materials:", error);
    } finally {
      setLoading(false);
    }
  }, [staleThreshold]);

  // 获取安全库存达标率
  const loadSafetyStock = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/inventory-analysis/safety-stock-compliance");
      setSafetyStockData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load safety stock:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取ABC分类
  const loadAbcAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/inventory-analysis/abc-analysis");
      setAbcAnalysisData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load ABC analysis:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取库存成本占用
  const loadCostOccupancy = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get("/inventory-analysis/cost-occupancy");
      setCostOccupancyData(response.data?.data || response.data);
    } catch (error) {
      console.error("Failed to load cost occupancy:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    loadTurnoverRate();
  }, []);

  // Tab切换时加载对应数据
  useEffect(() => {
    if (activeTab === 'turnover-rate') {loadTurnoverRate();}
    else if (activeTab === 'stale-materials') {loadStaleMaterials();}
    else if (activeTab === 'safety-stock') {loadSafetyStock();}
    else if (activeTab === 'abc-analysis') {loadAbcAnalysis();}
    else if (activeTab === 'cost-occupancy') {loadCostOccupancy();}
  }, [activeTab]);

  // 呆滞阈值变化时重新加载
  useEffect(() => {
    if (activeTab === 'stale-materials' && staleMaterialsData) {
      loadStaleMaterials();
    }
  }, [staleThreshold]);

  // 格式化金额
  const formatAmount = (amount) => {
    if (!amount) {return "¥0";}
    if (amount >= 10000) {
      return `¥${(amount / 10000).toFixed(1)}万`;
    }
    return `¥${amount.toLocaleString()}`;
  };

  // 导出报表
  const handleExport = () => {
    try {
      const exportData = [
        ["库存分析报表"],
        ["导出日期", new Date().toLocaleDateString("zh-CN")],
        [""],
      ];

      // 根据当前Tab添加数据
      if (activeTab === 'turnover-rate' && turnoverData) {
        exportData.push(
          ["=== 库存周转率 ==="],
          ["库存总值", `¥${turnoverData.summary?.total_inventory_value?.toLocaleString() || 0}`],
          ["物料总数", turnoverData.summary?.total_materials || 0],
          ["周转率", turnoverData.summary?.turnover_rate || 0],
          ["周转天数", turnoverData.summary?.turnover_days || 0],
          [""],
          ["分类", "库存金额", "物料数量", "占比(%)"]
        );
        turnoverData.category_breakdown?.forEach(c => {
          exportData.push([c.category_name, c.inventory_value, c.material_count, c.value_percentage]);
        });
      } else if (activeTab === 'stale-materials' && staleMaterialsData) {
        exportData.push(
          ["=== 呆滞物料预警 ==="],
          ["呆滞物料数", staleMaterialsData.summary?.stale_count || 0],
          ["呆滞金额", `¥${staleMaterialsData.summary?.stale_value?.toLocaleString() || 0}`],
          ["库龄阈值", `${staleMaterialsData.summary?.threshold_days || 90}天`]
        );
      } else if (activeTab === 'safety-stock' && safetyStockData) {
        exportData.push(
          ["=== 安全库存达标率 ==="],
          ["物料总数", safetyStockData.summary?.total_materials || 0],
          ["达标率", `${safetyStockData.summary?.compliant_rate || 0}%`],
          ["达标数", safetyStockData.summary?.compliant || 0],
          ["预警数", safetyStockData.summary?.warning || 0],
          ["缺货数", safetyStockData.summary?.out_of_stock || 0]
        );
      } else if (activeTab === 'abc-analysis' && abcAnalysisData) {
        exportData.push(
          ["=== ABC分类分析 ==="],
          ["物料总数", abcAnalysisData.total_materials || 0],
          ["采购总额", `¥${abcAnalysisData.total_amount?.toLocaleString() || 0}`],
          [""],
          ["分类", "物料数量", "数量占比(%)", "金额占比(%)"]
        );
        const summary = abcAnalysisData.abc_summary || {};
        exportData.push(
          ["A类", summary.A?.count || 0, summary.A?.count_percent || 0, summary.A?.amount_percent || 0],
          ["B类", summary.B?.count || 0, summary.B?.count_percent || 0, summary.B?.amount_percent || 0],
          ["C类", summary.C?.count || 0, summary.C?.count_percent || 0, summary.C?.amount_percent || 0]
        );
      } else if (activeTab === 'cost-occupancy' && costOccupancyData) {
        exportData.push(
          ["=== 库存成本占用 ==="],
          ["库存总值", `¥${costOccupancyData.summary?.total_inventory_value?.toLocaleString() || 0}`],
          ["分类数", costOccupancyData.summary?.total_categories || 0],
          [""],
          ["分类", "库存金额", "物料数量", "占比(%)"]
        );
        costOccupancyData.category_occupancy?.forEach(c => {
          exportData.push([c.category_name, c.inventory_value, c.material_count, c.value_percentage]);
        });
      }

      const csvContent = exportData
        .map((row) => row.map((cell) => `"${cell}"`).join(","))
        .join("\n");

      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", `库存分析_${activeTab}_${new Date().toISOString().split("T")[0]}.csv`);
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
            title="库存分析"
            description="库存周转率、呆滞物料、安全库存全面监控"
          />
          <Button onClick={handleExport} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            导出报表
          </Button>
        </div>

        {/* Tab内容 */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800/50">
            <TabsTrigger value="turnover-rate">周转率分析</TabsTrigger>
            <TabsTrigger value="stale-materials">呆滞物料</TabsTrigger>
            <TabsTrigger value="safety-stock">安全库存</TabsTrigger>
            <TabsTrigger value="abc-analysis">ABC分类</TabsTrigger>
            <TabsTrigger value="cost-occupancy">成本占用</TabsTrigger>
          </TabsList>

          {/* 周转率分析 */}
          <TabsContent value="turnover-rate" className="space-y-4">
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
                    {turnoverData.category_breakdown.map((item, index) => (
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
          </TabsContent>

          {/* 呆滞物料 */}
          <TabsContent value="stale-materials" className="space-y-4">
            <div className="flex items-center justify-between">
              {staleMaterialsData?.summary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 flex-1">
                  <Card className="bg-slate-800/50 border-slate-700/50">
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-slate-400">呆滞物料数</div>
                          <div className="text-2xl font-bold text-white mt-1">
                            {staleMaterialsData.summary.stale_count || 0}
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
                          <div className="text-sm text-slate-400">呆滞金额</div>
                          <div className="text-2xl font-bold text-white mt-1">
                            {formatAmount(staleMaterialsData.summary.stale_value)}
                          </div>
                        </div>
                        <DollarSign className="w-10 h-10 text-red-500" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-slate-800/50 border-slate-700/50">
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-sm text-slate-400">总库存价值</div>
                          <div className="text-2xl font-bold text-white mt-1">
                            {formatAmount(staleMaterialsData.summary.total_value_with_stock)}
                          </div>
                        </div>
                        <Warehouse className="w-10 h-10 text-blue-500" />
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
              <div className="flex items-center gap-2">
                <label className="text-sm text-slate-400">库龄阈值:</label>
                <select
                  value={staleThreshold}
                  onChange={(e) => setStaleThreshold(parseInt(e.target.value))}
                  className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                >
                  <option value={30}>30天</option>
                  <option value={60}>60天</option>
                  <option value={90}>90天</option>
                  <option value={120}>120天</option>
                  <option value={180}>180天</option>
                </select>
              </div>
            </div>

            {/* 库龄分布 */}
            {staleMaterialsData?.age_distribution && (
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle>库龄分布</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4">
                    {staleMaterialsData.age_distribution.map((item, index) => {
                      const colors = ['text-emerald-400', 'text-blue-400', 'text-amber-400', 'text-red-400'];
                      return (
                        <div key={index} className="text-center">
                          <div className={`text-2xl font-bold ${colors[index]}`}>
                            {formatAmount(item.value)}
                          </div>
                          <div className="text-sm text-slate-400 mt-1">{item.age_range}</div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 呆滞物料列表 */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle>呆滞物料详情</CardTitle>
                <CardDescription>按库存金额降序排列</CardDescription>
              </CardHeader>
              <CardContent>
                {staleMaterialsData?.stale_materials?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">物料编码</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">物料名称</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">分类</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">当前库存</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">库存价值</th>
                          <th className="text-right py-3 px-4 text-slate-400 font-medium">库龄(天)</th>
                          <th className="text-left py-3 px-4 text-slate-400 font-medium">最后变动</th>
                        </tr>
                      </thead>
                      <tbody>
                        {staleMaterialsData.stale_materials.map((item, index) => (
                          <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                            <td className="py-3 px-4 font-medium">{item.material_code}</td>
                            <td className="py-3 px-4">{item.material_name}</td>
                            <td className="py-3 px-4 text-slate-400">{item.category_name || '-'}</td>
                            <td className="text-right py-3 px-4">{item.current_stock} {item.unit}</td>
                            <td className="text-right py-3 px-4">{formatAmount(item.inventory_value)}</td>
                            <td className="text-right py-3 px-4">
                              <Badge className={item.stale_days > 180 ? 'bg-red-500' : item.stale_days > 90 ? 'bg-amber-500' : 'bg-blue-500'}>
                                {item.stale_days}天
                              </Badge>
                            </td>
                            <td className="py-3 px-4 text-slate-400">{item.last_activity?.split('T')[0]}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    {loading ? '加载中...' : '暂无呆滞物料'}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 安全库存 */}
          <TabsContent value="safety-stock" className="space-y-4">
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
          </TabsContent>

          {/* ABC分类 */}
          <TabsContent value="abc-analysis" className="space-y-4">
            {abcAnalysisData?.abc_summary && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-slate-800/50 border-slate-700/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-400">物料总数</div>
                        <div className="text-2xl font-bold text-white mt-1">
                          {abcAnalysisData.total_materials || 0}
                        </div>
                      </div>
                      <Package className="w-10 h-10 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-red-950/30 border border-red-900/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-red-400">A类物料</div>
                        <div className="text-2xl font-bold text-red-400 mt-1">
                          {abcAnalysisData.abc_summary.A.count || 0}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">占金额70%</div>
                      </div>
                      <BarChart3 className="w-10 h-10 text-red-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-amber-950/30 border border-amber-900/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-amber-400">B类物料</div>
                        <div className="text-2xl font-bold text-amber-400 mt-1">
                          {abcAnalysisData.abc_summary.B.count || 0}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">占金额20%</div>
                      </div>
                      <BarChart3 className="w-10 h-10 text-amber-500" />
                    </div>
                  </CardContent>
                </Card>
                <Card className="bg-emerald-950/30 border border-emerald-900/50">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm text-emerald-400">C类物料</div>
                        <div className="text-2xl font-bold text-emerald-400 mt-1">
                          {abcAnalysisData.abc_summary.C.count || 0}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">占金额10%</div>
                      </div>
                      <BarChart3 className="w-10 h-10 text-emerald-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* ABC分类分布图 */}
            {abcAnalysisData?.abc_summary && (
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle>ABC分类分布</CardTitle>
                  <CardDescription>按采购金额累计占比分类</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {['A', 'B', 'C'].map((cls) => {
                      const summary = abcAnalysisData.abc_summary[cls];
                      const colors = {
                        A: 'from-red-600 to-red-400',
                        B: 'from-amber-600 to-amber-400',
                        C: 'from-emerald-600 to-emerald-400'
                      };
                      const textColors = {
                        A: 'text-red-400',
                        B: 'text-amber-400',
                        C: 'text-emerald-400'
                      };
                      return (
                        <div key={cls} className="flex items-center gap-4">
                          <div className={`w-16 text-lg font-bold ${textColors[cls]}`}>{cls}类</div>
                          <div className="flex-1 bg-slate-700 rounded-full h-8 overflow-hidden">
                            <div
                              className={`h-full bg-gradient-to-r ${colors[cls]} flex items-center justify-end pr-3`}
                              style={{ width: `${summary.amount_percent}%` }}
                            >
                              <span className="text-sm font-medium text-white">
                                {summary.amount_percent}%
                              </span>
                            </div>
                          </div>
                          <div className="w-24 text-right text-sm text-slate-400">
                            {summary.count}个
                          </div>
                          <div className="w-24 text-right text-sm text-slate-400">
                            {summary.count_percent}%
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* 成本占用 */}
          <TabsContent value="cost-occupancy" className="space-y-4">
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
                    {costOccupancyData.category_occupancy.map((item, index) => (
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
                    {costOccupancyData.top_materials.map((item, index) => (
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
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
