/**
 * 采购分析页面
 * Features: 采购成本趋势、物料价格波动、供应商交期准时率、采购申请处理时效、物料质量合格率
 */
import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  ProcurementHeader,
  CostTrendTab,
  PriceFluctuationTab,
  DeliveryPerformanceTab,
  RequestEfficiencyTab,
  QualityRateTab,
  useProcurementData,
  TIME_RANGE_LABELS } from
'../components/procurement-analysis';

export default function ProcurementAnalysis() {
  const [activeTab, setActiveTab] = useState('cost-trend');
  const [timeRange, setTimeRange] = useState('6month'); // 3month, 6month, year

  // 使用自定义 Hook 管理数据
  const {
    loading: _loading,
    costTrendData,
    priceFluctuationData,
    deliveryPerformanceData,
    requestEfficiencyData,
    qualityRateData,
    loadCostTrend,
    loadPriceFluctuation,
    loadDeliveryPerformance,
    loadRequestEfficiency,
    loadQualityRate
  } = useProcurementData(timeRange);

  // 初始加载
  useEffect(() => {
    loadCostTrend();
  }, []);

  // Tab切换时加载对应数据
  useEffect(() => {
    if (activeTab === 'cost-trend') {loadCostTrend();}else
    if (activeTab === 'price-fluctuation') {loadPriceFluctuation();}else
    if (activeTab === 'delivery-performance') {loadDeliveryPerformance();}else
    if (activeTab === 'request-efficiency') {loadRequestEfficiency();}else
    if (activeTab === 'quality-rate') {loadQualityRate();}
  }, [activeTab, loadCostTrend, loadPriceFluctuation, loadDeliveryPerformance, loadRequestEfficiency, loadQualityRate]);

  // 导出报表
  const handleExport = () => {
    try {
      const exportData = [
      ['采购分析报表'],
      ['统计周期', TIME_RANGE_LABELS[timeRange] || timeRange],
      ['导出日期', new Date().toLocaleDateString('zh-CN')],
      ['']];


      // 根据当前Tab添加数据
      if (activeTab === 'cost-trend' && costTrendData) {
        exportData.push(
          ['=== 采购成本趋势 ==='],
          ['期间采购总额', `¥${costTrendData.summary?.total_amount?.toLocaleString() || 0}`],
          ['期间订单总数', costTrendData.summary?.total_orders || 0],
          ['月均采购额', `¥${costTrendData.summary?.avg_monthly_amount?.toLocaleString() || 0}`],
          [''],
          ['月份', '采购金额', '订单数量', '环比增长率(%)']
        );
        costTrendData.trend_data?.forEach((t) => {
          exportData.push([t.period, t.amount, t.order_count, t.mom_rate]);
        });
      } else if (activeTab === 'delivery-performance' && deliveryPerformanceData) {
        exportData.push(
          ['=== 供应商交期准时率 ==='],
          ['供应商总数', deliveryPerformanceData.summary?.total_suppliers || 0],
          ['平均准时率', `${deliveryPerformanceData.summary?.avg_on_time_rate || 0}%`],
          ['延期订单数', deliveryPerformanceData.summary?.total_delayed_orders || 0],
          [''],
          ['供应商名称', '交货总数', '准时交货', '延期交货', '准时率(%)', '平均延期天数']
        );
        deliveryPerformanceData.supplier_performance?.forEach((s) => {
          exportData.push([
          s.supplier_name,
          s.total_deliveries,
          s.on_time_deliveries,
          s.delayed_deliveries,
          s.on_time_rate,
          s.avg_delay_days]
          );
        });
      } else if (activeTab === 'quality-rate' && qualityRateData) {
        exportData.push(
          ['=== 物料质量合格率 ==='],
          ['供应商总数', qualityRateData.summary?.total_suppliers || 0],
          ['平均合格率', `${qualityRateData.summary?.avg_pass_rate || 0}%`],
          ['高质量供应商数(≥98%)', qualityRateData.summary?.high_quality_suppliers || 0],
          ['低质量供应商数(<90%)', qualityRateData.summary?.low_quality_suppliers || 0]
        );
      }

      const csvContent = exportData.
      map((row) => row.map((cell) => `"${cell}"`).join(',')).
      join('\n');

      const BOM = '\uFEFF';
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `采购分析_${activeTab}_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('导出失败:', error);
      alert('导出失败: ' + error.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="container mx-auto space-y-6">
        {/* 页头 */}
        <ProcurementHeader
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange}
          onExport={handleExport} />


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
          <TabsContent value="cost-trend">
            <CostTrendTab data={costTrendData} />
          </TabsContent>

          {/* 价格波动 */}
          <TabsContent value="price-fluctuation">
            <PriceFluctuationTab data={priceFluctuationData} />
          </TabsContent>

          {/* 交期准时率 */}
          <TabsContent value="delivery-performance">
            <DeliveryPerformanceTab data={deliveryPerformanceData} />
          </TabsContent>

          {/* 采购时效 */}
          <TabsContent value="request-efficiency">
            <RequestEfficiencyTab data={requestEfficiencyData} />
          </TabsContent>

          {/* 质量合格率 */}
          <TabsContent value="quality-rate">
            <QualityRateTab data={qualityRateData} />
          </TabsContent>
        </Tabs>
      </div>
    </div>);

}