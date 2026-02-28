import { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { rdProjectApi, rdReportApi } from "../services/api";
import { formatDate as _formatDate, formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  Select,
  Table } from
"../components/ui";
import {
  ArrowLeft,
  Download,
  FileText,
  Calculator,
  TrendingUp,
  BarChart3,
  Users,
  Calendar,
  Search } from
"lucide-react";

const reportTypes = [
{
  id: "auxiliary-ledger",
  name: "研发费用辅助账",
  description: "税务要求的辅助账格式，按项目、按费用类型汇总",
  icon: FileText,
  color: "primary"
},
{
  id: "deduction-detail",
  name: "加计扣除明细",
  description: "研发费用加计扣除明细表，按项目、按类型汇总",
  icon: Calculator,
  color: "emerald"
},
{
  id: "high-tech",
  name: "高新企业费用表",
  description: "高新技术企业认定要求的费用表，按六大费用类型汇总",
  icon: TrendingUp,
  color: "blue"
},
{
  id: "intensity",
  name: "研发投入强度",
  description: "研发费用/营业收入，用于计算研发投入强度",
  icon: BarChart3,
  color: "purple"
},
{
  id: "personnel",
  name: "研发人员统计",
  description: "研发人员占比、工时分配统计",
  icon: Users,
  color: "indigo"
}];


export default function RdCostReports() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [reportType, setReportType] = useState("auxiliary-ledger");
  const [reportData, setReportData] = useState(null);
  const [filters, setFilters] = useState({
    start_date: "",
    end_date: "",
    project_id: id || ""
  });
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (id) {
      fetchProject();
      // 从URL参数中获取报表类型
      const params = new URLSearchParams(location.search);
      const type = params.get("type");
      if (type) {
        setReportType(type);
      }
    }
  }, [id, location]);

  useEffect(() => {
    if (id && reportType) {
      fetchReportData();
    }
  }, [id, reportType, filters]);

  const fetchProject = async () => {
    try {
      const response = await rdProjectApi.get(id);
      const projectData = response.data?.data || response.data || response;
      setProject(projectData);
    } catch (err) {
      console.error("Failed to fetch project:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const params = {
        rd_project_id: id,
        ...filters
      };

      let response;
      switch (reportType) {
        case "auxiliary-ledger":
          response = await rdReportApi.getAuxiliaryLedger(params);
          break;
        case "deduction-detail":
          response = await rdReportApi.getDeductionDetail(params);
          break;
        case "high-tech":
          response = await rdReportApi.getHighTechReport(params);
          break;
        case "intensity":
          response = await rdReportApi.getIntensityReport(params);
          break;
        case "personnel":
          response = await rdReportApi.getPersonnelReport(params);
          break;
        default:
          return;
      }

      const data = response.data?.data || response.data || response;
      setReportData(data);
    } catch (err) {
      console.error("Failed to fetch report data:", err);
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const params = {
        rd_project_id: id,
        report_type: reportType,
        format: "excel",
        ...filters
      };

      const response = await rdReportApi.exportReport(params);

      // 创建下载链接
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${project?.project_name || "研发费用报表"}_${reportType}_${new Date().toISOString().split("T")[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("导出失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setExporting(false);
    }
  };

  if (loading && !project) {
    return <div className="text-center py-12">加载中...</div>;
  }

  const selectedReport =
  (reportTypes || []).find((r) => r.id === reportType) || reportTypes[0];

  return (
    <motion.div initial="hidden" animate="visible">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(`/rd-projects/${id}`)}>

            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">研发费用报表</h1>
            <p className="text-sm text-slate-400 mt-1">
              {project?.project_name}
            </p>
          </div>
        </div>
        <Button onClick={handleExport} loading={exporting}>
          <Download className="h-4 w-4 mr-2" />
          导出报表
        </Button>
      </div>

      {/* Report Type Selector */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {(reportTypes || []).map((report) =>
            <button
              key={report.id}
              onClick={() => setReportType(report.id)}
              className={cn(
                "p-4 rounded-lg border-2 transition-all text-left",
                reportType === report.id ?
                "border-primary bg-primary/10" :
                "border-white/10 bg-white/[0.02] hover:border-white/20"
              )}>

                <div
                className={cn(
                  "p-2 rounded-lg w-fit mb-3",
                  reportType === report.id ? "bg-primary/20" : "bg-white/5"
                )}>

                  {(() => { const DynIcon = report.icon; return <DynIcon
                  className={cn(
                    "h-5 w-5",
                    reportType === report.id ?
                    "text-primary" :
                    "text-slate-400"
                  )}  />; })()}

                </div>
                <h3
                className={cn(
                  "font-semibold mb-1",
                  reportType === report.id ? "text-white" : "text-slate-300"
                )}>

                  {report.name}
                </h3>
                <p className="text-xs text-slate-500">{report.description}</p>
            </button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">
                开始日期
              </label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) =>
                setFilters({ ...filters, start_date: e.target.value })
                }
                className="w-40" />

            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-2">
                结束日期
              </label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) =>
                setFilters({ ...filters, end_date: e.target.value })
                }
                className="w-40" />

            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={fetchReportData}
                className="ml-2">

                <Search className="h-4 w-4 mr-2" />
                查询
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report Content */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              {(() => { const DynIcon = selectedReport.icon; return <DynIcon className="h-5 w-5 text-primary"  />; })()}
              {selectedReport.name}
            </h3>
          </div>

          {loading ?
          <div className="text-center py-12 text-slate-500">加载中...</div> :
          reportData ?
          <div className="space-y-6">
              {/* Summary Stats */}
              {reportData.summary &&
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(reportData.summary).map(([key, value]) =>
              <div
                key={key}
                className="p-4 rounded-lg bg-white/[0.03] border border-white/5">

                      <p className="text-sm text-slate-400 mb-1">{key}</p>
                      <p className="text-xl font-semibold text-white">
                        {typeof value === "number" ?
                  value % 1 === 0 ?
                  value :
                  value.toFixed(2) :
                  typeof value === "string" && value.includes("¥") ?
                  value :
                  formatCurrency(value)}
                      </p>
              </div>
              )}
            </div>
            }

              {/* Table Data */}
              {reportData.items && reportData.items?.length > 0 &&
            <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/10">
                        {Object.keys(reportData.items[0]).map((key) =>
                    <th
                      key={key}
                      className="px-4 py-3 text-left text-sm font-medium text-slate-400">

                            {key}
                    </th>
                    )}
                      </tr>
                    </thead>
                    <tbody>
                      {(reportData.items || []).map((row, idx) =>
                  <tr
                    key={idx}
                    className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">

                          {Object.values(row).map((cell, cellIdx) =>
                    <td
                      key={cellIdx}
                      className="px-4 py-3 text-sm text-white">

                              {typeof cell === "number" ?
                      cell % 1 === 0 ?
                      cell :
                      cell.toFixed(2) :
                      cell}
                    </td>
                    )}
                  </tr>
                  )}
                    </tbody>
                  </table>
            </div>
            }

              {/* Chart Data */}
              {reportData.chart &&
            <div className="p-4 rounded-lg bg-white/[0.03] border border-white/5">
                  <p className="text-sm text-slate-400 mb-2">图表数据</p>
                  <pre className="text-xs text-slate-300 overflow-x-auto">
                    {JSON.stringify(reportData.chart, null, 2)}
                  </pre>
            </div>
            }

              {/* No Data */}
              {(!reportData.items || reportData.items?.length === 0) &&
            !reportData.summary &&
            <div className="text-center py-12 text-slate-500">
                    <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
                    <p>暂无报表数据</p>
                    <p className="text-xs mt-2">请调整筛选条件后重试</p>
            </div>
            }
          </div> :

          <div className="text-center py-12 text-slate-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p>加载报表数据失败</p>
              <Button
              variant="outline"
              className="mt-4"
              onClick={fetchReportData}>

                重试
              </Button>
          </div>
          }
        </CardContent>
      </Card>
    </motion.div>);

}