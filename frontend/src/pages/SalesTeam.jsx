/**
 * Sales Team Management Page - Team performance and management for sales directors
 * 重构版本：使用拆分的子组件和自定义Hooks
 * Features: Team member management, Performance tracking, Target assignment, Team analytics
 */

import { useState, useMemo, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Users,
  UserPlus,
  TrendingUp,
  BarChart3,
  Download } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
} from "../components/ui";
import { salesTeamApi } from "../services/api";
import { fadeIn, staggerContainer } from "../lib/animations";
import { toast } from "sonner";
import { getDefaultDateRange } from "@/lib/constants/salesTeam";
import { useSalesTeamFilters } from "../components/sales/team/hooks/useSalesTeamFilters";
import { useSalesTeamData } from "../components/sales/team/hooks/useSalesTeamData";
import { useSalesTeamRanking } from "../components/sales/team/hooks/useSalesTeamRanking";
import {
  TeamStatsCards,
  TeamFilters,
  TeamRankingBoard,
  TeamMemberList,
  TeamMemberDetailDialog } from
"../components/sales/team";

export default function SalesTeam() {
  const navigate = useNavigate();
  const location = useLocation();
  const defaultRange = useMemo(() => getDefaultDateRange(), []);

  // 根据 URL 路径判断初始显示模式
  const isRankingPath = location.pathname.includes('/ranking');

  // 筛选器状态管理
  const {
    filters,
    activeQuickRange,
    dateError,
    lastAutoRefreshAt,
    highlightAutoRefresh,
    handleFilterChange,
    handleApplyQuickRange,
    handleResetFilters,
    triggerAutoRefreshToast,
    validateDateRange
  } = useSalesTeamFilters(defaultRange);

  // 团队数据获取
  const {
    loading,
    teamMembers,
    teamStats,
    error: dataError,
    departmentOptions,
    regionOptions,
    fetchTeamData
  } = useSalesTeamData(filters, defaultRange, triggerAutoRefreshToast);

  // 排名数据管理
  const [showRanking, setShowRanking] = useState(isRankingPath || true);
  const {
    loading: rankingLoading,
    data: rankingData,
    config: rankingConfig,
    rankingType,
    metricConfigList,
    rankingOptions,
    selectedRankingOption,
    setRankingType
  } = useSalesTeamRanking(filters, showRanking, dateError);

  // 搜索和导出状态
  const [searchTerm, setSearchTerm] = useState("");
  const [exporting, setExporting] = useState(false);

  // 成员详情对话框
  const [selectedMember, setSelectedMember] = useState(null);
  const [showMemberDialog, setShowMemberDialog] = useState(false);

  // 创建团队对话框
  const [showCreateTeamDialog, setShowCreateTeamDialog] = useState(false);
  const [creatingTeam, setCreatingTeam] = useState(false);
  const [createTeamForm, setCreateTeamForm] = useState({
    team_name: "",
    team_code: "",
    team_type: "REGION",
    department_id: "",
    leader_id: "",
    description: "",
  });

  // 从其他页面跳转时，直接打开成员详情
  useEffect(() => {
    const openMember = location.state?.openMember;
    if (!openMember) {return;}
    setSelectedMember(openMember);
    setShowMemberDialog(true);
    // 清理 state，避免刷新/返回时重复弹窗
    navigate(location.pathname, { replace: true, state: {} });
  }, [location.state?.openMember, navigate, location.pathname]);

  // 日期验证
  useEffect(() => {
    validateDateRange();
  }, [filters.startDate, filters.endDate, validateDateRange]);

  // 获取团队数据（依赖筛选条件）
  useEffect(() => {
    if (dateError) {return;}
    fetchTeamData();
  }, [
  filters.departmentId,
  filters.region,
  filters.startDate,
  filters.endDate,
  dateError,
  fetchTeamData]
  );

  // 搜索过滤
  const filteredMembers = useMemo(() => {
    if (!searchTerm) {return teamMembers;}
    const keyword = searchTerm.toLowerCase();
    return (teamMembers || []).filter((member) => {
      const name = member.name?.toLowerCase?.() || "";
      const role = member.role?.toLowerCase?.() || "";
      const regionText = member.region?.toLowerCase?.() || "";
      return (
        name.includes(keyword) ||
        role.includes(keyword) ||
        regionText.includes(keyword));

    });
  }, [teamMembers, searchTerm]);

  // 页面头部描述
  const headerDescription = `团队规模: ${teamStats.totalMembers}人 | 活跃成员: ${teamStats.activeMembers}人 | 平均完成率: ${teamStats.avgAchievementRate}% | 统计区间: ${filters.startDate} ~ ${filters.endDate}`;


  // 导出数据
  const handleExport = async () => {
    if (dataError || dateError) {return;}
    try {
      setExporting(true);
      const params = {};
      // department_id 为 "all" 时不传递该参数（后端期望 Optional[int]）
      if (filters.departmentId && filters.departmentId !== "all") {
        params.department_id = parseInt(filters.departmentId, 10);
      }
      if (filters.region) {params.region = filters.region.trim();}
      if (filters.startDate) {params.start_date = filters.startDate;}
      if (filters.endDate) {params.end_date = filters.endDate;}
      const res = await salesTeamApi.exportTeam(params);
      const blob = new Blob([res.data], { type: "text/csv;charset=utf-8;" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const filename = `sales-team-${(filters.startDate || defaultRange.start).replace(/-/g, "")}-${(filters.endDate || defaultRange.end).replace(/-/g, "")}.csv`;
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("导出销售团队数据失败:", err);
    } finally {
      setExporting(false);
    }
  };

  // 查看成员详情
  const handleViewMember = (member) => {
    setSelectedMember(member);
    setShowMemberDialog(true);
  };

  // 导航到绩效页面
  const handleNavigatePerformance = (member) => {
    if (!member?.id) {return;}
    navigate(`/performance/results/${member.id}`);
  };

  // 导航到CRM页面
  const handleNavigateCRM = (member) => {
    if (!member?.id) {return;}
    navigate(`/sales/customers?owner_id=${member.id}`);
  };

  const resetCreateTeamForm = () => {
    setCreateTeamForm({
      team_name: "",
      team_code: "",
      team_type: "REGION",
      department_id: "",
      leader_id: "",
      description: "",
    });
  };

  const generateTeamCode = () => `TEAM${Date.now().toString().slice(-8)}`;

  const handleCreateTeam = async () => {
    if (!createTeamForm.team_name?.trim()) {
      toast.error("团队名称不能为空");
      return;
    }

    const teamCode = (createTeamForm.team_code || generateTeamCode())
      .toUpperCase()
      .replace(/\s+/g, "")
      .slice(0, 20);

    try {
      setCreatingTeam(true);
      await salesTeamApi.createTeam({
        team_code: teamCode,
        team_name: createTeamForm.team_name.trim(),
        description: createTeamForm.description?.trim() || undefined,
        team_type: createTeamForm.team_type || "REGION",
        department_id: createTeamForm.department_id
          ? Number(createTeamForm.department_id)
          : undefined,
        leader_id: createTeamForm.leader_id
          ? Number(createTeamForm.leader_id)
          : undefined,
      });

      toast.success(`团队创建成功（${teamCode}）`);
      setShowCreateTeamDialog(false);
      resetCreateTeamForm();
      fetchTeamData();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(detail || "创建团队失败");
    } finally {
      setCreatingTeam(false);
    }
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="团队管理"
        description={headerDescription}
        actions={
        <motion.div
          variants={fadeIn}
          className="flex flex-wrap gap-2 justify-end">

            <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={() => setShowRanking(!showRanking)}>

              <BarChart3 className="w-4 h-4" />
              {showRanking ? "隐藏排名" : "业绩排名"}
            </Button>
            <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={handleExport}
            loading={exporting}
            disabled={!!dataError || exporting || !!dateError}>

              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={() => navigate("/performance")}>

              <TrendingUp className="w-4 h-4" />
              绩效中心
            </Button>
            <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={() => navigate("/sales/customers")}>

              <Users className="w-4 h-4" />
              CRM
            </Button>
            <Button
              className="flex items-center gap-2"
              onClick={() => setShowCreateTeamDialog(true)}>
              <UserPlus className="w-4 h-4" />
              新建团队
            </Button>
        </motion.div>
        } />


      {/* 数据加载错误提示 */}
      {dataError && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-xs text-red-400">{dataError}</p>
          <Button
            size="sm"
            variant="ghost"
            className="text-xs text-red-400 hover:text-red-300"
            onClick={() => fetchTeamData()}
          >
            重试
          </Button>
        </div>
      )}

      {/* 筛选器 */}
      <TeamFilters
        filters={filters}
        departmentOptions={departmentOptions}
        regionOptions={regionOptions}
        dateError={dateError}
        onFilterChange={handleFilterChange}
        onQuickRange={handleApplyQuickRange}
        onReset={handleResetFilters}
        activeQuickRange={activeQuickRange}
        lastAutoRefreshAt={lastAutoRefreshAt}
        highlightAutoRefresh={highlightAutoRefresh} />


      {/* 团队统计卡片 */}
      <TeamStatsCards teamStats={teamStats} />

      {/* 业绩排名 */}
      {showRanking &&
      <TeamRankingBoard
        rankingData={rankingData}
        rankingConfig={rankingConfig}
        rankingType={rankingType}
        onRankingTypeChange={setRankingType}
        filters={filters}
        onConfigClick={() => navigate("/sales-director-dashboard")}
        loading={rankingLoading}
        metricConfigList={metricConfigList}
        rankingOptions={rankingOptions}
        selectedRankingOption={selectedRankingOption} />

      }

      {/* 搜索框 */}
      <motion.div variants={fadeIn}>
        <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-700/50">
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="搜索团队成员..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500" />

              <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
          </div>
        </div>
      </motion.div>

      {/* 团队成员列表 */}
      <TeamMemberList
        loading={loading}
        members={filteredMembers}
        onViewDetail={handleViewMember}
        onNavigatePerformance={handleNavigatePerformance}
        onNavigateCRM={handleNavigateCRM} />


      {/* 成员详情对话框 */}
      <TeamMemberDetailDialog
        open={showMemberDialog}
        onOpenChange={setShowMemberDialog}
        member={selectedMember}
        onNavigatePerformance={handleNavigatePerformance}
        onNavigateCRM={handleNavigateCRM} />

      {/* 新建团队对话框 */}
      <Dialog open={showCreateTeamDialog} onOpenChange={setShowCreateTeamDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>新建销售团队</DialogTitle>
            <DialogDescription>创建团队实体，用于目标分配与统计</DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-sm text-slate-300">团队名称 *</label>
              <Input
                placeholder="请输入团队名称"
                value={createTeamForm.team_name}
                onChange={(e) =>
                  setCreateTeamForm((prev) => ({ ...prev, team_name: e.target.value }))
                }
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm text-slate-300">团队编码</label>
              <Input
                placeholder="留空自动生成"
                value={createTeamForm.team_code}
                onChange={(e) =>
                  setCreateTeamForm((prev) => ({ ...prev, team_code: e.target.value }))
                }
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-sm text-slate-300">团队类型</label>
                <select
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white"
                  value={createTeamForm.team_type}
                  onChange={(e) =>
                    setCreateTeamForm((prev) => ({ ...prev, team_type: e.target.value }))
                  }
                >
                  <option value="REGION">按区域</option>
                  <option value="INDUSTRY">按行业</option>
                  <option value="SCALE">按规模</option>
                  <option value="OTHER">其他</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-sm text-slate-300">所属部门</label>
                <select
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white"
                  value={createTeamForm.department_id}
                  onChange={(e) =>
                    setCreateTeamForm((prev) => ({ ...prev, department_id: e.target.value }))
                  }
                >
                  <option value="">不指定</option>
                  {(departmentOptions || [])
                    .filter((d) => d.value !== "all")
                    .map((dept) => (
                      <option key={dept.value} value={dept.value}>
                        {dept.label}
                      </option>
                    ))}
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-sm text-slate-300">负责人</label>
              <select
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white"
                value={createTeamForm.leader_id}
                onChange={(e) =>
                  setCreateTeamForm((prev) => ({ ...prev, leader_id: e.target.value }))
                }
              >
                <option value="">不指定</option>
                {(teamMembers || []).map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.user_name || member.name || `用户${member.user_id}`}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-sm text-slate-300">描述</label>
              <Input
                placeholder="可选"
                value={createTeamForm.description}
                onChange={(e) =>
                  setCreateTeamForm((prev) => ({ ...prev, description: e.target.value }))
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              disabled={creatingTeam}
              onClick={() => {
                setShowCreateTeamDialog(false);
                resetCreateTeamForm();
              }}
            >
              取消
            </Button>
            <Button disabled={creatingTeam} onClick={handleCreateTeam}>
              {creatingTeam ? "创建中..." : "创建团队"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </motion.div>);

}
