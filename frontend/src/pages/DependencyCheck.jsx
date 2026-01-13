import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Network,
  AlertCircle,
  Wrench,
  Eye,
  Play,
  AlertOctagon,
  GitBranch,
  Link2,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../components/ui/dialog";
import { formatDate } from "../lib/utils";
import { progressApi } from "../services/api";

export default function DependencyCheck({ projectId }) {
  const { id: routeId } = useParams();
  const id = projectId || routeId;
  const navigate = useNavigate();

  // 状态管理
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [dependencyData, setDependencyData] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // 自动修复选项
  const [autoFixTiming, setAutoFixTiming] = useState(false);
  const [autoFixMissing, setAutoFixMissing] = useState(true);

  // 对话框状态
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // 初始化加载数据
  useEffect(() => {
    console.log("[DependencyCheck] useEffect triggered - id:", id, "projectId:", projectId, "routeId:", routeId);
    if (!id) {
      console.error("[DependencyCheck] No project ID available");
      setErrorMessage("项目ID不可用");
      setLoading(false);
      return;
    }
    fetchProject();
    fetchDependencyCheck();
  }, [id, projectId]);  // 包括projectId，确保当prop变化时重新加载
  
  const fetchProject = async () => {
    try {
      const res = await fetch(`/api/v1/projects/${id}`).then(r => r.json());
      setProject(res.data?.data || res.data);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };
  
  const fetchDependencyCheck = async () => {
    try {
      setLoading(true);
      setErrorMessage("");
      console.log("[DependencyCheck] Fetching dependency check for project:", id);
      const res = await progressApi.analytics.checkDependencies(id);
      console.log("[DependencyCheck] API response:", res);
      console.log("[DependencyCheck] Response data:", res.data);
      console.log("[DependencyCheck] Response data?.data:", res.data?.data);

      const data = res.data?.data || res.data;
      console.log("[DependencyCheck] Final data to set:", data);

      if (!data) {
        throw new Error("API returned no data");
      }

      setDependencyData(data);
      console.log("[DependencyCheck] Dependency data set successfully");
    } catch (error) {
      console.error("[DependencyCheck] Failed to fetch dependency data:", error);
      console.error("[DependencyCheck] Error message:", error.message);
      console.error("[DependencyCheck] Error response:", error.response?.data);
      setErrorMessage("依赖检查数据加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };
  
  const handlePreview = async () => {
    try {
      setProcessing(true);

      // 先获取依赖检查结果
      const checkRes = await progressApi.analytics.checkDependencies(id);
      const depData = checkRes.data?.data || checkRes.data;

      // 构建预览数据
      const preview = {
        has_cycle: depData?.has_cycle || false,
        cycle_count: depData?.cycle_paths?.length || 0,
        cycle_paths: depData?.cycle_paths || [],
        issue_count: depData?.issues?.length || 0,
        issues: depData?.issues || [],
        preview_actions: {
          will_fix_timing: depData?.issues?.filter(i =>
            i.issue_type === "TIMING_CONFLICT" && autoFixTiming
          ).length || 0,
          will_remove_missing: depData?.issues?.filter(i =>
            i.issue_type === "MISSING_PREDECESSOR" && autoFixMissing
          ).length || 0,
          will_skip_cycles: depData?.cycle_paths?.length || 0,
          will_send_notifications: (
            depData?.has_cycle ||
            depData?.issues?.some(i =>
              i.severity === "HIGH" || i.severity === "URGENT"
            )
          )
        }
      };
      
      setPreviewData(preview);
      setShowPreviewDialog(true);
    } catch (error) {
      console.error("Failed to preview dependency check:", error);
      setErrorMessage("预览失败，请稍后重试。");
    } finally {
      setProcessing(false);
    }
  };
  
  const handleFixDependencies = async () => {
    try {
      setProcessing(true);
      setShowConfirmDialog(false);
      setErrorMessage("");
      setSuccessMessage("");

      const res = await progressApi.autoProcess.fixDependencies(id, {
        auto_fix_timing: autoFixTiming,
        auto_fix_missing: autoFixMissing
      });
      
      if (res.data?.success) {
        setSuccessMessage("依赖问题已成功修复！");
        
        // 刷新依赖检查数据
        await fetchDependencyCheck();
        
        // 3秒后清除成功消息
        setTimeout(() => setSuccessMessage(""), 3000);
      } else {
        setErrorMessage("修复依赖问题失败：" + (res.data?.error || "未知错误"));
      }
    } catch (error) {
      console.error("Failed to fix dependencies:", error);
      setErrorMessage("修复依赖问题失败：" + (error.message || "未知错误"));
    } finally {
      setProcessing(false);
    }
  };
  
  // 分类问题
  const cycleIssues = dependencyData?.cycle_paths || [];
  const timingIssues = dependencyData?.issues?.filter(i => 
    i.issue_type === "TIMING_CONFLICT"
  ) || [];
  const missingIssues = dependencyData?.issues?.filter(i => 
    i.issue_type === "MISSING_PREDECESSOR"
  ) || [];
  const otherIssues = dependencyData?.issues?.filter(i => 
    !["TIMING_CONFLICT", "MISSING_PREDECESSOR"].includes(i.issue_type)
  ) || [];
  
  // 问题严重度颜色
  const severityColors = {
    HIGH: "text-red-600 bg-red-50 border-red-200",
    URGENT: "text-red-700 bg-red-100 border-red-300",
    MEDIUM: "text-amber-600 bg-amber-50 border-amber-200",
    LOW: "text-blue-600 bg-blue-50 border-blue-200",
  };
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <div className="text-slate-600">加载中...</div>
        </div>
      </div>
    );
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
              onClick={() => navigate(`/projects/${id}`)}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目
            </Button>
            <PageHeader
              title={`${project?.project_name || "项目"} - 依赖巡检`}
              description="检测循环依赖、缺失依赖和时序冲突"
            />
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDependencyCheck}
              disabled={processing}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreview}
              disabled={processing}
            >
              <Eye className="w-4 h-4 mr-2" />
              预览修复
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => setShowConfirmDialog(true)}
              disabled={processing}
            >
              <Wrench className="w-4 h-4 mr-2" />
              执行修复
            </Button>
          </div>
        </div>
        
        {/* 消息提示 */}
        {errorMessage && (
          <div className="mb-4 rounded-md bg-red-50 border border-red-200 text-red-700 px-4 py-3 flex items-start">
            <AlertCircle className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
            <div>{errorMessage}</div>
          </div>
        )}
        
        {successMessage && (
          <div className="mb-4 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 flex items-start">
            <CheckCircle2 className="w-5 h-5 mr-3 mt-0.5 flex-shrink-0" />
            <div>{successMessage}</div>
          </div>
        )}
        
        {/* 自动修复选项 */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-8">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="autoFixTiming"
                    checked={autoFixTiming}
                    onChange={(e) => setAutoFixTiming(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded border-slate-300"
                  />
                  <label 
                    htmlFor="autoFixTiming" 
                    className="text-sm text-slate-700 cursor-pointer"
                  >
                    自动修复时序冲突
                  </label>
                </div>
                <div className="text-xs text-slate-500">
                  (调整任务计划时间)
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="autoFixMissing"
                  checked={autoFixMissing}
                  onChange={(e) => setAutoFixMissing(e.target.checked)}
                  className="w-4 h-4 text-blue-600 rounded border-slate-300"
                />
                <label 
                  htmlFor="autoFixMissing" 
                  className="text-sm text-slate-700 cursor-pointer"
                >
                  自动移除缺失依赖
                </label>
                <div className="text-xs text-slate-500">
                  (删除指向不存在任务的依赖)
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* 概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        {/* 循环依赖 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">循环依赖</div>
              <GitBranch className={`w-4 h-4 ${cycleIssues.length > 0 ? "text-red-500" : "text-emerald-500"}`} />
            </div>
            <div className={`text-3xl font-bold ${cycleIssues.length > 0 ? "text-red-600" : "text-emerald-600"}`}>
              {cycleIssues.length}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              {cycleIssues.length > 0 ? "存在循环依赖，需要人工处理" : "无循环依赖"}
            </div>
          </CardContent>
        </Card>
        
        {/* 时序冲突 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">时序冲突</div>
              <AlertTriangle className={`w-4 h-4 ${timingIssues.length > 0 ? "text-amber-500" : "text-emerald-500"}`} />
            </div>
            <div className={`text-3xl font-bold ${timingIssues.length > 0 ? "text-amber-600" : "text-emerald-600"}`}>
              {timingIssues.length}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              {autoFixTiming ? "将自动修复" : "需要手动调整"}
            </div>
          </CardContent>
        </Card>
        
        {/* 缺失依赖 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">缺失依赖</div>
              <Link2 className={`w-4 h-4 ${missingIssues.length > 0 ? "text-blue-500" : "text-emerald-500"}`} />
            </div>
            <div className={`text-3xl font-bold ${missingIssues.length > 0 ? "text-blue-600" : "text-emerald-600"}`}>
              {missingIssues.length}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              {autoFixMissing ? "将自动移除" : "需手动删除"}
            </div>
          </CardContent>
        </Card>
        
        {/* 其他问题 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-600">其他问题</div>
              <AlertOctagon className={`w-4 h-4 ${otherIssues.length > 0 ? "text-amber-500" : "text-emerald-500"}`} />
            </div>
            <div className={`text-3xl font-bold ${otherIssues.length > 0 ? "text-amber-600" : "text-emerald-600"}`}>
              {otherIssues.length}
            </div>
            <div className="text-sm text-slate-500 mt-1">
              {otherIssues.length > 0 ? "需手动处理" : "无其他问题"}
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* 循环依赖详情 */}
      {cycleIssues.length > 0 && (
        <Card className="mb-6 border border-red-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              循环依赖详情
              <Badge variant="destructive">{cycleIssues.length} 个</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {cycleIssues.map((cycle, idx) => (
                <div key={idx} className="rounded-md bg-red-50 border border-red-200 p-4">
                  <div className="font-medium text-red-900 mb-2">
                    循环 {idx + 1}:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {cycle.map((taskName, taskIdx) => (
                      <React.Fragment key={taskIdx}>
                        <span className="text-sm text-red-800">
                          {taskName}
                        </span>
                        {taskIdx < cycle.length - 1 && (
                          <span className="text-red-400">→</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-md bg-amber-50 border border-amber-200 p-3 text-sm">
              <strong className="text-amber-900">⚠️ 循环依赖无法自动修复，需要手动调整依赖关系或拆分任务。</strong>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* 时序冲突详情 */}
      {timingIssues.length > 0 && (
        <Card className="mb-6 border border-amber-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-700">
              <AlertTriangle className="w-5 h-5" />
              时序冲突详情
              <Badge variant="secondary">{timingIssues.length} 个</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {timingIssues.map((issue, idx) => (
                <div key={idx} className="border border-amber-200 rounded-lg p-4">
                  <div className="font-medium text-slate-900 mb-2">
                    {issue.task_name}
                  </div>
                  <div className="text-sm text-amber-700 mb-2">
                    {issue.detail}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    {autoFixTiming ? (
                      <Badge variant="secondary" className="text-emerald-700 bg-emerald-50">
                        将自动修复
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        需手动调整
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* 缺失依赖详情 */}
      {missingIssues.length > 0 && (
        <Card className="mb-6 border border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700">
              <Link2 className="w-5 h-5" />
              缺失依赖详情
              <Badge variant="secondary">{missingIssues.length} 个</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {missingIssues.map((issue, idx) => (
                <div key={idx} className="border border-blue-200 rounded-lg p-4">
                  <div className="font-medium text-slate-900 mb-2">
                    {issue.task_name}
                  </div>
                  <div className="text-sm text-blue-700 mb-2">
                    {issue.detail}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    {autoFixMissing ? (
                      <Badge variant="secondary" className="text-emerald-700 bg-emerald-50">
                        将自动移除
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        需手动删除
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* 其他问题详情 */}
      {otherIssues.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-700">
              <AlertOctagon className="w-5 h-5" />
              其他依赖问题
              <Badge variant="secondary">{otherIssues.length} 个</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {otherIssues.map((issue, idx) => (
                <div 
                  key={idx} 
                  className={`border rounded-lg p-4 ${severityColors[issue.severity] || "border-slate-200"}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="font-medium text-slate-900">
                      {issue.task_name}
                    </div>
                    <Badge variant="secondary" className={severityColors[issue.severity]?.split(" ")[0]}>
                      {issue.severity}
                    </Badge>
                  </div>
                  <div className="text-sm text-slate-700">
                    {issue.detail}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* 无问题状态 */}
      {cycleIssues.length === 0 && timingIssues.length === 0 && 
       missingIssues.length === 0 && otherIssues.length === 0 && (
        <Card className="mb-6">
          <CardContent className="py-12 text-center">
            <CheckCircle2 className="w-16 h-16 mx-auto mb-4 text-emerald-500" />
            <div className="text-xl font-semibold text-slate-900 mb-2">
              恭喜！没有发现依赖问题
            </div>
            <div className="text-slate-600">
              项目的依赖关系配置良好，可以正常执行。
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* 预览对话框 */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              依赖修复预览
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {previewData ? (
              <div className="space-y-6">
                {/* 循环依赖预览 */}
                {previewData.has_cycle && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900 mb-3">循环依赖（需手动处理）</h4>
                    <div className="space-y-2">
                      {previewData.cycle_paths.map((cycle, idx) => (
                        <div key={idx} className="rounded-md bg-red-50 border border-red-200 p-3">
                          <div className="text-sm text-red-800">
                            循环 {idx + 1}: {cycle.join(" → ")}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="rounded-md bg-amber-50 border border-amber-200 p-3 text-sm mt-2">
                      <strong className="text-amber-900">⚠️ 循环依赖无法自动修复，请在修复其他问题后手动调整。</strong>
                    </div>
                  </div>
                )}
                
                {/* 修复操作预览 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">将要执行的修复操作</h4>
                  <div className="space-y-2">
                    {previewData.preview_actions?.will_fix_timing > 0 && (
                      <div className="rounded-md bg-amber-50 border border-amber-200 p-3">
                        <div className="font-medium text-amber-900 mb-1">
                          将修复 {previewData.preview_actions.will_fix_timing} 个时序冲突
                        </div>
                        <div className="text-xs text-amber-700">
                          自动调整任务计划时间以解决时序冲突
                        </div>
                      </div>
                    )}
                    
                    {previewData.preview_actions?.will_remove_missing > 0 && (
                      <div className="rounded-md bg-blue-50 border border-blue-200 p-3">
                        <div className="font-medium text-blue-900 mb-1">
                          将移除 {previewData.preview_actions.will_remove_missing} 个缺失依赖
                        </div>
                        <div className="text-xs text-blue-700">
                          删除指向不存在任务的依赖关系
                        </div>
                      </div>
                    )}
                    
                    {previewData.preview_actions?.will_skip_cycles > 0 && (
                      <div className="rounded-md bg-slate-100 border border-slate-300 p-3">
                        <div className="font-medium text-slate-900 mb-1">
                          跳过 {previewData.preview_actions.will_skip_cycles} 个循环依赖
                        </div>
                        <div className="text-xs text-slate-700">
                          循环依赖需手动处理
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">加载预览数据中...</div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPreviewDialog(false)}>
              取消
            </Button>
            <Button onClick={() => {
              setShowPreviewDialog(false);
              setShowConfirmDialog(true);
            }}>
              确认修复
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* 确认执行对话框 */}
      <Dialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wrench className="w-5 h-5 text-blue-500" />
              确认执行依赖修复
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <p className="text-slate-700">
                确定要执行以下依赖修复操作吗？
              </p>
              
              <div className="rounded-md bg-slate-50 p-4 space-y-2 text-sm">
                {autoFixTiming && (
                  <div className="flex items-center gap-2">
                    <Network className="w-4 h-4 text-amber-500" />
                    <span>自动修复 {timingIssues.length} 个时序冲突</span>
                  </div>
                )}
                
                {autoFixMissing && missingIssues.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Link2 className="w-4 h-4 text-blue-500" />
                    <span>自动移除 {missingIssues.length} 个缺失依赖</span>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>记录所有修复操作到进度日志</span>
                </div>
              </div>
              
              {cycleIssues.length > 0 && (
                <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm">
                  <strong className="text-red-900">⚠️ 注意：</strong>
                  循环依赖无法自动修复，需要手动处理。
                </div>
              )}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfirmDialog(false)}>
              取消
            </Button>
            <Button 
              onClick={handleFixDependencies}
              disabled={processing}
            >
              {processing ? "修复中..." : "确认修复"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
