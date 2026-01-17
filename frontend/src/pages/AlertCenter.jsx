/**
 * Alert Center Management (重构版)
 * 预警中心 - 统一预警管理平台
 *
 * 功能：
 * 1. 预警创建、编辑、查看
 * 2. 预警级别和状态管理
 * 3. 预警规则配置和触发条件
 * 4. 多渠道通知设置
 * 5. SLA监控和分析
 * 6. 预警批量处理和导出
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  Search,
  Eye,
  Settings,
  Bell,
  TrendingUp,
  TrendingDown,
  Calendar,
  User,
  FileText,
  RefreshCw,
  Download,
  CheckSquare,
  Square,
  ArrowUpDown,
  Filter } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { LoadingCard, ErrorMessage, EmptyState } from "../components/common";
import { toast } from "../components/ui/toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
  DialogDescription } from
"../components/ui/dialog";
import { cn as _cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { alertApi, projectApi } from "../services/api";

// 导入重构后的组件
import {
  AlertCenterOverview,
  ALERT_LEVELS,
  ALERT_STATUS,
  ALERT_TYPES,
  ALERT_ACTIONS,
  getAlertLevelConfig,
  getAlertStatusConfig,
  getAlertTypeConfig,
  getAvailableActions,
  calculateResponseTime as _calculateResponseTime,
  calculateResolutionTime as _calculateResolutionTime,
  checkResponseTimeSLA as _checkResponseTimeSLA,
  requiresEscalation as _requiresEscalation,
  getAlertSummary as _getAlertSummary } from
"../components/alert-center";

export default function AlertCenter() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    resolved: 0,
    critical: 0,
    today_new: 0,
    urgent: 0,
    warning: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [selectedProject, setSelectedProject] = useState("ALL");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [showDetail, setShowDetail] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showResolveDialog, setShowResolveDialog] = useState(false);
  const [showCloseDialog, setShowCloseDialog] = useState(false);
  const [resolveResult, setResolveResult] = useState("");
  const [_closeReason, setCloseReason] = useState("");
  const [selectedAlerts, setSelectedAlerts] = useState(new Set());
  const [sortBy, setSortBy] = useState("triggered_at");
  const [sortOrder, _setSortOrder] = useState("desc");
  const [projects, setProjects] = useState([]);

  // 加载项目列表
  const loadProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({ page: 1, page_size: 1000 });
      const data = response.data || response;
      const projectList = data.items || data || [];

      // 转换为组件所需格式
      const transformedProjects = projectList.map((project) => ({
        id: project.id || project.project_code,
        name: project.project_name || ""
      }));

      setProjects(transformedProjects);
    } catch (error) {
      console.error("Failed to load projects:", error);
      const mockProjects = [
      { id: 1, name: "测试项目A" },
      { id: 2, name: "测试项目B" },
      { id: 3, name: "测试项目C" }];

      setProjects(mockProjects);
    }
  }, []);

  // 加载预警数据
  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        page_size: pageSize
      };

      if (selectedLevel !== "ALL") {
        params.alert_level = selectedLevel;
      }
      if (selectedStatus !== "ALL") {
        params.status = selectedStatus === "ACTIVE" ? "PENDING" : selectedStatus;
      }
      if (selectedProject !== "ALL") {
        params.project_id = parseInt(selectedProject);
      }
      if (dateRange.start) {
        params.date_from = dateRange.start;
      }
      if (dateRange.end) {
        params.date_to = dateRange.end;
      }
      if (searchQuery) {
        params.keyword = searchQuery;
      }

      params.ordering = sortOrder === "desc" ? `-${sortBy}` : sortBy;

      const response = await alertApi.list(params);
      const data = response.data?.data || response.data || response;

      setAlerts(data.items || data || []);
      setTotal(data.total || data.length || 0);
    } catch (error) {
      console.error("Failed to load alerts:", error);
      setError(error.response?.data?.detail || error.message || "加载预警失败");
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, selectedLevel, selectedStatus, selectedProject, dateRange, searchQuery, sortBy, sortOrder]);

  // 加载统计数据
  const loadStatistics = useCallback(async () => {
    try {
      const response = await alertApi.statistics();
      const data = response.data?.data || response.data || {};

      setStats({
        total: data.total || 0,
        pending: data.pending || 0,
        resolved: data.resolved || 0,
        critical: data.critical || 0,
        today_new: data.today_new || 0,
        urgent: data.urgent || 0,
        warning: data.warning || 0
      });
    } catch (error) {
      console.error("Failed to load statistics:", error);
    }
  }, []);

  // 初始化加载
  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    loadAlerts();
    loadStatistics();
  }, [loadAlerts, loadStatistics]);

  // 批量确认预警
  const handleBatchAcknowledge = useCallback(async () => {
    if (selectedAlerts.size === 0) return;

    try {
      const promises = Array.from(selectedAlerts).map((id) =>
      alertApi.acknowledge(id)
      );
      await Promise.all(promises);
      await loadAlerts();
      await loadStatistics();
      const count = selectedAlerts.size;
      setSelectedAlerts(new Set());
      toast.success(`已批量确认 ${count} 条预警`);
    } catch (error) {
      console.error("Failed to batch acknowledge:", error);
      toast.error("批量确认失败，请稍后重试");
    }
  }, [selectedAlerts, loadAlerts, loadStatistics]);

  // 批量解决预警
  const handleBatchResolve = useCallback(async () => {
    if (selectedAlerts.size === 0) return;

    try {
      const promises = Array.from(selectedAlerts).map((id) =>
      alertApi.resolve(id, { resolution_method: "批量解决", resolution_note: "批量操作" })
      );
      await Promise.all(promises);
      await loadAlerts();
      await loadStatistics();
      const count = selectedAlerts.size;
      setSelectedAlerts(new Set());
      toast.success(`已批量解决 ${count} 条预警`);
    } catch (error) {
      console.error("Failed to batch resolve:", error);
      toast.error("批量解决失败，请稍后重试");
    }
  }, [selectedAlerts, loadAlerts, loadStatistics]);

  // 导出Excel
  const handleExportExcel = useCallback(async () => {
    try {
      const params = {
        project_id: selectedProject !== "ALL" ? parseInt(selectedProject) : undefined,
        alert_level: selectedLevel !== "ALL" ? selectedLevel : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        start_date: dateRange.start || undefined,
        end_date: dateRange.end || undefined
      };

      const response = await alertApi.exportExcel(params);
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `预警报表_${new Date().toISOString().split("T")[0]}.xlsx`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Excel导出成功");
    } catch (error) {
      console.error("Failed to export Excel:", error);
      toast.error("导出失败，请稍后重试");
    }
  }, [selectedProject, selectedLevel, selectedStatus, dateRange]);

  // 导出PDF
  const handleExportPdf = useCallback(async () => {
    try {
      const params = {
        project_id: selectedProject !== "ALL" ? parseInt(selectedProject) : undefined,
        alert_level: selectedLevel !== "ALL" ? selectedLevel : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        start_date: dateRange.start || undefined,
        end_date: dateRange.end || undefined
      };

      const response = await alertApi.exportPdf(params);
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `预警报表_${new Date().toISOString().split("T")[0]}.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("PDF导出成功");
    } catch (error) {
      console.error("Failed to export PDF:", error);
      toast.error("导出失败，请稍后重试");
    }
  }, [selectedProject, selectedLevel, selectedStatus, dateRange]);

  // 查看详情
  const handleViewDetail = useCallback((alert) => {
    setSelectedAlert(alert);
    setShowDetail(true);
  }, []);

  // 单个确认
  const handleAcknowledge = useCallback(async (alertId) => {
    try {
      await alertApi.acknowledge(alertId);
      await loadAlerts();
      await loadStatistics();
      toast.success("预警确认成功");
    } catch (error) {
      console.error("Failed to acknowledge:", error);
      toast.error("确认失败，请稍后重试");
    }
  }, [loadAlerts, loadStatistics]);

  // 解决预警
  const handleResolve = useCallback(async (alertId, result) => {
    try {
      await alertApi.resolve(alertId, {
        resolution_method: "手动解决",
        resolution_note: result
      });
      setShowResolveDialog(false);
      setResolveResult("");
      await loadAlerts();
      await loadStatistics();
      toast.success("预警解决成功");
    } catch (error) {
      console.error("Failed to resolve:", error);
      toast.error("解决失败，请稍后重试");
    }
  }, [loadAlerts, loadStatistics]);

  // 关闭预警
  const _handleClose = useCallback(async (alertId, reason) => {
    try {
      await alertApi.close(alertId, {
        closure_reason: reason
      });
      setShowCloseDialog(false);
      setCloseReason("");
      await loadAlerts();
      await loadStatistics();
      toast.success("预警关闭成功");
    } catch (error) {
      console.error("Failed to close:", error);
      toast.error("关闭失败，请稍后重试");
    }
  }, [loadAlerts, loadStatistics]);

  // 筛选和搜索
  const filteredAlerts = useMemo(() => {
    // API已经处理了筛选，这里只处理前端排序
    const sorted = [...alerts].sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (sortBy === "triggered_at" && aValue) {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      if (sortOrder === "desc") {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      } else {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      }
    });

    return sorted;
  }, [alerts, sortBy, sortOrder]);

  // 处理复选框选择
  const handleSelectAll = useCallback(() => {
    if (selectedAlerts.size === filteredAlerts.length) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(new Set(filteredAlerts.map((alert) => alert.id)));
    }
  }, [filteredAlerts, selectedAlerts.size]);

  const handleSelectOne = useCallback((alertId, selected) => {
    const newSelected = new Set(selectedAlerts);
    if (selected) {
      newSelected.add(alertId);
    } else {
      newSelected.delete(alertId);
    }
    setSelectedAlerts(newSelected);
  }, [selectedAlerts]);

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (
      (e.ctrlKey || e.metaKey) &&
      e.key === "a" &&
      e.target.tagName !== "INPUT" &&
      e.target.tagName !== "TEXTAREA")
      {
        e.preventDefault();
        handleSelectAll();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
  showDetail,
  showResolveDialog,
  showCloseDialog,
  filteredAlerts,
  handleSelectAll]
  );

  // 快速操作处理
  const handleQuickAction = useCallback((action) => {
    switch (action) {
      case 'createAlert':
        // 跳转到创建预警页面
        navigate('/alerts/create');
        break;
      case 'manageRules':
        // 跳转到规则管理页面
        navigate('/alerts/rules');
        break;
      case 'notificationSettings':
        // 跳转到通知设置页面
        navigate('/alerts/notifications');
        break;
      case 'exportReport':
        // 触发导出
        handleExportExcel();
        break;
    }
  }, [navigate, handleExportExcel]);

  if (loading && alerts.length === 0) {
    return (
      <LoadingCard message="加载预警数据中..." />);

  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={loadAlerts} />);


  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <PageHeader
        title="预警中心"
        subtitle="统一预警管理平台 - 实时监控、智能分析、快速响应"
        breadcrumbs={[
        { label: "系统管理", href: "/system" },
        { label: "预警中心" }]
        }
        actions={[
        {
          label: "新建规则",
          icon: Settings,
          onClick: () => navigate('/alerts/rules/create'),
          variant: "default"
        }]
        } />


      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 预警概览 */}
        <AlertCenterOverview
          alerts={alerts}
          stats={stats}
          onQuickAction={handleQuickAction} />


        {/* 筛选和搜索 */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索预警标题、描述、项目..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700" />

                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <select
                    value={selectedLevel}
                    onChange={(e) => setSelectedLevel(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                    <option value="ALL">全部级别</option>
                    {Object.entries(ALERT_LEVELS).map(([key, config]) =>
                    <option key={key} value={key}>
                        {config.label}
                      </option>
                    )}
                  </select>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                    <option value="ALL">全部状态</option>
                    {Object.entries(ALERT_STATUS).map(([key, config]) =>
                    <option key={key} value={key}>
                        {config.label}
                      </option>
                    )}
                  </select>
                  <select
                    value={selectedProject}
                    onChange={(e) => setSelectedProject(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white">

                    <option value="ALL">全部项目</option>
                    {projects.map((project) =>
                    <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    )}
                  </select>
                  <Input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange((prev) => ({ ...prev, start: e.target.value }))}
                    className="w-40"
                    placeholder="开始日期" />

                  <Input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange((prev) => ({ ...prev, end: e.target.value }))}
                    className="w-40"
                    placeholder="结束日期" />

                  <Button
                    variant="outline"
                    onClick={() => setSortBy((prev) => prev === sortBy ? 'triggered_at' : prev)}>

                    <ArrowUpDown className="h-4 w-4 mr-2" />
                    {sortBy === 'triggered_at' ? '默认排序' : '按时间排序'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 预警列表 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible">

          {filteredAlerts.length === 0 ?
          <Card>
              <CardContent className="p-8">
                <EmptyState
                icon={AlertTriangle}
                title="暂无预警"
                description={searchQuery || selectedLevel !== "ALL" || selectedStatus !== "ALL" ? "没有找到匹配的预警" : "系统运行正常，暂无预警"}
                action={
                <Button
                  onClick={() => navigate('/alerts/create')}
                  className="mt-4">

                      <AlertTriangle className="h-4 w-4 mr-2" />
                      创建测试预警
                    </Button>
                } />

              </CardContent>
            </Card> :

          <>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">预警列表</h3>
                    <div className="flex items-center gap-2">
                      {selectedAlerts.size > 0 &&
                    <>
                          <Button
                        size="sm"
                        onClick={handleBatchAcknowledge}
                        className="bg-blue-500 hover:bg-blue-600">

                            批量确认 ({selectedAlerts.size})
                          </Button>
                          <Button
                        size="sm"
                        onClick={handleBatchResolve}
                        className="bg-emerald-500 hover:bg-emerald-600">

                            批量解决 ({selectedAlerts.size})
                          </Button>
                        </>
                    }
                      <Button
                      size="sm"
                      onClick={() =>
                      setSelectedAlerts(
                        new Set(filteredAlerts.map((alert) => alert.id))
                      )
                      }
                      variant="outline">

                        {selectedAlerts.size === filteredAlerts.length ?
                      "取消全选" :
                      "全选"}
                      </Button>
                      <div className="flex gap-1">
                        <Button
                        size="sm"
                        onClick={handleExportExcel}
                        variant="outline">

                          <Download className="h-4 w-4 mr-2" />
                          Excel
                        </Button>
                        <Button
                        size="sm"
                        onClick={handleExportPdf}
                        variant="outline">

                          <Download className="h-4 w-4 mr-2" />
                          PDF
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 预警列表内容 */}
              <div className="space-y-4">
              {filteredAlerts.map((alert, index) => {
                const levelConfig = getAlertLevelConfig(alert.alert_level);
                const statusConfig = getAlertStatusConfig(alert.status);
                const typeConfig = getAlertTypeConfig(alert.alert_type);
                const availableActions = getAvailableActions(alert);

                return (
                  <motion.div
                    key={alert.id}
                    variants={fadeIn}
                    custom={index}>

                    <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/70 transition-colors">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 flex-1">
                            <input
                              type="checkbox"
                              checked={selectedAlerts.has(alert.id)}
                              onChange={(e) => handleSelectOne(alert.id, e.target.checked)}
                              className="mt-1" />

                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-3 mb-2">
                                <div className={`w-3 h-3 rounded-full ${levelConfig.color}`} />
                                <h4 className="text-lg font-semibold text-white">
                                  {alert.title || '未命名预警'}
                                </h4>
                                <Badge className={levelConfig.color}>
                                  {levelConfig.label}
                                </Badge>
                                <Badge className={statusConfig.color} variant="outline">
                                  {statusConfig.label}
                                </Badge>
                              </div>
                              
                              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-3 text-sm">
                                <div>
                                  <span className="text-slate-400">类型:</span>
                                  <span className="text-white">{typeConfig.label}</span>
                                </div>
                                <div>
                                  <span className="text-slate-400">项目:</span>
                                  <span className="text-white">{alert.project_name || '未分配'}</span>
                                </div>
                                <div>
                                  <span className="text-slate-400">触发时间:</span>
                                  <span className="text-white">
                                    {alert.triggered_at ? new Date(alert.triggered_at).toLocaleString() : '-'}
                                  </span>
                                </div>
                              </div>

                              {alert.description &&
                              <div className="mb-3">
                                  <p className="text-sm text-slate-300 mb-1">描述:</p>
                                  <p className="text-sm text-white line-clamp-2">
                                    {alert.description}
                                  </p>
                                </div>
                              }

                              <div className="flex flex-wrap gap-2">
                                {availableActions.includes('确认') &&
                                <Button
                                  size="sm"
                                  onClick={() => handleAcknowledge(alert.id)}
                                  className="bg-blue-500 hover:bg-blue-600">

                                    确认
                                  </Button>
                                }
                                {availableActions.includes('解决') &&
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    setSelectedAlert(alert);
                                    setShowResolveDialog(true);
                                  }}
                                  className="bg-emerald-500 hover:bg-emerald-600">

                                    解决
                                  </Button>
                                }
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleViewDetail(alert)}>

                                  <Eye className="h-4 w-4 mr-2" />
                                  详情
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>);

              })}
              </div>
            </>
          }

          {/* 分页 */}
          {total > pageSize &&
          <div className="flex justify-center items-center gap-2 mt-6">
              <Button
              variant="outline"
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page <= 1}>

                上一页
              </Button>
              <span className="text-sm text-slate-400">
                第 {page} 页，共 {Math.ceil(total / pageSize)} 页
              </span>
              <Button
              variant="outline"
              onClick={() => setPage((prev) => prev + 1)}
              disabled={page >= Math.ceil(total / pageSize)}>

                下一页
              </Button>
            </div>
          }
        </motion.div>

        {/* 解决预警对话框 */}
        <Dialog open={showResolveDialog} onOpenChange={setShowResolveDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>解决预警</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {selectedAlert &&
              <div className="text-sm text-slate-300">
                  <p><strong>预警:</strong> {selectedAlert.title}</p>
                  <p><strong>级别:</strong> {getAlertLevelConfig(selectedAlert.alert_level).label}</p>
                </div>
              }
              <div>
                <label className="text-sm font-medium text-slate-300">解决方案</label>
                <textarea
                  value={resolveResult}
                  onChange={(e) => setResolveResult(e.target.value)}
                  className="w-full mt-1 p-2 bg-slate-800 border border-slate-700 rounded text-white"
                  rows={3}
                  placeholder="请输入解决方案..." />

              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowResolveDialog(false)}>

                取消
              </Button>
              <Button
                onClick={() => handleResolve(selectedAlert.id, resolveResult)}
                className="bg-emerald-500 hover:bg-emerald-600">

                确认解决
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* 预警详情对话框 */}
        <Dialog open={showDetail} onOpenChange={setShowDetail}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>预警详情</DialogTitle>
            </DialogHeader>
            {selectedAlert &&
            <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">基本信息</h3>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm text-slate-400">预警编号:</span>
                        <p className="text-white">{selectedAlert.alert_no || '-'}</p>
                      </div>
                      <div>
                        <span className="text-sm text-slate-400">预警级别:</span>
                        <p className="text-white">
                          {getAlertLevelConfig(selectedAlert.alert_level).label}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-slate-400">预警类型:</span>
                        <p className="text-white">
                          {getAlertTypeConfig(selectedAlert.alert_type).label}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm text-slate-400">当前状态:</span>
                        <p className="text-white">
                          {getAlertStatusConfig(selectedAlert.status).label}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">时间信息</h3>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm text-slate-400">触发时间:</span>
                        <p className="text-white">
                          {selectedAlert.triggered_at ? new Date(selectedAlert.triggered_at).toLocaleString() : '-'}
                        </p>
                      </div>
                      {selectedAlert.first_action_time &&
                    <div>
                          <span className="text-sm text-slate-400">首次响应:</span>
                          <p className="text-white">
                            {new Date(selectedAlert.first_action_time).toLocaleString()}
                          </p>
                        </div>
                    }
                      {selectedAlert.resolved_time &&
                    <div>
                          <span className="text-sm text-slate-400">解决时间:</span>
                          <p className="text-white">
                            {new Date(selectedAlert.resolved_time).toLocaleString()}
                          </p>
                        </div>
                    }
                    </div>
                  </div>
                </div>

                {selectedAlert.description &&
              <div>
                    <h3 className="text-lg font-semibold text-white mb-4">详细描述</h3>
                    <p className="text-slate-300">{selectedAlert.description}</p>
                  </div>
              }

                {selectedAlert.trigger_data &&
              <div>
                    <h3 className="text-lg font-semibold text-white mb-4">触发数据</h3>
                    <pre className="bg-slate-800 p-4 rounded text-sm text-slate-300 overflow-auto">
                      {JSON.stringify(selectedAlert.trigger_data, null, 2)}
                    </pre>
                  </div>
              }
              </div>
            }
            <DialogFooter>
              <Button
                onClick={() => setShowDetail(false)}
                className="w-full">

                关闭
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>);

}