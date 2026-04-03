import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCw, Eye, Wrench, AlertCircle, CheckCircle2 } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { useProjectDependencyCheck } from "./hooks/useProjectDependencyCheck";
import LoadingState from "./LoadingState";
import AutoFixOptions from "./AutoFixOptions";
import SummaryCards from "./SummaryCards";
import CycleIssuesList from "./CycleIssuesList";
import TimingIssuesList from "./TimingIssuesList";
import MissingIssuesList from "./MissingIssuesList";
import OtherIssuesList from "./OtherIssuesList";
import AllClearState from "./AllClearState";
import PreviewDialog from "./PreviewDialog";
import ConfirmDialog from "./ConfirmDialog";

export default function DependencyCheck({ projectId }) {
  const { id: routeId } = useParams();
  const id = projectId || routeId;
  const navigate = useNavigate();

  const {
    loading,
    project,
    previewData,
    processing,
    errorMessage,
    successMessage,
    cycleIssues,
    timingIssues,
    missingIssues,
    otherIssues,
    autoFixTiming,
    setAutoFixTiming,
    autoFixMissing,
    setAutoFixMissing,
    showPreviewDialog,
    setShowPreviewDialog,
    showConfirmDialog,
    setShowConfirmDialog,
    fetchDependencyCheck,
    handlePreview,
    handleFixDependencies,
  } = useProjectDependencyCheck(id);

  if (loading) return <LoadingState />;

  const hasNoIssues =
    cycleIssues.length === 0 &&
    timingIssues.length === 0 &&
    missingIssues.length === 0 &&
    otherIssues.length === 0;

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

        <AutoFixOptions
          autoFixTiming={autoFixTiming}
          setAutoFixTiming={setAutoFixTiming}
          autoFixMissing={autoFixMissing}
          setAutoFixMissing={setAutoFixMissing}
        />
      </div>

      {/* 概览卡片 */}
      <SummaryCards
        cycleIssues={cycleIssues}
        timingIssues={timingIssues}
        missingIssues={missingIssues}
        otherIssues={otherIssues}
        autoFixTiming={autoFixTiming}
        autoFixMissing={autoFixMissing}
      />

      {/* 问题详情列表 */}
      <CycleIssuesList cycleIssues={cycleIssues} />
      <TimingIssuesList timingIssues={timingIssues} autoFixTiming={autoFixTiming} />
      <MissingIssuesList missingIssues={missingIssues} autoFixMissing={autoFixMissing} />
      <OtherIssuesList otherIssues={otherIssues} />

      {/* 无问题状态 */}
      {hasNoIssues && <AllClearState />}

      {/* 预览对话框 */}
      <PreviewDialog
        open={showPreviewDialog}
        onOpenChange={setShowPreviewDialog}
        previewData={previewData}
        onConfirm={() => {
          setShowPreviewDialog(false);
          setShowConfirmDialog(true);
        }}
      />

      {/* 确认执行对话框 */}
      <ConfirmDialog
        open={showConfirmDialog}
        onOpenChange={setShowConfirmDialog}
        onConfirm={handleFixDependencies}
        processing={processing}
        autoFixTiming={autoFixTiming}
        autoFixMissing={autoFixMissing}
        timingIssues={timingIssues}
        missingIssues={missingIssues}
        cycleIssues={cycleIssues}
      />
    </div>
  );
}
