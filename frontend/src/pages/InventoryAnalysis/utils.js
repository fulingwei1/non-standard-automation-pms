/**
 * Utility functions for Inventory Analysis
 */

/**
 * Format currency amount in CNY, using 万 for values >= 10000
 */
export const formatAmount = (amount) => {
  if (!amount) {return "¥0";}
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(1)}万`;
  }
  return `¥${amount.toLocaleString()}`;
};

/**
 * Build CSV export data based on the active tab and its data
 */
export function buildExportData(activeTab, { turnoverData, staleMaterialsData, safetyStockData, abcAnalysisData, costOccupancyData }) {
  const exportData = [
    ["库存分析报表"],
    ["导出日期", new Date().toLocaleDateString("zh-CN")],
    [""],
  ];

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

  return exportData;
}

/**
 * Download CSV content as a file
 */
export function downloadCsv(exportData, activeTab) {
  const csvContent = exportData
    .map((row) => (row || []).map((cell) => `"${cell}"`).join(","))
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
}
