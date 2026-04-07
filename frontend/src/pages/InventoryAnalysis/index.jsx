/**
 * 库存分析页面
 * Features: 库存周转率、呆滞物料预警、安全库存达标率、ABC分类、库存成本占用
 */
import { useState, useEffect, useCallback } from "react";
import { api } from "../../services/api";
import { buildExportData, downloadCsv } from "./utils";

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

  // 导出报表
  const handleExport = () => {
    try {
      const exportData = buildExportData(activeTab, {
        turnoverData,
        staleMaterialsData,
        safetyStockData,
        abcAnalysisData,
        costOccupancyData,
      });
      downloadCsv(exportData, activeTab);
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
        <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800/50">
            <TabsTrigger value="turnover-rate">周转率分析</TabsTrigger>
            <TabsTrigger value="stale-materials">呆滞物料</TabsTrigger>
            <TabsTrigger value="safety-stock">安全库存</TabsTrigger>
            <TabsTrigger value="abc-analysis">ABC分类</TabsTrigger>
            <TabsTrigger value="cost-occupancy">成本占用</TabsTrigger>
          </TabsList>

          <TabsContent value="turnover-rate">
            <TurnoverRateTab turnoverData={turnoverData} />
          </TabsContent>

          <TabsContent value="stale-materials">
            <StaleMaterialsTab
              staleMaterialsData={staleMaterialsData}
              staleThreshold={staleThreshold}
              setStaleThreshold={setStaleThreshold}
              loading={loading}
            />
          </TabsContent>

          <TabsContent value="safety-stock">
            <SafetyStockTab safetyStockData={safetyStockData} />
          </TabsContent>

          <TabsContent value="abc-analysis">
            <AbcAnalysisTab abcAnalysisData={abcAnalysisData} />
          </TabsContent>

          <TabsContent value="cost-occupancy">
            <CostOccupancyTab costOccupancyData={costOccupancyData} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
