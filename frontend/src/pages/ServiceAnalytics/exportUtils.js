import { toast } from "../../components/ui/toast";
import { PERIOD_LABEL } from "./constants";

/**
 * Builds the export-data shape used by both CSV and Excel renderers.
 */
function buildExportData(analytics, period) {
  return {
    统计周期: PERIOD_LABEL[period] || period,
    导出日期: new Date().toLocaleDateString("zh-CN"),
    概览: {
      工单总数:     analytics.overview.totalTickets,
      服务记录数:   analytics.overview.totalRecords,
      沟通记录数:   analytics.overview.totalCommunications,
      满意度调查数: analytics.overview.totalSurveys,
      平均响应时间: `${analytics.overview.averageResponseTime}小时`,
      平均解决时间: `${analytics.overview.averageResolutionTime}小时`,
      平均满意度:   analytics.overview.averageSatisfaction,
      完成率:       `${analytics.overview.completionRate}%`
    },
    工单趋势: (analytics.ticketTrends || []).map((t) => ({
      月份: t.month, 工单数: t.count, 已解决: t.resolved
    })),
    服务类型分布: (analytics.serviceTypeDistribution || []).map((d) => ({
      类型: d.type, 数量: d.count, 占比: `${d.percentage}%`
    })),
    问题类型分布: (analytics.problemTypeDistribution || []).map((d) => ({
      类型: d.type, 数量: d.count, 占比: `${d.percentage}%`
    })),
    响应时间分布: (analytics.responseTimeDistribution || []).map((d) => ({
      时间范围: d.range, 数量: d.count, 占比: `${d.percentage}%`
    }))
  };
}

/**
 * Generates an Excel-compatible HTML string from the export data object.
 */
function generateExcelHTML(data) {
  let html = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head>
      <meta charset="utf-8">
      <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4f46e5; color: white; font-weight: bold; }
        .section-title { background-color: #e5e7eb; font-weight: bold; }
      </style>
    </head>
    <body>
      <h2>服务数据分析报表</h2>
      <p>统计周期: ${data.统计周期}</p>
      <p>导出日期: ${data.导出日期}</p>
      <br>
  `;

  html += '<table><tr class="section-title"><th colspan="2">概览数据</th></tr><tr><th>项目</th><th>数值</th></tr>';
  Object.entries(data.概览).forEach(([key, value]) => {
    html += `<tr><td>${key}</td><td>${value}</td></tr>`;
  });
  html += "</table><br>";

  if (data.工单趋势?.length > 0) {
    html += '<table><tr class="section-title"><th colspan="3">工单趋势</th></tr><tr><th>月份</th><th>工单数</th><th>已解决</th></tr>';
    data.工单趋势.forEach((t) => {
      html += `<tr><td>${t.月份}</td><td>${t.工单数}</td><td>${t.已解决}</td></tr>`;
    });
    html += "</table><br>";
  }

  if (data.服务类型分布?.length > 0) {
    html += '<table><tr class="section-title"><th colspan="3">服务类型分布</th></tr><tr><th>类型</th><th>数量</th><th>占比</th></tr>';
    data.服务类型分布.forEach((d) => {
      html += `<tr><td>${d.类型}</td><td>${d.数量}</td><td>${d.占比}</td></tr>`;
    });
    html += "</table><br>";
  }

  if (data.问题类型分布?.length > 0) {
    html += '<table><tr class="section-title"><th colspan="3">问题类型分布</th></tr><tr><th>类型</th><th>数量</th><th>占比</th></tr>';
    data.问题类型分布.forEach((d) => {
      html += `<tr><td>${d.类型}</td><td>${d.数量}</td><td>${d.占比}</td></tr>`;
    });
    html += "</table><br>";
  }

  if (data.响应时间分布?.length > 0) {
    html += '<table><tr class="section-title"><th colspan="3">响应时间分布</th></tr><tr><th>时间范围</th><th>数量</th><th>占比</th></tr>';
    data.响应时间分布.forEach((d) => {
      html += `<tr><td>${d.时间范围}</td><td>${d.数量}</td><td>${d.占比}</td></tr>`;
    });
    html += "</table>";
  }

  html += "</body></html>";
  return html;
}

/**
 * Triggers a browser file download.
 */
function triggerDownload(blob, filename) {
  const url  = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Exports analytics data as CSV or Excel.
 *
 * @param {object} analytics  – the analytics state object
 * @param {string} period     – active period key ("DAILY" | "WEEKLY" | …)
 * @param {"csv"|"excel"} format
 */
export function handleExport(analytics, period, format = "csv") {
  if (!analytics) {
    toast.error("暂无数据可导出");
    return;
  }

  try {
    const data      = buildExportData(analytics, period);
    const dateStamp = new Date().toISOString().split("T")[0];

    if (format === "excel") {
      const htmlContent = generateExcelHTML(data);
      const blob = new Blob([htmlContent], { type: "application/vnd.ms-excel" });
      triggerDownload(blob, `服务数据分析报表_${period}_${dateStamp}.xls`);
      toast.success("Excel报表导出成功");
    } else {
      const csvRows = [];

      csvRows.push("=== 概览数据 ===", "项目,数值");
      Object.entries(data.概览).forEach(([key, value]) => {
        csvRows.push(`"${key}","${value}"`);
      });
      csvRows.push("");

      if (data.工单趋势?.length > 0) {
        csvRows.push("=== 工单趋势 ===", "月份,工单数,已解决");
        data.工单趋势.forEach((t) => {
          csvRows.push(`"${t.月份}",${t.工单数},${t.已解决}`);
        });
        csvRows.push("");
      }

      if (data.服务类型分布?.length > 0) {
        csvRows.push("=== 服务类型分布 ===", "类型,数量,占比");
        data.服务类型分布.forEach((d) => {
          csvRows.push(`"${d.类型}",${d.数量},"${d.占比}"`);
        });
        csvRows.push("");
      }

      if (data.问题类型分布?.length > 0) {
        csvRows.push("=== 问题类型分布 ===", "类型,数量,占比");
        data.问题类型分布.forEach((d) => {
          csvRows.push(`"${d.类型}",${d.数量},"${d.占比}"`);
        });
        csvRows.push("");
      }

      if (data.响应时间分布?.length > 0) {
        csvRows.push("=== 响应时间分布 ===", "时间范围,数量,占比");
        data.响应时间分布.forEach((d) => {
          csvRows.push(`"${d.时间范围}",${d.数量},"${d.占比}"`);
        });
      }

      const BOM  = "\uFEFF";
      const blob = new Blob([BOM + csvRows.join("\n")], {
        type: "text/csv;charset=utf-8;"
      });
      triggerDownload(blob, `服务数据分析报表_${period}_${dateStamp}.csv`);
      toast.success("CSV报表导出成功");
    }
  } catch (err) {
    console.error("导出失败:", err);
    toast.error("导出失败: " + (err.message || "未知错误"));
  }
}
