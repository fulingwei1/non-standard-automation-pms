import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  ShieldAlert,
  Zap,
  Eye,
  Play,
  AlertCircle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody } from
"../components/ui/dialog";
import { Switch } from "../components/ui/switch";
import { formatDate } from "../lib/utils";
import { progressApi } from "../services/api";

export default function ProgressForecast({ projectId }) {
  const { id: routeId } = useParams();
  const id = projectId || routeId;
  const navigate = useNavigate();

  // 状态管理
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // 自动处理选项
  const [autoBlock, setAutoBlock] = useState(false);
  const [delayThreshold, setDelayThreshold] = useState(7);

  // 对话框状态
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // 初始化加载数据
  useEffect(() => {
    console.log("[ProgressForecast] useEffect triggered - id:", id, "projectId:", projectId, "routeId:", routeId);
    if (!id) {
      console.error("[ProgressForecast] No project ID available");
      setErrorMessage("项目ID不可用");
      setLoading(false);
      return;
    }
    fetchProject();
    fetchForecast();
  }, [id, projectId]); // 包括projectId，确保当prop变化时重新加载

  const fetchProject = async () => {
    try {
      const res = await fetch(`/api/v1/projects/${id}`).then((r) => r.json());
      setProject(res.data?.data || res.data);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };

  const fetchForecast = async () => {
    try {
      setLoading(true);
      setErrorMessage("");
      console.log("[ProgressForecast] Fetching forecast for project:", id);
      const res = await progressApi.analytics.getForecast(id);
      console.log("[ProgressForecast] API response:", res);
      console.log("[ProgressForecast] Response data:", res.data);
      console.log("[ProgressForecast] Response data?.data:", res.data?.data);

      const data = res.data?.data || res.data;
      console.log("[ProgressForecast] Final data to set:", data);

      if (!data) {
        throw new Error("API returned no data");
      }

      setForecastData(data);
      console.log("[ProgressForecast] Forecast data set successfully");
    } catch (error) {
      console.error("[ProgressForecast] Failed to fetch forecast data:", error);
      console.error("[ProgressForecast] Error message:", error.message);
      console.error("[ProgressForecast] Error response:", error.response?.data);
      setErrorMessage("进度预测数据加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    try {
      setProcessing(true);
      const res = await progressApi.autoProcess.preview(id, {
        auto_block: autoBlock,
        delay_threshold: delayThreshold
      });
      setPreviewData(res.data?.data || res.data);
      setShowPreviewDialog(true);
    } catch (error) {
      console.error("Failed to preview auto process:", error);
      setErrorMessage("预览失败，请稍后重试。");
    } finally {
      setProcessing(false);
    }
  };

  const _handleApplyForecast = async () => {
    try {
      setProcessing(true);
      setShowConfirmDialog(false);
      setErrorMessage("");
      setSuccessMessage("");

      await progressApi.autoProcess.applyForecast(id, {
        auto_block: autoBlock,
        delay_threshold: delayThreshold
      });

      setSuccessMessage("进度预测已成功应用到任务！");

      // 刷新预测数据
      await fetchForecast();

      // 3秒后清除成功消息
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (error) {
      console.error("Failed to apply forecast:", error);
      setErrorMessage("应用进度预测失败：" + (error.message || "未知错误"));
    } finally {
      setProcessing(false);
    }
  };

  const handleCompleteProcess = async () => {
    try {
      setProcessing(true);
      setShowConfirmDialog(false);
      setErrorMessage("");
      setSuccessMessage("");

      const options = {
        auto_block: autoBlock,
        delay_threshold: delayThreshold,
        auto_fix_timing: false,
        auto_fix_missing: true,
        send_notifications: true
      };

      const res = await progressApi.autoProcess.runCompleteProcess(id, options);

      if (res.data?.success) {
        setSuccessMessage("自动处理流程执行成功！");

        // 刷新预测数据
        await fetchForecast();

        // 3秒后清除成功消息
        setTimeout(() => setSuccessMessage(""), 3000);
      } else {
        setErrorMessage("自动处理流程执行失败：" + (res.data?.error || "未知错误"));
      }
    } catch (error) {
      console.error("Failed to run complete process:", error);
      setErrorMessage("执行自动处理流程失败：" + (error.message || "未知错误"));
    } finally {
      setProcessing(false);
    }
  };

  // 计算统计数据
  const criticalTasks = forecastData?.tasks?.filter((t) => t.critical) || [];
  const delayedTasks = forecastData?.tasks?.filter((t) => (t.delay_days || 0) > 0) || [];
  const _onTrackTasks = forecastData?.tasks?.filter((t) => t.status === "OnTrack") || [];

  const _confidenceColor = {
    HIGH: "text-emerald-600 bg-emerald-50 border-emerald-200",
    MEDIUM: "text-amber-600 bg-amber-50 border-amber-200",
    LOW: "text-red-600 bg-red-50 border-red-200"
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <div className="text-slate-600">加载中...</div>
        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* 页面头部 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/projects/${id}`)}>

              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目
            </Button>
            <PageHeader
              title={`${project?.project_name || "项目"} - 进度预测`}
              description="智能化进度预测与风险预警" />

          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchForecast}
              disabled={processing}>

              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreview}
              disabled={processing}>

              <Eye className="w-4 h-4 mr-2" />
              预览自动处理
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => setShowConfirmDialog(true)}
              disabled={processing}>

              <Play className="w-4 h-4 mr-2" />
              执行自动处理
            </Button>
          </div>
        </div>
        
        {/* 消息提示 */}
        {errorMessage &&
        <div className="mb-4 rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 flex items-start">
            <AlertCircle className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
            <div>{errorMessage}</div>
        </div>
        }
        
        {successMessage &&
        <div className="mb-4 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 flex items-start">
            <CheckCircle2 className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
            <div>{successMessage}</div>
        </div>
        }
        
        {/* 自动处理选项 */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-8">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={autoBlock}
                      onCheckedChange={setAutoBlock} />

                    <span className="text-sm text-slate-700">自动阻塞延迟任务</span>
                  </div>
                  <div className="text-xs text-slate-500">
                    (超过阈值时自动标记为BLOCKED)
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <label className="text-sm text-slate-700">延迟阈值:</label>
                  <input
                    type="number"
                    value={delayThreshold || "unknown"}
                    onChange={(e) => setDelayThreshold(parseInt(e.target.value))}
                    min={1}
                    max={30}
                    className="w-20 px-3 py-1.5 border border-slate-300 rounded-md text-sm" />

                  <span className="text-sm text-slate-700">天</span>
                </div>
              </div>
              
              <div className="text-sm text-slate-500">
                预测准确性: {forecastData?.confidence || "N/A"}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* 概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        {/* 当前进度 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">当前进度</div>
              <TrendingUp className="w-4 h-4 text-emerald-500" />
            </div>
            <div className="text-3xl font-bold text-slate-900 mb-1">
              {forecastData?.current_progress?.toFixed(1) || 0}%
            </div>
            <Progress value={forecastData?.current_progress || 0} className="h-2" />
          </CardContent>
        </Card>
        
        {/* 预测完成日期 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">预测完成日期</div>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <div className="text-xl font-bold text-slate-900">
              {formatDate(forecastData?.predicted_completion_date)}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              预计还有 {forecastData?.forecast_horizon_days || 0} 天
            </div>
          </CardContent>
        </Card>
        
        {/* 预测延期 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">预测延期</div>
              <AlertTriangle className="w-4 h-4 text-amber-500" />
            </div>
            <div className={`text-xl font-bold ${
            (forecastData?.predicted_delay_days || 0) > 0 ? "text-red-600" : "text-emerald-600"}`
            }>
              {forecastData?.predicted_delay_days || 0} 天
            </div>
            <div className="text-sm text-slate-500 mt-1">
              计划日期: {formatDate(forecastData?.planned_completion_date)}
            </div>
          </CardContent>
        </Card>
        
        {/* 高风险任务 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">高风险任务</div>
              <ShieldAlert className="w-4 h-4 text-red-500" />
            </div>
            <div className="text-xl font-bold text-slate-900">
              {criticalTasks.length}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              占比: {forecastData?.tasks?.length ?
              (criticalTasks.length / forecastData.tasks?.length * 100).toFixed(1) : 0}%
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* 未来进度预期 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>未来进度预期</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-600 mb-2">未来7天</div>
              <div className="text-2xl font-bold text-slate-900">
                +{forecastData?.expected_progress_next_7d?.toFixed(1) || 0}%
              </div>
              <Progress
                value={forecastData?.expected_progress_next_7d || 0}
                className="h-2 mt-2" />

            </div>
            <div>
              <div className="text-sm text-slate-600 mb-2">未来14天</div>
              <div className="text-2xl font-bold text-slate-900">
                +{forecastData?.expected_progress_next_14d?.toFixed(1) || 0}%
              </div>
              <Progress
                value={forecastData?.expected_progress_next_14d || 0}
                className="h-2 mt-2" />

            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* 延迟任务列表 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              延迟任务列表
            </div>
            <Badge variant={delayedTasks.length > 0 ? "destructive" : "secondary"}>
              {delayedTasks.length} 个
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {delayedTasks.length === 0 ?
          <div className="text-center py-8 text-slate-500">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-emerald-500" />
              <div>没有延迟任务，项目进展顺利！</div>
          </div> :

          <div className="space-y-3">
              {delayedTasks.slice(0, 10).map((task) =>
            <div key={task.task_id} className="border border-slate-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="font-medium text-slate-900 mb-1">
                        {task.task_name}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Badge variant={task.critical ? "destructive" : "secondary"}>
                          {task.status}
                        </Badge>
                        <span>进度: {task.progress_percent}%</span>
                      </div>
                    </div>
                    <div className={`text-sm font-semibold ${
                task.critical ? "text-red-600" : "text-amber-600"}`
                }>
                      延迟 {task.delay_days} 天
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm text-slate-600">
                    <div>
                      <span className="text-slate-500">计划完成:</span>{" "}
                      {formatDate(task.plan_end)}
                    </div>
                    <div>
                      <span className="text-slate-500">预测完成:</span>{" "}
                      {formatDate(task.predicted_finish_date)}
                    </div>
                    <div>
                      <span className="text-slate-500">速度:</span>{" "}
                      {task.rate_per_day ? `${task.rate_per_day.toFixed(2)}%/天` : "N/A"}
                    </div>
                    <div>
                      <span className="text-slate-500">权重:</span>{" "}
                      {task.weight}
                    </div>
                  </div>
            </div>
            )}
              
              {delayedTasks.length > 10 &&
            <div className="text-center pt-4">
                  <div className="text-sm text-slate-500">
                    还有 {delayedTasks.length - 10} 个延迟任务...
                  </div>
            </div>
            }
          </div>
          }
        </CardContent>
      </Card>
      
      {/* 预览对话框 */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              自动处理预览
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {previewData ?
            <div className="space-y-6">
                {/* 预览操作 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">将要执行的操作</h4>
                  <div className="space-y-2">
                    {previewData.preview_actions?.will_block?.length > 0 &&
                  <div className="rounded-md bg-red-50 border border-red-200 p-3">
                        <div className="font-medium text-red-900 mb-2">
                          将阻塞 {previewData.preview_actions.will_block?.length} 个任务
                        </div>
                        <ul className="text-sm space-y-1">
                          {(previewData.preview_actions.will_block || []).map((action, idx) =>
                      <li key={idx} className="text-red-800">
                              {action.task_name}: {action.reason}
                      </li>
                      )}
                        </ul>
                  </div>
                  }
                    
                    {previewData.preview_actions?.will_fix_timing > 0 &&
                  <div className="rounded-md bg-amber-50 border border-amber-200 p-3">
                        <div className="font-medium text-amber-900 mb-2">
                          将修复 {previewData.preview_actions.will_fix_timing} 个时序冲突
                        </div>
                  </div>
                  }
                    
                    {previewData.preview_actions?.will_remove_missing > 0 &&
                  <div className="rounded-md bg-blue-50 border border-blue-200 p-3">
                        <div className="font-medium text-blue-900 mb-2">
                          将移除 {previewData.preview_actions.will_remove_missing} 个缺失依赖
                        </div>
                  </div>
                  }
                    
                    {previewData.preview_actions?.will_send_notifications &&
                  <div className="rounded-md bg-emerald-50 border border-emerald-200 p-3">
                        <div className="font-medium text-emerald-900 mb-2">
                          将发送通知给相关人员
                        </div>
                  </div>
                  }
                  </div>
                </div>
            </div> :

            <div className="text-center py-8 text-slate-500">加载预览数据中...</div>
            }
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPreviewDialog(false)}>
              取消
            </Button>
            <Button onClick={() => setShowConfirmDialog(true)}>
              确认执行
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* 确认执行对话框 */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Play className="w-5 h-5 text-blue-500" />
              确认执行自动处理
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <p className="text-slate-700">
                确定要执行以下自动处理操作吗？
              </p>
              
              <div className="rounded-md bg-slate-50 p-4 space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-blue-500" />
                  <span>
                    {autoBlock ? "自动阻塞" : "仅标记"} 延迟超过 {delayThreshold} 天的任务
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-blue-500" />
                  <span>发送风险通知给项目经理和任务负责人</span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-blue-500" />
                  <span>记录所有操作到进度日志</span>
                </div>
              </div>
              
              <div className="rounded-md bg-amber-50 border border-amber-200 p-3 text-sm">
                <strong className="text-amber-900">注意:</strong>
                此操作将自动更新任务状态和创建通知，请确认后执行。
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              取消
            </Button>
            <Button
              onClick={handleCompleteProcess}
              disabled={processing}>

              {processing ? "执行中..." : "确认执行"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}