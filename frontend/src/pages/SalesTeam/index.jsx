/**
 * 团队管理页面 - 统一入口
 * 整合：组织架构 + 成员列表 + 业绩排行
 *
 * Tab 1: 组织架构 - 4层层级树形结构展示
 * Tab 2: 成员列表 - 扁平化团队成员管理
 * Tab 3: 业绩排行 - 业绩榜单与排名
 */

import { useState, useMemo, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";




import { salesTeamApi } from "../../services/api";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { getDefaultDateRange } from "@/lib/constants/salesTeam";
import { useSalesTeamFilters } from "../../components/sales/team/hooks/useSalesTeamFilters";
import { useSalesTeamData } from "../../components/sales/team/hooks/useSalesTeamData";
import { useSalesTeamRanking } from "../../components/sales/team/hooks/useSalesTeamRanking";



import { filterMembersBySearch } from "./utils";

export default function SalesTeam({ embedded = false }) {
  const navigate = useNavigate();
  const location = useLocation();
  const defaultRange = useMemo(() => getDefaultDateRange(), []);

  // Current active tab
  const [activeTab, setActiveTab] = useState("organization");

  // Filter state management
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
    validateDateRange,
  } = useSalesTeamFilters(defaultRange);

  // Team data fetching
  const {
    loading,
    teamMembers,
    teamStats,
    error: dataError,
    departmentOptions,
    regionOptions,
    fetchTeamData,
  } = useSalesTeamData(filters, defaultRange, triggerAutoRefreshToast);

  // Ranking data management
  const {
    loading: rankingLoading,
    data: rankingData,
    config: rankingConfig,
    rankingType,
    metricConfigList,
    rankingOptions,
    selectedRankingOption,
    setRankingType,
  } = useSalesTeamRanking(filters, true, dateError);

  // Search and export state
  const [searchTerm, setSearchTerm] = useState("");
  const [exporting, setExporting] = useState(false);

  // Member detail dialog
  const [selectedMember, setSelectedMember] = useState(null);
  const [showMemberDialog, setShowMemberDialog] = useState(false);

  // Create team dialog
  const [showCreateTeamDialog, setShowCreateTeamDialog] = useState(false);

  // Open member detail when navigating from another page
  useEffect(() => {
    const openMember = location.state?.openMember;
    if (!openMember) return;
    setSelectedMember(openMember);
    setShowMemberDialog(true);
    setActiveTab("members");
    navigate(location.pathname, { replace: true, state: {} });
  }, [location.state?.openMember, navigate, location.pathname]);

  // Date validation
  useEffect(() => {
    validateDateRange();
  }, [filters.startDate, filters.endDate, validateDateRange]);

  // Fetch team data
  useEffect(() => {
    if (dateError) return;
    fetchTeamData();
  }, [
    filters.departmentId,
    filters.region,
    filters.startDate,
    filters.endDate,
    dateError,
    fetchTeamData,
  ]);

  // Search filter
  const filteredMembers = useMemo(
    () => filterMembersBySearch(teamMembers, searchTerm),
    [teamMembers, searchTerm]
  );

  // Page header description
  const headerDescription = `团队规模: ${teamStats.totalMembers}人 | 活跃成员: ${teamStats.activeMembers}人 | 平均完成率: ${teamStats.avgAchievementRate}%`;

  // Export data
  const handleExport = async () => {
    if (dataError || dateError) return;
    try {
      setExporting(true);
      const params = {};
      if (filters.departmentId && filters.departmentId !== "all") {
        params.department_id = parseInt(filters.departmentId, 10);
      }
      if (filters.region) params.region = filters.region.trim();
      if (filters.startDate) params.start_date = filters.startDate;
      if (filters.endDate) params.end_date = filters.endDate;
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

  // View member detail
  const handleViewMember = (member) => {
    setSelectedMember(member);
    setShowMemberDialog(true);
  };

  // Navigate to performance page
  const handleNavigatePerformance = (member) => {
    if (!member?.id) return;
    navigate(`/performance/results/${member.id}`);
  };

  // Navigate to CRM page
  const handleNavigateCRM = (member) => {
    if (!member?.id) return;
    navigate(`/sales/customers?owner_id=${member.id}`);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      {!embedded ? (
        <PageHeader
          title="团队管理"
          description={headerDescription}
          actions={
            <motion.div variants={fadeIn} className="flex flex-wrap gap-2 justify-end">
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={handleExport}
                loading={exporting}
                disabled={!!dataError || exporting || !!dateError}
              >
                <Download className="w-4 h-4" />
                导出
              </Button>
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => navigate("/performance")}
              >
                <TrendingUp className="w-4 h-4" />
                绩效中心
              </Button>
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => navigate("/sales/customers")}
              >
                <Users className="w-4 h-4" />
                CRM
              </Button>
              <Button
                className="flex items-center gap-2"
                onClick={() => setShowCreateTeamDialog(true)}
              >
                <UserPlus className="w-4 h-4" />
                新建团队
              </Button>
            </motion.div>
          }
        />
      ) : null}

      {/* Data loading error */}
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

      {/* Main content: three tab views */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3 lg:w-[500px]">
          <TabsTrigger value="organization" className="flex items-center gap-2">
            <Building2 className="w-4 h-4" />
            组织架构
          </TabsTrigger>
          <TabsTrigger value="members" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            成员列表
          </TabsTrigger>
          <TabsTrigger value="ranking" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            业绩排行
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Organization */}
        <TabsContent value="organization" className="mt-6">
          <OrganizationTree />
          <OrgHierarchyCard />
        </TabsContent>

        {/* Tab 2: Members */}
        <TabsContent value="members" className="mt-6 space-y-6">
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
            highlightAutoRefresh={highlightAutoRefresh}
          />

          <TeamStatsCards teamStats={teamStats} />

          {/* Search box */}
          <motion.div variants={fadeIn}>
            <div className="p-4 bg-slate-900/40 rounded-lg border border-slate-700/50">
              <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    placeholder="搜索团队成员..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                </div>
              </div>
            </div>
          </motion.div>

          <TeamMemberList
            loading={loading}
            members={filteredMembers}
            onViewDetail={handleViewMember}
            onNavigatePerformance={handleNavigatePerformance}
            onNavigateCRM={handleNavigateCRM}
          />
        </TabsContent>

        {/* Tab 3: Ranking */}
        <TabsContent value="ranking" className="mt-6 space-y-6">
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
            highlightAutoRefresh={highlightAutoRefresh}
          />

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
            selectedRankingOption={selectedRankingOption}
          />
        </TabsContent>
      </Tabs>

      {/* Member detail dialog */}
      <TeamMemberDetailDialog
        open={showMemberDialog}
        onOpenChange={setShowMemberDialog}
        member={selectedMember}
        onNavigatePerformance={handleNavigatePerformance}
        onNavigateCRM={handleNavigateCRM}
      />

      {/* Create team dialog */}
      <CreateTeamDialog
        open={showCreateTeamDialog}
        onOpenChange={setShowCreateTeamDialog}
        departmentOptions={departmentOptions}
        teamMembers={teamMembers}
        onTeamCreated={fetchTeamData}
      />
    </motion.div>
  );
}
