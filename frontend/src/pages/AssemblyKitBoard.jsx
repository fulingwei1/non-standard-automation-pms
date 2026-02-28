/**
 * Assembly Kit Board Page - 装配齐套看板页面
 * Features: 6阶段进度可视化、齐套率分布、缺料预警、排产建议
 */
import { useState, useEffect } from "react";
import {
  Package,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  BarChart3,
  PlayCircle,
  Clock,
  Wrench,
  Zap,
  Cable,
  Bug,
  Palette,
  ChevronRight,
  ThumbsUp,
  ThumbsDown,
  Calendar,
  TrendingUp,
  Eye } from
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
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter } from
"../components/ui/dialog";
import { Textarea } from "../components/ui/textarea";
import { cn } from "../lib/utils";
import { assemblyKitApi, projectApi } from "../services/api";

// 阶段图标映射
const stageIcons = {
  FRAME: Wrench,
  MECH: Package,
  ELECTRIC: Zap,
  WIRING: Cable,
  DEBUG: Bug,
  COSMETIC: Palette
};

// 预警级别配置
const alertLevelConfig = {
  L1: {
    label: "停工预警",
    color: "bg-red-600",
    textColor: "text-red-600",
    bgLight: "bg-red-50 border-red-500"
  },
  L2: {
    label: "紧急预警",
    color: "bg-orange-500",
    textColor: "text-orange-600",
    bgLight: "bg-orange-50 border-orange-500"
  },
  L3: {
    label: "提前预警",
    color: "bg-yellow-500",
    textColor: "text-yellow-600",
    bgLight: "bg-yellow-50 border-yellow-500"
  },
  L4: {
    label: "常规预警",
    color: "bg-blue-500",
    textColor: "text-blue-600",
    bgLight: "bg-blue-50 border-blue-500"
  }
};

export default function AssemblyKitBoard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [projects, setProjects] = useState([]);
  const [filterProject, setFilterProject] = useState("");
  const [_selectedAnalysis, _setSelectedAnalysis] = useState(null);
  const [analysisDetail, setAnalysisDetail] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [alerts, setAlerts] = useState(null);

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    fetchDashboardData();
    fetchAlerts();
  }, [filterProject]);

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject && filterProject !== "all") {
        params.project_ids = filterProject;
      }
      const res = await assemblyKitApi.dashboard(params);
      setDashboardData(res.data || res || null);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSuggestions = async () => {
    try {
      setLoading(true);
      const res = await assemblyKitApi.generateSuggestions({ scope: "WEEKLY" });
      console.log("排产建议生成成功:", res.data);
      if (res.data?.suggestions) {
        alert(`已生成 ${res.data.suggestions.length} 条排产建议`);
        fetchDashboardData();
      }
    } catch (error) {
      console.error("生成排产建议失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const params = { page_size: 20 };
      if (filterProject && filterProject !== "all") {
        params.project_id = filterProject;
      }
      const res = await assemblyKitApi.getShortageAlerts(params);
      setAlerts(res.data || res || null);
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
    }
  };

  const fetchAnalysisDetail = async (readinessId) => {
    try {
      const res = await assemblyKitApi.getAnalysisDetail(readinessId);
      setAnalysisDetail(res.data || res);
      setDetailDialogOpen(true);
    } catch (error) {
      console.error("获取详情失败:", error);
    }
  };

  const handleAcceptSuggestion = async (suggestionId) => {
    try {
      await assemblyKitApi.acceptSuggestion(suggestionId, {});
      console.log("已接受排产建议");
      fetchDashboardData();
    } catch (error) {
      console.error("操作失败:", error);
    }
  };

  const handleRejectSuggestion = async () => {
    if (!selectedSuggestion || !rejectReason.trim()) {
      console.error("请填写拒绝原因");
      return;
    }
    try {
      await assemblyKitApi.rejectSuggestion(selectedSuggestion.id, {
        reject_reason: rejectReason
      });
      console.log("已拒绝排产建议");
      setRejectDialogOpen(false);
      setRejectReason("");
      setSelectedSuggestion(null);
      fetchDashboardData();
    } catch (error) {
      console.error("操作失败:", error);
    }
  };

  const getKitRateColor = (rate) => {
    if (rate >= 100) {return "text-emerald-600";}
    if (rate >= 80) {return "text-blue-600";}
    if (rate >= 50) {return "text-amber-600";}
    return "text-red-600";
  };

  const _getProgressColor = (rate) => {
    if (rate >= 100) {return "bg-emerald-500";}
    if (rate >= 80) {return "bg-blue-500";}
    if (rate >= 50) {return "bg-amber-500";}
    return "bg-red-500";
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>);

  }

  const stats = dashboardData?.stats || {};
  const stageStats = dashboardData?.stage_stats || [];
  const alertSummary = dashboardData?.alert_summary || {};
  const recentAnalyses = dashboardData?.recent_analyses || [];
  const pendingSuggestions = dashboardData?.pending_suggestions || [];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <PageHeader
          title="装配齐套看板"
          description="基于装配工艺路径的智能齐套分析，实现能做到哪一步的精准判断" />

        <div className="flex items-center gap-4">
          <Select value={filterProject} onValueChange={setFilterProject}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="选择项目" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部项目</SelectItem>
              {projects.map((proj) =>
              <SelectItem key={proj.id} value={proj.id.toString()}>
                  {proj.name || proj.project_name}
              </SelectItem>
              )}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            onClick={() => {
              fetchDashboardData();
              fetchAlerts();
            }}>

            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
          <Button
            variant="outline"
            onClick={handleGenerateSuggestions}
            disabled={loading}>

            <Calendar className="w-4 h-4 mr-2" />
            生成排产建议
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">项目总数</div>
                <div className="text-2xl font-bold text-slate-800">
                  {stats.total_projects || 0}
                </div>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">可开工</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {stats.can_start_count || 0}
                </div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">平均齐套率</div>
                <div
                  className={cn(
                    "text-2xl font-bold",
                    getKitRateColor(stats.avg_kit_rate || 0)
                  )}>

                  {stats.avg_kit_rate || 0}%
                </div>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">阻塞齐套率</div>
                <div
                  className={cn(
                    "text-2xl font-bold",
                    getKitRateColor(stats.avg_blocking_rate || 0)
                  )}>

                  {stats.avg_blocking_rate || 0}%
                </div>
              </div>
              <Package className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 6-Stage Progress Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlayCircle className="w-5 h-5" />
            装配阶段齐套率
          </CardTitle>
          <CardDescription>
            六个装配阶段的齐套情况，阻塞齐套率需达到100%才能开始该阶段
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-4">
            {stageStats.map((stage, index) => {
              const Icon = stageIcons[stage.stage_code] || Package;
              const isBlocked = stage.blocked_count > 0;
              return (
                <div key={stage.stage_code} className="relative">
                  {/* Connection line */}
                  {index < stageStats.length - 1 &&
                  <div className="absolute top-8 left-1/2 w-full h-0.5 bg-slate-200 z-0" />
                  }
                  <div
                    className={cn(
                      "relative z-10 flex flex-col items-center p-4 rounded-lg border-2 transition-all",
                      isBlocked ?
                      "border-red-300 bg-red-50" :
                      "border-emerald-300 bg-emerald-50"
                    )}>

                    <div
                      className={cn(
                        "w-12 h-12 rounded-full flex items-center justify-center mb-2",
                        isBlocked ? "bg-red-100" : "bg-emerald-100"
                      )}>

                      <Icon
                        className={cn(
                          "w-6 h-6",
                          isBlocked ? "text-red-600" : "text-emerald-600"
                        )} />

                    </div>
                    <div className="text-sm font-medium text-center mb-1">
                      {stage.stage_name}
                    </div>
                    <div
                      className={cn(
                        "text-lg font-bold",
                        getKitRateColor(stage.avg_kit_rate)
                      )}>

                      {stage.avg_kit_rate}%
                    </div>
                    <div className="flex gap-2 mt-2 text-xs">
                      <span className="text-emerald-600">
                        {stage.can_start_count} 可开
                      </span>
                      <span className="text-red-600">
                        {stage.blocked_count} 阻塞
                      </span>
                    </div>
                  </div>
                </div>);

            })}
          </div>
        </CardContent>
      </Card>

      {/* Alert Summary */}
      <div className="grid grid-cols-4 gap-4">
        {["L1", "L2", "L3", "L4"].map((level) => {
          const config = alertLevelConfig[level];
          const count = alertSummary[level] || 0;
          return (
            <Card
              key={level}
              className={cn(
                count > 0 && "border-l-4",
                count > 0 && config.bgLight.split(" ")[1]
              )}>

              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">
                      {config.label}
                    </div>
                    <div
                      className={cn(
                        "text-2xl font-bold",
                        count > 0 ? config.textColor : "text-slate-400"
                      )}>

                      {count}
                    </div>
                  </div>
                  <AlertTriangle
                    className={cn(
                      "w-8 h-8",
                      count > 0 ? config.textColor : "text-slate-300"
                    )} />

                </div>
              </CardContent>
            </Card>);

        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Analyses */}
        <Card>
          <CardHeader>
            <CardTitle>最近齐套分析</CardTitle>
          </CardHeader>
          <CardContent>
            {recentAnalyses.length > 0 ?
            <div className="space-y-3">
                {recentAnalyses.map((analysis) =>
              <div
                key={analysis.id}
                className={cn(
                  "p-4 rounded-lg border cursor-pointer hover:bg-slate-50 transition-colors",
                  analysis.can_start ?
                  "border-emerald-200 bg-emerald-50/50" :
                  "border-red-200 bg-red-50/50"
                )}
                onClick={() => fetchAnalysisDetail(analysis.id)}>

                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium">
                            {analysis.project_name || analysis.project_no}
                          </span>
                          {analysis.machine_no &&
                      <Badge variant="outline">
                              {analysis.machine_no}
                      </Badge>
                      }
                        </div>
                        <div className="text-sm text-slate-500 mb-2">
                          分析时间:{" "}
                          {new Date(analysis.analysis_time).toLocaleString()}
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1">
                            <span className="text-sm text-slate-500">
                              整体:
                            </span>
                            <span
                          className={cn(
                            "font-medium",
                            getKitRateColor(analysis.overall_kit_rate)
                          )}>

                              {analysis.overall_kit_rate}%
                            </span>
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="text-sm text-slate-500">
                              阻塞:
                            </span>
                            <span
                          className={cn(
                            "font-medium",
                            getKitRateColor(analysis.blocking_kit_rate)
                          )}>

                              {analysis.blocking_kit_rate}%
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        {analysis.can_start ?
                    <Badge className="bg-emerald-500">可开工</Badge> :

                    <Badge className="bg-red-500">
                            阻塞于 {analysis.first_blocked_stage}
                    </Badge>
                    }
                        <Eye className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
              </div>
              )}
            </div> :

            <div className="text-center py-8 text-slate-400">
                暂无分析记录
            </div>
            }
          </CardContent>
        </Card>

        {/* Pending Suggestions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              排产建议
            </CardTitle>
          </CardHeader>
          <CardContent>
            {pendingSuggestions.length > 0 ?
            <div className="space-y-3">
                {pendingSuggestions.map((suggestion) =>
              <div
                key={suggestion.id}
                className="p-4 rounded-lg border bg-blue-50/50 border-blue-200">

                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="font-medium">
                          {suggestion.project_name || suggestion.project_no}
                        </div>
                        {suggestion.machine_no &&
                    <span className="text-sm text-slate-500">
                            {suggestion.machine_no}
                    </span>
                    }
                      </div>
                      <Badge variant="outline" className="bg-blue-100">
                        {suggestion.suggestion_type === "CAN_START" ?
                    "可立即开工" :
                    suggestion.suggestion_type === "WAIT_MATERIAL" ?
                    "等待物料" :
                    suggestion.suggestion_type === "PARTIAL_START" ?
                    "部分开工" :
                    suggestion.suggestion_type}
                      </Badge>
                    </div>
                    <div className="text-sm text-slate-600 mb-2">
                      建议开工: {suggestion.suggested_start_date}
                    </div>
                    <div className="flex items-center gap-2 text-sm mb-3">
                      <span>
                        优先级得分: <strong>{suggestion.priority_score}</strong>
                      </span>
                      <span>
                        齐套率:{" "}
                        <strong
                      className={getKitRateColor(
                        suggestion.current_kit_rate
                      )}>

                          {suggestion.current_kit_rate}%
                        </strong>
                      </span>
                    </div>
                    {suggestion.score_factors &&
                <div className="text-xs text-slate-500 mb-2 p-2 bg-white rounded">
                        <div className="font-medium mb-1">评分详情：</div>
                        <div className="space-y-1">
                          {Object.entries(suggestion.score_factors).map(
                      ([key, factor]) =>
                      <div key={key} className="flex justify-between">
                                <span>{factor.description || key}:</span>
                                <span className="font-medium">
                                  {factor.score}/{factor.max}分
                                </span>
                      </div>

                    )}
                        </div>
                </div>
                }
                    {suggestion.resource_allocation &&
                <div className="text-xs text-slate-500 mb-2 p-2 bg-white rounded">
                        <div className="font-medium mb-1">资源情况：</div>
                        <div className="space-y-1">
                          <div>
                            可用工位:{" "}
                            {suggestion.resource_allocation.
                      available_workstations || 0}
                            个
                          </div>
                          <div>
                            可用人员:{" "}
                            {suggestion.resource_allocation.available_workers ||
                      0}
                            人
                          </div>
                          {suggestion.resource_allocation.conflicts &&
                    suggestion.resource_allocation.conflicts.length >
                    0 &&
                    <div className="text-red-500">
                                资源冲突:{" "}
                                {
                      suggestion.resource_allocation.conflicts.
                      length
                      }
                                个
                    </div>
                    }
                        </div>
                </div>
                }
                    {suggestion.reason &&
                <div className="text-sm text-slate-500 mb-3 p-2 bg-white rounded">
                        {suggestion.reason}
                </div>
                }
                    <div className="flex gap-2">
                      <Button
                    size="sm"
                    className="bg-emerald-500 hover:bg-emerald-600"
                    onClick={() => handleAcceptSuggestion(suggestion.id)}>

                        <ThumbsUp className="w-4 h-4 mr-1" />
                        接受
                      </Button>
                      <Button
                    size="sm"
                    variant="outline"
                    className="border-red-300 text-red-600 hover:bg-red-50"
                    onClick={() => {
                      setSelectedSuggestion(suggestion);
                      setRejectDialogOpen(true);
                    }}>

                        <ThumbsDown className="w-4 h-4 mr-1" />
                        拒绝
                      </Button>
                    </div>
              </div>
              )}
            </div> :

            <div className="text-center py-8 text-slate-400">
                暂无待处理建议
            </div>
            }
          </CardContent>
        </Card>
      </div>

      {/* Shortage Alerts List */}
      {alerts && alerts.items && alerts.items.length > 0 &&
      <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              缺料预警明细
              <Badge variant="outline" className="ml-2">
                {alerts.total} 条
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>预警级别</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>物料</TableHead>
                  <TableHead>装配阶段</TableHead>
                  <TableHead>缺料数量</TableHead>
                  <TableHead>是否阻塞</TableHead>
                  <TableHead>响应截止</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {alerts.items.map((alert) => {
                const config =
                alertLevelConfig[alert.alert_level] || alertLevelConfig.L4;
                return (
                  <TableRow key={alert.shortage_id}>
                      <TableCell>
                        <Badge className={config.color}>{config.label}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{alert.project_name}</div>
                        {alert.machine_no &&
                      <div className="text-xs text-slate-500">
                            {alert.machine_no}
                      </div>
                      }
                      </TableCell>
                      <TableCell>
                        <div>{alert.material_name}</div>
                        <div className="text-xs text-slate-500">
                          {alert.material_code}
                        </div>
                      </TableCell>
                      <TableCell>{alert.stage_name}</TableCell>
                      <TableCell className="text-red-600 font-medium">
                        {alert.shortage_qty}
                      </TableCell>
                      <TableCell>
                        {alert.is_blocking ?
                      <XCircle className="w-5 h-5 text-red-500" /> :

                      <CheckCircle2 className="w-5 h-5 text-slate-300" />
                      }
                      </TableCell>
                      <TableCell className="text-sm">
                        {new Date(alert.response_deadline).toLocaleString()}
                      </TableCell>
                  </TableRow>);

              })}
              </TableBody>
            </Table>
          </CardContent>
      </Card>
      }

      {/* Analysis Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>齐套分析详情</DialogTitle>
            <DialogDescription>
              {analysisDetail?.readiness_no} - {analysisDetail?.project_name}
            </DialogDescription>
          </DialogHeader>
          {analysisDetail &&
          <div className="space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-sm text-slate-500">整体齐套率</div>
                  <div
                  className={cn(
                    "text-xl font-bold",
                    getKitRateColor(analysisDetail.overall_kit_rate)
                  )}>

                    {analysisDetail.overall_kit_rate}%
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-sm text-slate-500">阻塞齐套率</div>
                  <div
                  className={cn(
                    "text-xl font-bold",
                    getKitRateColor(analysisDetail.blocking_kit_rate)
                  )}>

                    {analysisDetail.blocking_kit_rate}%
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-sm text-slate-500">开工状态</div>
                  <div
                  className={cn(
                    "text-xl font-bold",
                    analysisDetail.can_start ?
                    "text-emerald-600" :
                    "text-red-600"
                  )}>

                    {analysisDetail.can_start ? "可开工" : "阻塞"}
                  </div>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="text-sm text-slate-500">首个阻塞阶段</div>
                  <div className="text-xl font-bold text-slate-700">
                    {analysisDetail.first_blocked_stage || "-"}
                  </div>
                </div>
              </div>

              {/* Stage Progress */}
              <div>
                <h4 className="font-medium mb-3">各阶段齐套率</h4>
                <div className="space-y-3">
                  {analysisDetail.stage_kit_rates?.map((stage) =>
                <div
                  key={stage.stage_code}
                  className="flex items-center gap-4">

                      <div className="w-24 text-sm font-medium">
                        {stage.stage_name}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Progress
                        value={stage.kit_rate}
                        className="h-2 flex-1" />

                          <span
                        className={cn(
                          "text-sm font-medium w-12",
                          getKitRateColor(stage.kit_rate)
                        )}>

                            {stage.kit_rate}%
                          </span>
                        </div>
                        <div className="text-xs text-slate-500">
                          阻塞: {stage.blocking_rate}% |
                          {stage.can_start ?
                      <span className="text-emerald-600 ml-1">
                              可开始
                      </span> :

                      <span className="text-red-600 ml-1">阻塞</span>
                      }
                        </div>
                      </div>
                </div>
                )}
                </div>
              </div>

              {/* Shortage Details */}
              {analysisDetail.shortage_details?.length > 0 &&
            <div>
                  <h4 className="font-medium mb-3">
                    缺料明细 ({analysisDetail.shortage_details.length} 项)
                  </h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>物料编码</TableHead>
                        <TableHead>物料名称</TableHead>
                        <TableHead>装配阶段</TableHead>
                        <TableHead>需求</TableHead>
                        <TableHead>可用</TableHead>
                        <TableHead>缺料</TableHead>
                        <TableHead>阻塞性</TableHead>
                        <TableHead>预警</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {analysisDetail.shortage_details.map((detail) =>
                  <TableRow key={detail.id}>
                          <TableCell className="font-mono text-sm">
                            {detail.material_code}
                          </TableCell>
                          <TableCell>{detail.material_name}</TableCell>
                          <TableCell>
                            {detail.stage_name || detail.assembly_stage}
                          </TableCell>
                          <TableCell>{detail.required_qty}</TableCell>
                          <TableCell>{detail.available_qty}</TableCell>
                          <TableCell className="text-red-600 font-medium">
                            {detail.shortage_qty}
                          </TableCell>
                          <TableCell>
                            {detail.is_blocking ?
                      <Badge className="bg-red-500">阻塞</Badge> :

                      <Badge variant="outline">可后补</Badge>
                      }
                          </TableCell>
                          <TableCell>
                            <Badge
                        className={
                        alertLevelConfig[detail.alert_level]?.color ||
                        "bg-slate-500"
                        }>

                              {detail.alert_level}
                            </Badge>
                          </TableCell>
                  </TableRow>
                  )}
                    </TableBody>
                  </Table>
            </div>
            }
          </div>
          }
        </DialogContent>
      </Dialog>

      {/* Reject Suggestion Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>拒绝排产建议</DialogTitle>
            <DialogDescription>请填写拒绝原因</DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="请输入拒绝原因..."
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={4} />

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRejectDialogOpen(false)}>

              取消
            </Button>
            <Button
              onClick={handleRejectSuggestion}
              className="bg-red-500 hover:bg-red-600">

              确认拒绝
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}