/**
 * Worker Workstation Page - 工人工作台页面 (重构版)
 * Features: 我的工单、报工提交（开工/进度/完工）、我的报工记录
 */
import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Wrench,
  Clock,
  CheckCircle2,
  PlayCircle,
  PauseCircle,
  TrendingUp,
  FileText,
  User,
  Calendar,
  Package,
  AlertTriangle,
  RefreshCw,
  Plus,
  Camera,
  QrCode,
  Scan,
  X,
  Calculator,
  Zap,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown } from
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
import { Progress } from "../components/ui/progress";
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import { cn as _cn, formatDate } from "../lib/utils";
import { productionApi } from "../services/api";
import { toast } from "../components/ui/toast";

// 导入重构后的组件
import {
  WorkerWorkOverview,
  WORK_ORDER_STATUS,
  REPORT_TYPE,
  SKILL_LEVELS,
  WORK_ORDER_TYPES,
  QUICK_QUANTITY_OPTIONS,
  calculateProgress,
  calculateWorkHours,
  getStatusColor as _getStatusColor,
  getReportTypeColor as _getReportTypeColor,
  validateReportData,
  getQualityLevel as _getQualityLevel,
  getNextAvailableActions,
  formatWorkHours } from
"../components/worker-workstation";

export default function WorkerWorkstation() {
  const _navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [myWorkOrders, setMyWorkOrders] = useState([]);
  const [myReports, setMyReports] = useState([]);
  const [workerId, setWorkerId] = useState(null);
  const [_error, setError] = useState(null);

  // 对话框状态
  const [showStartDialog, setShowStartDialog] = useState(false);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  // 报工数据状态
  const [startData, setStartData] = useState({
    start_note: "",
    equipment_check: true,
    material_check: true
  });

  const [progressData, setProgressData] = useState({
    progress_percent: 0,
    progress_note: "",
    current_issues: ""
  });

  const [completeData, setCompleteData] = useState({
    completed_qty: 0,
    qualified_qty: 0,
    defect_qty: 0,
    work_hours: 0,
    report_note: ""
  });

  // 照片状态
  const [photos, setPhotos] = useState([]);
  const fileInputRef = useRef(null);

  // 筛选和排序状态
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState("created_time");
  const [sortDirection, setSortDirection] = useState("desc");

  // 加载工人信息
  useEffect(() => {
    const loadWorker = async () => {
      try {
        const res = await productionApi.workers.list({ page_size: 1000 });
        const workers = res.data.results || [];
        // 这里假设当前登录用户是工人，实际应该从认证信息获取
        if (workers.length > 0) {
          setWorkerId(workers[0].id);
        }
      } catch (error) {
        console.error("Failed to load worker info:", error);
        setError("加载工人信息失败");
      }
    };
    loadWorker();
  }, []);

  // 加载我的工单
  const fetchMyWorkOrders = useCallback(async () => {
    if (!workerId) {return;}

    try {
      setLoading(true);
      const res = await productionApi.workOrders.list({
        assigned_to: workerId,
        ordering: `${sortDirection === "desc" ? "-" : ""}${sortField}`
      });
      setMyWorkOrders(res.data.results || []);
    } catch (error) {
      console.error("Failed to fetch work orders:", error);
      toast.error("获取工单失败");
    } finally {
      setLoading(false);
    }
  }, [workerId, sortField, sortDirection]);

  // 加载我的报工记录
  const fetchMyReports = useCallback(async () => {
    if (!workerId) {return;}

    try {
      const res = await productionApi.workReports.my({
        worker_id: workerId,
        ordering: "-created_time"
      });
      setMyReports(res.data.results || []);
    } catch (error) {
      console.error("Failed to fetch work reports:", error);
      toast.error("获取报工记录失败");
    }
  }, [workerId]);

  // 初始化加载
  useEffect(() => {
    if (workerId) {
      fetchMyWorkOrders();
      fetchMyReports();
    }
  }, [workerId, fetchMyWorkOrders, fetchMyReports]);

  // 开工报工
  const handleStartWork = async () => {
    if (!selectedOrder || submitting) {return;}

    const errors = validateReportData('START', startData, selectedOrder);
    if (errors.length > 0) {
      errors.forEach((error) => toast.error(error));
      return;
    }

    try {
      setSubmitting(true);
      await productionApi.workReports.start({
        work_order_id: selectedOrder.id,
        start_note: startData.start_note,
        equipment_check: startData.equipment_check,
        material_check: startData.material_check
      });

      setShowStartDialog(false);
      setStartData({
        start_note: "",
        equipment_check: true,
        material_check: true
      });

      await fetchMyWorkOrders();
      await fetchMyReports();
      toast.success("开工报工成功");
    } catch (error) {
      console.error("Failed to start work:", error);
      toast.error("开工报工失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  // 进度报工
  const handleProgressReport = async () => {
    if (!selectedOrder || submitting) {return;}

    const errors = validateReportData('PROGRESS', progressData, selectedOrder);
    if (errors.length > 0) {
      errors.forEach((error) => toast.error(error));
      return;
    }

    try {
      setSubmitting(true);
      await productionApi.workReports.progress({
        work_order_id: selectedOrder.id,
        progress_percent: progressData.progress_percent,
        progress_note: progressData.progress_note,
        current_issues: progressData.current_issues
      });

      setShowProgressDialog(false);
      setProgressData({
        progress_percent: 0,
        progress_note: "",
        current_issues: ""
      });

      await fetchMyWorkOrders();
      await fetchMyReports();
      toast.success("进度报工成功");
    } catch (error) {
      console.error("Failed to report progress:", error);
      toast.error("进度报工失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  // 完工报工
  const handleCompleteWork = async () => {
    if (!selectedOrder || submitting) {return;}

    const errors = validateReportData('COMPLETE', completeData, selectedOrder);
    if (errors.length > 0) {
      errors.forEach((error) => toast.error(error));
      return;
    }

    // 自动计算不良数量
    const defectQty = completeData.completed_qty - completeData.qualified_qty;

    // 自动计算工时（如果未填写）
    let workHours = completeData.work_hours;
    if (!workHours && selectedOrder.actual_start_time) {
      workHours = calculateWorkHours(selectedOrder.actual_start_time);
    }

    try {
      setSubmitting(true);
      await productionApi.workReports.complete({
        work_order_id: selectedOrder.id,
        completed_qty: completeData.completed_qty,
        qualified_qty: completeData.qualified_qty,
        defect_qty: defectQty,
        work_hours: workHours,
        report_note: completeData.report_note || ""
      });

      setShowCompleteDialog(false);
      setCompleteData({
        completed_qty: 0,
        qualified_qty: 0,
        defect_qty: 0,
        work_hours: 0,
        report_note: ""
      });
      setPhotos([]);

      await fetchMyWorkOrders();
      await fetchMyReports();
      toast.success("完工报工成功");
    } catch (error) {
      console.error("Failed to complete work:", error);
      toast.error("完工报工失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  // 快捷数量选择
  const handleQuickQuantity = (type, value) => {
    if (!selectedOrder) {return;}
    const planQty = selectedOrder.plan_qty || 0;

    if (type === "completed") {
      const qty = value === "all" ? planQty : value;
      const progress = calculateProgress(qty, planQty);
      setCompleteData((prev) => ({
        ...prev,
        completed_qty: qty,
        qualified_qty: qty, // 默认全部合格
        defect_qty: 0
      }));
      // 同时更新进度
      setProgressData((prev) => ({
        ...prev,
        progress_percent: progress
      }));
    } else if (type === "qualified") {
      setCompleteData((prev) => ({
        ...prev,
        qualified_qty: value === "all" ? prev.completed_qty : value,
        defect_qty:
        prev.completed_qty - (value === "all" ? prev.completed_qty : value)
      }));
    }
  };

  // 照片处理
  const handlePhotoUpload = (e) => {
    const files = Array.from(e.target.files);
    const newPhotos = files.map((file) => ({
      file,
      url: URL.createObjectURL(file),
      name: file.name
    }));
    setPhotos((prev) => [...prev, ...newPhotos]);
  };

  const removePhoto = (index) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
  };

  // 排序处理
  const _handleSort = (field) => {
    if (sortField === field) {
      setSortDirection((prev) => prev === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // 筛选和排序工单
  const filteredWorkOrders = useMemo(() => {
    let filtered = myWorkOrders;

    // 状态筛选
    if (filterStatus !== "all") {
      filtered = filtered.filter((order) => order.status === filterStatus);
    }

    // 搜索筛选
    if (searchTerm) {
      filtered = filtered.filter((order) =>
      order.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.product_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.project_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return filtered;
  }, [myWorkOrders, filterStatus, searchTerm]);

  // 快速操作处理
  const handleQuickAction = (action) => {
    const order = myWorkOrders.find((o) => o.id === action.orderId);
    if (!order) {return;}

    setSelectedOrder(order);

    switch (action.type) {
      case 'START':
        setShowStartDialog(true);
        break;
      case 'PROGRESS':
        setProgressData((prev) => ({
          ...prev,
          progress_percent: calculateProgress(order.completed_qty || 0, order.plan_qty || 0)
        }));
        setShowProgressDialog(true);
        break;
      case 'COMPLETE':
        setCompleteData((prev) => ({
          ...prev,
          completed_qty: order.plan_qty || 0,
          qualified_qty: order.plan_qty || 0
        }));
        setShowCompleteDialog(true);
        break;
    }
  };

  // 计算工人当前绩效（模拟数据）
  const currentPerformance = useMemo(() => {
    const todayReports = myReports.filter((report) => {
      const reportDate = new Date(report.created_time);
      const today = new Date();
      return reportDate.toDateString() === today.toDateString();
    });

    const completedReports = todayReports.filter((r) => r.report_type === 'COMPLETE');
    const totalCompleted = completedReports.reduce((sum, r) => sum + (r.completed_qty || 0), 0);
    const totalQualified = completedReports.reduce((sum, r) => sum + (r.qualified_qty || 0), 0);
    const totalHours = todayReports.reduce((sum, r) => sum + (r.work_hours || 0), 0);

    return {
      efficiency: totalHours > 0 ? Math.min(8 / totalHours, 1.2) : 0,
      quality: totalCompleted > 0 ? totalQualified / totalCompleted : 0,
      timeliness: myWorkOrders.filter((o) => o.status === 'COMPLETED').length / Math.max(myWorkOrders.length, 1),
      attendance: 1, // 假设全勤
      skill_improvement: 0.8 // 模拟值
    };
  }, [myReports, myWorkOrders]);

  // 模拟工人数据（实际应该从API获取）
  const workerData = {
    id: workerId,
    name: "当前工人",
    skill_level: "SENIOR"
  };

  if (loading && myWorkOrders.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">加载中...</span>
      </div>);

  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="工人工作站"
        subtitle="管理工单和报工记录"
        breadcrumbs={[
        { label: "生产管理", href: "/production" },
        { label: "工人工作站" }]
        } />


      {/* 工作概览 */}
      <WorkerWorkOverview
        worker={workerData}
        workOrders={myWorkOrders}
        reports={myReports}
        performance={currentPerformance}
        onQuickAction={handleQuickAction} />


      {/* 主要功能标签页 */}
      <Tabs defaultValue="orders" className="space-y-4">
        <TabsList>
          <TabsTrigger value="orders">我的工单</TabsTrigger>
          <TabsTrigger value="reports">我的报工记录</TabsTrigger>
        </TabsList>

        {/* 我的工单 */}
        <TabsContent value="orders" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Wrench className="h-5 w-5" />
                  我的工单
                </span>
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="搜索工单..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-64" />

                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      {Object.entries(WORK_ORDER_STATUS).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>工单号</TableHead>
                    <TableHead>产品名称</TableHead>
                    <TableHead>项目</TableHead>
                    <TableHead>计划数量</TableHead>
                    <TableHead>完成数量</TableHead>
                    <TableHead>进度</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredWorkOrders.map((order) => {
                    const progress = calculateProgress(order.completed_qty || 0, order.plan_qty || 0);
                    const statusConfig = WORK_ORDER_STATUS[order.status] || WORK_ORDER_STATUS.PENDING;
                    const availableActions = getNextAvailableActions(order);

                    return (
                      <TableRow key={order.id}>
                        <TableCell className="font-medium">
                          {order.order_number}
                        </TableCell>
                        <TableCell>{order.product_name}</TableCell>
                        <TableCell>{order.project_name}</TableCell>
                        <TableCell>{order.plan_qty || 0}</TableCell>
                        <TableCell>{order.completed_qty || 0}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={progress} className="w-16 h-2" />
                            <span className="text-sm">{progress}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={statusConfig.color}>
                            {statusConfig.label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            {availableActions.map((action, index) =>
                            <Button
                              key={index}
                              size="sm"
                              variant="outline"
                              className={`${action.color} text-white hover:opacity-90`}
                              onClick={() => handleQuickAction(action)}>

                                <action.icon className="h-4 w-4" />
                            </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>);

                  })}
                </TableBody>
              </Table>
              {filteredWorkOrders.length === 0 &&
              <div className="text-center py-8 text-gray-500">
                  暂无工单数据
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 我的报工记录 */}
        <TabsContent value="reports" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                我的报工记录
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>报工时间</TableHead>
                    <TableHead>工单号</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>内容</TableHead>
                    <TableHead>工时</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {myReports.map((report) => {
                    const typeConfig = REPORT_TYPE[report.report_type] || REPORT_TYPE.START;

                    return (
                      <TableRow key={report.id}>
                        <TableCell>
                          {formatDate(report.created_time)}
                        </TableCell>
                        <TableCell>{report.work_order_number}</TableCell>
                        <TableCell>
                          <Badge className={typeConfig.color}>
                            {typeConfig.label}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="max-w-xs truncate">
                            {report.start_note || report.progress_note || report.report_note || "-"}
                          </div>
                        </TableCell>
                        <TableCell>{formatWorkHours(report.work_hours)}</TableCell>
                      </TableRow>);

                  })}
                </TableBody>
              </Table>
              {myReports.length === 0 &&
              <div className="text-center py-8 text-gray-500">
                  暂无报工记录
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 开工报工对话框 */}
      <Dialog open={showStartDialog} onOpenChange={setShowStartDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>开工报工</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {selectedOrder &&
            <div className="text-sm text-gray-600">
                工单号：{selectedOrder.order_number}
            </div>
            }
            <div>
              <label className="text-sm font-medium">开工说明</label>
              <textarea
                className="w-full mt-1 p-2 border rounded-md"
                rows={3}
                value={startData.start_note}
                onChange={(e) => setStartData((prev) => ({ ...prev, start_note: e.target.value }))}
                placeholder="请输入开工说明..." />

            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={startData.equipment_check}
                  onChange={(e) => setStartData((prev) => ({ ...prev, equipment_check: e.target.checked }))} />

                <span className="text-sm">设备检查完成</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={startData.material_check}
                  onChange={(e) => setStartData((prev) => ({ ...prev, material_check: e.target.checked }))} />

                <span className="text-sm">物料检查完成</span>
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowStartDialog(false)}>

              取消
            </Button>
            <Button
              className="bg-blue-500 hover:bg-blue-600"
              onClick={handleStartWork}
              disabled={submitting}>

              {submitting ? "提交中..." : "确认开工"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 进度报工对话框 */}
      <Dialog open={showProgressDialog} onOpenChange={setShowProgressDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>进度报工</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {selectedOrder &&
            <div className="text-sm text-gray-600">
                工单号：{selectedOrder.order_number}
            </div>
            }
            <div>
              <label className="text-sm font-medium">进度百分比</label>
              <div className="flex items-center gap-2 mt-1">
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={progressData.progress_percent}
                  onChange={(e) => setProgressData((prev) => ({ ...prev, progress_percent: parseInt(e.target.value) || 0 }))}
                  className="w-20 p-2 border rounded-md" />

                <span>%</span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">进度说明</label>
              <textarea
                className="w-full mt-1 p-2 border rounded-md"
                rows={3}
                value={progressData.progress_note}
                onChange={(e) => setProgressData((prev) => ({ ...prev, progress_note: e.target.value }))}
                placeholder="请输入进度说明..." />

            </div>
            <div>
              <label className="text-sm font-medium">当前问题</label>
              <textarea
                className="w-full mt-1 p-2 border rounded-md"
                rows={2}
                value={progressData.current_issues}
                onChange={(e) => setProgressData((prev) => ({ ...prev, current_issues: e.target.value }))}
                placeholder="如有问题请在此说明..." />

            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowProgressDialog(false)}>

              取消
            </Button>
            <Button
              className="bg-amber-500 hover:bg-amber-600"
              onClick={handleProgressReport}
              disabled={submitting}>

              {submitting ? "提交中..." : "确认报工"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 完工报工对话框 */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>完工报工</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {selectedOrder &&
            <div className="text-sm text-gray-600">
                工单号：{selectedOrder.order_number} | 计划数量：{selectedOrder.plan_qty}
            </div>
            }
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">完成数量</label>
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="number"
                    min="0"
                    max={selectedOrder?.plan_qty || 0}
                    value={completeData.completed_qty}
                    onChange={(e) => handleQuickQuantity("completed", parseInt(e.target.value) || 0)}
                    className="w-24 p-2 border rounded-md" />

                  <div className="flex gap-1">
                    {QUICK_QUANTITY_OPTIONS.COMMON.map((option, index) =>
                    <Button
                      key={index}
                      size="sm"
                      variant="outline"
                      onClick={() => handleQuickQuantity("completed", option.value)}>

                        {option.label}
                    </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleQuickQuantity("completed", "all")}>

                      全部
                    </Button>
                  </div>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium">合格数量</label>
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="number"
                    min="0"
                    max={completeData.completed_qty}
                    value={completeData.qualified_qty}
                    onChange={(e) => setCompleteData((prev) => ({ ...prev, qualified_qty: parseInt(e.target.value) || 0 }))}
                    className="w-24 p-2 border rounded-md" />

                  <span className="text-sm text-gray-600">
                    不良：{completeData.completed_qty - completeData.qualified_qty}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">工时</label>
              <div className="flex items-center gap-2 mt-1">
                <input
                  type="number"
                  step="0.25"
                  min="0"
                  value={completeData.work_hours}
                  onChange={(e) => setCompleteData((prev) => ({ ...prev, work_hours: parseFloat(e.target.value) || 0 }))}
                  className="w-24 p-2 border rounded-md" />

                <span className="text-sm text-gray-600">小时</span>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium">完工说明</label>
              <textarea
                className="w-full mt-1 p-2 border rounded-md"
                rows={3}
                value={completeData.report_note}
                onChange={(e) => setCompleteData((prev) => ({ ...prev, report_note: e.target.value }))}
                placeholder="请输入完工说明..." />

            </div>

            <div>
              <label className="text-sm font-medium">照片上传</label>
              <div className="mt-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handlePhotoUpload}
                  className="hidden" />

                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}>

                  <Camera className="h-4 w-4 mr-2" />
                  选择照片
                </Button>
              </div>
              {photos.length > 0 &&
              <div className="mt-2 grid grid-cols-4 gap-2">
                  {photos.map((photo, index) =>
                <div key={index} className="relative">
                      <img
                    src={photo.url}
                    alt={photo.name}
                    className="w-full h-20 object-cover rounded border" />

                      <Button
                    size="sm"
                    variant="destructive"
                    className="absolute -top-2 -right-2 h-6 w-6 p-0"
                    onClick={() => removePhoto(index)}>

                        <X className="h-3 w-3" />
                      </Button>
                </div>
                )}
              </div>
              }
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCompleteDialog(false)}>

              取消
            </Button>
            <Button
              className="bg-emerald-500 hover:bg-emerald-600"
              onClick={handleCompleteWork}
              disabled={submitting}>

              {submitting ? "提交中..." : "确认完工"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}