/**
 * Shortage Report List Page - 缺料上报列表页面
 * Features: 缺料上报列表、创建、确认、处理、解决
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  XCircle,
  Package } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { cn as _cn, formatDate } from "../lib/utils";
import { shortageApi, projectApi } from "../services/api";
import { confirmAction } from "@/lib/confirmAction";
const statusConfigs = {
  REPORTED: { label: "已上报", color: "bg-blue-500" },
  CONFIRMED: { label: "已确认", color: "bg-emerald-500" },
  HANDLING: { label: "处理中", color: "bg-amber-500" },
  RESOLVED: { label: "已解决", color: "bg-green-500" },
  REJECTED: { label: "已驳回", color: "bg-red-500" }
};
const urgentLevelConfigs = {
  URGENT: { label: "紧急", color: "bg-red-500" },
  HIGH: { label: "高", color: "bg-orange-500" },
  MEDIUM: { label: "中", color: "bg-amber-500" },
  LOW: { label: "低", color: "bg-blue-500" }
};
export default function ShortageReportList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState([]);
  const [projects, setProjects] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterUrgentLevel, setFilterUrgentLevel] = useState("");
  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  useEffect(() => {
    fetchProjects();
    fetchReports();
  }, [filterProject, filterStatus, filterUrgentLevel, searchKeyword]);
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };
  const fetchReports = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject) {params.project_id = filterProject;}
      if (filterStatus) {params.status = filterStatus;}
      if (filterUrgentLevel) {params.urgent_level = filterUrgentLevel;}
      if (searchKeyword) {params.keyword = searchKeyword;}
      const res = await shortageApi.reports.list(params);
      const reportList = res.data?.items || res.data?.items || res.data || [];
      setReports(reportList);
    } catch (error) {
      console.error("Failed to fetch reports:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleViewDetail = async (reportId) => {
    try {
      const res = await shortageApi.reports.get(reportId);
      setSelectedReport(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch report detail:", error);
    }
  };
  const handleConfirm = async (reportId) => {
    if (!await confirmAction("确认此缺料上报？")) {return;}
    try {
      await shortageApi.reports.confirm(reportId);
      fetchReports();
      if (showDetailDialog) {
        handleViewDetail(reportId);
      }
    } catch (error) {
      console.error("Failed to confirm report:", error);
      alert("确认失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const filteredReports = useMemo(() => {
    return (reports || []).filter((report) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          report.report_no?.toLowerCase().includes(keyword) ||
          report.material_code?.toLowerCase().includes(keyword) ||
          report.material_name?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [reports, searchKeyword]);
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="缺料上报管理"
        description="缺料上报列表、创建、确认、处理、解决" />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索上报单号、物料编码..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {(projects || []).map((proj) =>
                <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.project_name}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select
              value={filterUrgentLevel}
              onValueChange={setFilterUrgentLevel}>

              <SelectTrigger>
                <SelectValue placeholder="选择紧急程度" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                {Object.entries(urgentLevelConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => navigate("/shortage-reports/new")}>
          <Plus className="w-4 h-4 mr-2" />
          新建缺料上报
        </Button>
      </div>
      {/* Report List */}
      <Card>
        <CardHeader>
          <CardTitle>缺料上报列表</CardTitle>
          <CardDescription>
            共 {filteredReports.length} 个缺料上报
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredReports.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无缺料上报</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>上报单号</TableHead>
                  <TableHead>物料编码</TableHead>
                  <TableHead>物料名称</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>缺料数量</TableHead>
                  <TableHead>紧急程度</TableHead>
                  <TableHead>上报时间</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(filteredReports || []).map((report) =>
              <TableRow key={report.id}>
                    <TableCell className="font-mono text-sm">
                      {report.report_no}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {report.material_code}
                    </TableCell>
                    <TableCell className="font-medium">
                      {report.material_name}
                    </TableCell>
                    <TableCell>{report.project_name || "-"}</TableCell>
                    <TableCell className="font-medium text-red-600">
                      {report.shortage_qty || 0}
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    urgentLevelConfigs[report.urgent_level]?.color ||
                    "bg-slate-500"
                    }>

                        {urgentLevelConfigs[report.urgent_level]?.label ||
                    report.urgent_level}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {report.report_time ?
                  formatDate(report.report_time) :
                  "-"}
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    statusConfigs[report.status]?.color || "bg-slate-500"
                    }>

                        {statusConfigs[report.status]?.label || report.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewDetail(report.id)}>

                          <Eye className="w-4 h-4" />
                        </Button>
                        {report.status === "REPORTED" &&
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleConfirm(report.id)}>

                            <CheckCircle2 className="w-4 h-4" />
                    </Button>
                    }
                      </div>
                    </TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>
      {/* Report Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedReport?.report_no} - 缺料上报详情
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedReport &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">上报单号</div>
                    <div className="font-mono">{selectedReport.report_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge
                    className={statusConfigs[selectedReport.status]?.color}>

                      {statusConfigs[selectedReport.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">物料编码</div>
                    <div className="font-mono">
                      {selectedReport.material_code}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">物料名称</div>
                    <div>{selectedReport.material_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedReport.project_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">缺料数量</div>
                    <div className="font-medium text-red-600">
                      {selectedReport.shortage_qty || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">紧急程度</div>
                    <Badge
                    className={
                    urgentLevelConfigs[selectedReport.urgent_level]?.color
                    }>

                      {urgentLevelConfigs[selectedReport.urgent_level]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">上报时间</div>
                    <div>
                      {selectedReport.report_time ?
                    formatDate(selectedReport.report_time) :
                    "-"}
                    </div>
                  </div>
                </div>
                {selectedReport.report_description &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">上报说明</div>
                    <div>{selectedReport.report_description}</div>
              </div>
              }
                {selectedReport.handle_plan &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">处理方案</div>
                    <div>{selectedReport.handle_plan}</div>
              </div>
              }
                {selectedReport.resolve_method &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">解决方式</div>
                    <div>{selectedReport.resolve_method}</div>
              </div>
              }
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            {selectedReport && selectedReport.status === "REPORTED" &&
            <Button onClick={() => handleConfirm(selectedReport.id)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                确认上报
            </Button>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}