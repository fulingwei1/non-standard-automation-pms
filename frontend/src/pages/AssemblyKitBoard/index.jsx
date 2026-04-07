/**
 * Assembly Kit Board Page - 装配齐套看板页面
 * Features: 6阶段进度可视化、齐套率分布、缺料预警、排产建议
 */
import { useState, useEffect } from "react";




import { projectApi } from "../../services/api";
import { assemblyKitApi } from "../../services/api/production";


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
        alert(`已生成 ${res.data.suggestions?.length} 条排产建议`);
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
          <Select value={filterProject || "unknown"} onValueChange={setFilterProject}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="选择项目" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部项目</SelectItem>
              {(projects || []).map((proj) =>
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
      <StatisticsCards stats={stats} />

      {/* 6-Stage Progress Visualization */}
      <StageProgress stageStats={stageStats} />

      {/* Alert Summary */}
      <AlertSummary alertSummary={alertSummary} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Analyses */}
        <RecentAnalyses
          recentAnalyses={recentAnalyses}
          onViewDetail={fetchAnalysisDetail}
        />

        {/* Pending Suggestions */}
        <PendingSuggestions
          pendingSuggestions={pendingSuggestions}
          onAccept={handleAcceptSuggestion}
          onReject={(suggestion) => {
            setSelectedSuggestion(suggestion);
            setRejectDialogOpen(true);
          }}
        />
      </div>

      {/* Shortage Alerts List */}
      <ShortageAlerts alerts={alerts} />

      {/* Analysis Detail Dialog */}
      <AnalysisDetailDialog
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        analysisDetail={analysisDetail}
      />

      {/* Reject Suggestion Dialog */}
      <RejectDialog
        open={rejectDialogOpen}
        onOpenChange={setRejectDialogOpen}
        rejectReason={rejectReason}
        onRejectReasonChange={setRejectReason}
        onConfirm={handleRejectSuggestion}
      />
    </div>);

}
