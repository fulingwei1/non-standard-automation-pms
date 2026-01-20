/**
 * Shortage Alert Page - 缺料预警页面
 * Features: 缺料预警列表、详情、确认、处理、统计分析
 */
import { useState, useEffect, useMemo } from "react";
import {
  AlertTriangle,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Package,
  TrendingUp,
  Calendar,
  User,
  RefreshCw,
  BarChart3,
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
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui/dialog";
import { cn, formatDate } from "../lib/utils";
import { shortageAlertApi, projectApi } from "../services/api";
const statusConfigs = {
  PENDING: { label: "待处理", color: "bg-blue-500" },
  ACKNOWLEDGED: { label: "已确认", color: "bg-amber-500" },
  PROCESSING: { label: "处理中", color: "bg-purple-500" },
  RESOLVED: { label: "已解决", color: "bg-emerald-500" },
  CLOSED: { label: "已关闭", color: "bg-slate-500" },
};
const levelConfigs = {
  LEVEL1: { label: "一级预警", color: "bg-red-500", urgency: "紧急" },
  LEVEL2: { label: "二级预警", color: "bg-orange-500", urgency: "重要" },
  LEVEL3: { label: "三级预警", color: "bg-amber-500", urgency: "一般" },
  LEVEL4: { label: "四级预警", color: "bg-blue-500", urgency: "提醒" },
};
export default function ShortageAlert() {
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterLevel, setFilterLevel] = useState("all");
  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showHandleDialog, setShowHandleDialog] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  // Form state
  const [handleData, setHandleData] = useState({
    solution: "",
    status: "PROCESSING",
    remark: "",
  });
  useEffect(() => {
    fetchProjects();
    fetchAlerts();
    fetchSummary();
  }, [filterProject, filterStatus, filterLevel, searchKeyword]);
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };
  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject && filterProject !== "all")
        {params.project_id = filterProject;}
      if (filterStatus && filterStatus !== "all") {params.status = filterStatus;}
      if (filterLevel && filterLevel !== "all")
        {params.alert_level = filterLevel;}
      if (searchKeyword) {params.search = searchKeyword;}
      const res = await shortageAlertApi.list(params);
      const alertList = res.data?.items || res.data || [];
      setAlerts(alertList);
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  };
  const fetchSummary = async () => {
    try {
      const res = await shortageAlertApi.getSummary();
      setSummary(res.data || res);
    } catch (error) {
      console.error("Failed to fetch summary:", error);
      setSummary({
        pending_count: 0,
        processing_count: 0,
        resolved_count: 0,
        total_count: 0,
      });
    }
  };
  const handleViewDetail = async (alertId) => {
    try {
      const res = await shortageAlertApi.get(alertId);
      setSelectedAlert(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch alert detail:", error);
    }
  };
  const handleAcknowledge = async (alertId) => {
    if (!confirm("确认已收到此缺料预警？")) {return;}
    try {
      await shortageAlertApi.acknowledge(alertId);
      fetchAlerts();
      fetchSummary();
    } catch (error) {
      console.error("Failed to acknowledge alert:", error);
      const errorMessage =
        error.response?.data?.detail || error.message || "确认失败，请稍后重试";
      alert(errorMessage);
    }
  };
  const handleResolve = async () => {
    if (!selectedAlert) {return;}
    try {
      await shortageAlertApi.resolve(selectedAlert.id, handleData);
      setShowHandleDialog(false);
      setHandleData({
        solution: "",
        status: "PROCESSING",
        remark: "",
      });
      fetchAlerts();
      fetchSummary();
      if (showDetailDialog) {
        handleViewDetail(selectedAlert.id);
      }
    } catch (error) {
      console.error("Failed to resolve alert:", error);
      const errorMessage =
        error.response?.data?.detail || error.message || "处理失败，请稍后重试";
      alert(errorMessage);
    }
  };
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          alert.material_code?.toLowerCase().includes(keyword) ||
          alert.material_name?.toLowerCase().includes(keyword) ||
          alert.project_name?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [alerts, searchKeyword]);
  const isUrgent = (alert) => {
    if (!alert.required_date) {return false;}
    const daysUntilRequired = Math.ceil(
      (new Date(alert.required_date) - new Date()) / (1000 * 60 * 60 * 24),
    );
    return daysUntilRequired <= 7 && daysUntilRequired >= 0;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="缺料预警"
          description="缺料预警管理，支持确认、处理、统计分析"
        />
        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-400 mb-1">待处理</div>
                    <div className="text-2xl font-bold text-blue-400">
                      {summary.pending_count || 0}
                    </div>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-blue-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-400 mb-1">处理中</div>
                    <div className="text-2xl font-bold text-purple-400">
                      {summary.processing_count || 0}
                    </div>
                  </div>
                  <Package className="w-8 h-8 text-purple-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-400 mb-1">已解决</div>
                    <div className="text-2xl font-bold text-emerald-400">
                      {summary.resolved_count || 0}
                    </div>
                  </div>
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-400 mb-1">总缺料项</div>
                    <div className="text-2xl font-bold text-slate-200">
                      {summary.total_count || 0}
                    </div>
                  </div>
                  <BarChart3 className="w-8 h-8 text-violet-400" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        {/* Filters */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索物料编码、名称..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-slate-900/50 border-slate-700 text-slate-200"
                  icon={Search}
                />
              </div>
              <Select value={filterProject} onValueChange={setFilterProject}>
                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部项目</SelectItem>
                  {projects.map((proj) => {
                    const projId = proj.id?.toString();
                    if (!projId || projId === "") {return null;}
                    return (
                      <SelectItem key={proj.id} value={projId}>
                        {proj.project_name}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  {Object.entries(statusConfigs)
                    .filter(([key]) => key && key !== "")
                    .map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              <Select value={filterLevel} onValueChange={setFilterLevel}>
                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="选择预警级别" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部级别</SelectItem>
                  {Object.entries(levelConfigs).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
        {/* Alert List */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-slate-200">缺料预警列表</CardTitle>
            <CardDescription className="text-slate-400">
              共 {filteredAlerts.length} 个缺料预警
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredAlerts.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                暂无缺料预警
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-400">项目</TableHead>
                    <TableHead className="text-slate-400">物料编码</TableHead>
                    <TableHead className="text-slate-400">物料名称</TableHead>
                    <TableHead className="text-slate-400">需求数量</TableHead>
                    <TableHead className="text-slate-400">可用数量</TableHead>
                    <TableHead className="text-slate-400">缺料数量</TableHead>
                    <TableHead className="text-slate-400">需求日期</TableHead>
                    <TableHead className="text-slate-400">预警级别</TableHead>
                    <TableHead className="text-slate-400">状态</TableHead>
                    <TableHead className="text-right text-slate-400">
                      操作
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAlerts.map((alert) => {
                    const urgent = isUrgent(alert);
                    return (
                      <TableRow key={alert.id} className="border-slate-700">
                        <TableCell className="font-medium text-slate-200">
                          {alert.project_name || "-"}
                        </TableCell>
                        <TableCell className="font-mono text-sm text-slate-300">
                          {alert.material_code}
                        </TableCell>
                        <TableCell className="text-slate-200">
                          {alert.material_name}
                        </TableCell>
                        <TableCell className="text-slate-300">
                          {alert.required_qty || 0}
                        </TableCell>
                        <TableCell
                          className={cn(
                            "text-slate-300",
                            alert.available_qty < alert.required_qty &&
                              "text-red-400",
                          )}
                        >
                          {alert.available_qty || 0}
                        </TableCell>
                        <TableCell className="font-medium text-red-400">
                          {alert.shortage_qty || 0}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-300">
                              {alert.required_date
                                ? formatDate(alert.required_date)
                                : "-"}
                            </span>
                            {urgent && (
                              <Badge className="bg-red-500 text-xs">
                                <AlertTriangle className="w-3 h-3 mr-1" />
                                紧急
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              levelConfigs[alert.alert_level]?.color ||
                              "bg-slate-500"
                            }
                          >
                            {levelConfigs[alert.alert_level]?.label ||
                              alert.alert_level}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            className={
                              statusConfigs[alert.status]?.color ||
                              "bg-slate-500"
                            }
                          >
                            {statusConfigs[alert.status]?.label || alert.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetail(alert.id)}
                              className="text-slate-400 hover:text-slate-200"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {alert.status === "PENDING" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleAcknowledge(alert.id)}
                                className="text-slate-400 hover:text-slate-200"
                              >
                                <CheckCircle2 className="w-4 h-4" />
                              </Button>
                            )}
                            {alert.status !== "RESOLVED" &&
                              alert.status !== "CLOSED" && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setSelectedAlert(alert);
                                    setShowHandleDialog(true);
                                  }}
                                  className="text-slate-400 hover:text-slate-200"
                                >
                                  <Package className="w-4 h-4" />
                                </Button>
                              )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
        {/* Alert Detail Dialog */}
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-4xl bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">缺料预警详情</DialogTitle>
            </DialogHeader>
            <DialogBody>
              {selectedAlert && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-400 mb-1">项目</div>
                      <div className="font-medium text-slate-200">
                        {selectedAlert.project_name || "-"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">状态</div>
                      <Badge
                        className={statusConfigs[selectedAlert.status]?.color}
                      >
                        {statusConfigs[selectedAlert.status]?.label}
                      </Badge>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        物料编码
                      </div>
                      <div className="font-mono text-slate-200">
                        {selectedAlert.material_code}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        物料名称
                      </div>
                      <div className="text-slate-200">
                        {selectedAlert.material_name}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        需求数量
                      </div>
                      <div className="font-medium text-slate-200">
                        {selectedAlert.required_qty || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        可用数量
                      </div>
                      <div
                        className={cn(
                          "text-slate-200",
                          selectedAlert.available_qty <
                            selectedAlert.required_qty && "text-red-400",
                        )}
                      >
                        {selectedAlert.available_qty || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        缺料数量
                      </div>
                      <div className="font-medium text-red-400">
                        {selectedAlert.shortage_qty || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        需求日期
                      </div>
                      <div className="text-slate-200">
                        {selectedAlert.required_date
                          ? formatDate(selectedAlert.required_date)
                          : "-"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        预警级别
                      </div>
                      <Badge
                        className={
                          levelConfigs[selectedAlert.alert_level]?.color
                        }
                      >
                        {levelConfigs[selectedAlert.alert_level]?.label}
                      </Badge>
                    </div>
                    {selectedAlert.resolved_at && (
                      <div>
                        <div className="text-sm text-slate-400 mb-1">
                          解决时间
                        </div>
                        <div className="text-slate-200">
                          {formatDate(selectedAlert.resolved_at)}
                        </div>
                      </div>
                    )}
                  </div>
                  {selectedAlert.solution && (
                    <div>
                      <div className="text-sm text-slate-400 mb-1">
                        解决方案
                      </div>
                      <div className="text-slate-200">
                        {selectedAlert.solution}
                      </div>
                    </div>
                  )}
                  {selectedAlert.remark && (
                    <div>
                      <div className="text-sm text-slate-400 mb-1">备注</div>
                      <div className="text-slate-200">
                        {selectedAlert.remark}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </DialogBody>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowDetailDialog(false)}
              >
                关闭
              </Button>
              {selectedAlert && selectedAlert.status === "PENDING" && (
                <Button onClick={() => handleAcknowledge(selectedAlert.id)}>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  确认预警
                </Button>
              )}
              {selectedAlert &&
                selectedAlert.status !== "RESOLVED" &&
                selectedAlert.status !== "CLOSED" && (
                  <Button
                    onClick={() => {
                      setShowDetailDialog(false);
                      setShowHandleDialog(true);
                    }}
                  >
                    <Package className="w-4 h-4 mr-2" />
                    处理预警
                  </Button>
                )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
        {/* Handle Alert Dialog */}
        <Dialog open={showHandleDialog} onOpenChange={setShowHandleDialog}>
          <DialogContent className="bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">处理缺料预警</DialogTitle>
            </DialogHeader>
            <DialogBody>
              {selectedAlert && (
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-slate-400 mb-1">物料</div>
                    <div className="font-medium text-slate-200">
                      {selectedAlert.material_name}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">缺料数量</div>
                    <div className="font-medium text-red-400">
                      {selectedAlert.shortage_qty || 0}
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block text-slate-400">
                      处理状态
                    </label>
                    <Select
                      value={handleData.status}
                      onValueChange={(val) =>
                        setHandleData({ ...handleData, status: val })
                      }
                    >
                      <SelectTrigger className="bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PROCESSING">处理中</SelectItem>
                        <SelectItem value="RESOLVED">已解决</SelectItem>
                        <SelectItem value="CLOSED">已关闭</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block text-slate-400">
                      解决方案
                    </label>
                    <textarea
                      className="w-full min-h-[100px] p-3 border border-slate-700 rounded-lg bg-slate-800 text-slate-200 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={handleData.solution}
                      onChange={(e) =>
                        setHandleData({
                          ...handleData,
                          solution: e.target.value,
                        })
                      }
                      placeholder="填写解决方案..."
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block text-slate-400">
                      备注
                    </label>
                    <Input
                      value={handleData.remark}
                      onChange={(e) =>
                        setHandleData({ ...handleData, remark: e.target.value })
                      }
                      placeholder="备注信息"
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                </div>
              )}
            </DialogBody>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowHandleDialog(false)}
              >
                取消
              </Button>
              <Button onClick={handleResolve}>保存</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
