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
import { motion } from "framer-motion";
import {
  Users,
  User,
  UserPlus,
  TrendingUp,
  BarChart3,
  Download,
  Building2,
  ChevronRight,
  ChevronDown,
  Briefcase,
} from "lucide-react";
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
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
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
  TeamMemberDetailDialog,
} from "../components/sales/team";

// ============================================
// 组织架构组件 (来自 SalesOrganization.jsx)
// ============================================

// 组织树节点组件
function OrgNode({ node, level, onSelect, selectedId }) {
  const [expanded, setExpanded] = useState(level < 2);

  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.id;

  const getLevelColor = () => {
    const colors = {
      GM: "border-purple-500 bg-purple-500/10",
      Director: "border-blue-500 bg-blue-500/10",
      Manager: "border-green-500 bg-green-500/10",
      Sales: "border-slate-500 bg-slate-500/10",
    };
    return colors[node.level] || colors.Sales;
  };

  const getRateColor = (rate) => {
    if (rate >= 70) return "text-green-500";
    if (rate >= 60) return "text-blue-500";
    if (rate >= 50) return "text-orange-500";
    return "text-red-500";
  };

  return (
    <div className="ml-4">
      <div
        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-all ${getLevelColor()} ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
        onClick={() => onSelect(node)}
      >
        {hasChildren ? (
          <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}>
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        ) : (
          <div className="w-4" />
        )}

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">{node.name}</span>
            <Badge variant="outline" className="text-xs">{node.level}</Badge>
          </div>
          {node.person && (
            <div className="text-xs text-slate-400">{node.person.name} · {node.person.title}</div>
          )}
        </div>

        {node.metrics && (
          <div className="text-right">
            <div className={`text-sm font-bold ${getRateColor(node.metrics.achievement_rate || node.metrics.rate)}`}>
              {node.metrics.achievement_rate || node.metrics.rate}%
            </div>
            {node.metrics.achieved_ytd && (
              <div className="text-xs text-slate-400">
                ¥{(node.metrics.achieved_ytd / 1000000).toFixed(1)}M / ¥{(node.metrics.quota_annual / 1000000).toFixed(0)}M
              </div>
            )}
          </div>
        )}
      </div>

      {expanded && hasChildren && (
        <div className="mt-2 border-l-2 border-slate-700 pl-2">
          {node.children.map((child) => (
            <OrgNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// 组织树视图
function OrganizationTree() {
  const [selectedNode, setSelectedNode] = useState(null);
  const [orgTree, setOrgTree] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadOrg = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await salesTeamApi.getOrg();
        const data = res.formatted || res.data?.data || res.data || {};
        setOrgTree(data.organization_tree || null);
      } catch (err) {
        console.error("加载组织架构失败:", err);
        setError("加载组织架构数据失败，请稍后重试");
        setOrgTree(null);
      } finally {
        setLoading(false);
      }
    };
    loadOrg();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-slate-400">加载组织架构中...</CardContent>
      </Card>
    );
  }

  if (error || !orgTree) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-slate-400">
          {error || "暂无组织架构数据，请先创建销售团队"}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* 组织树 */}
      <Card>
        <CardHeader>
          <CardTitle>销售组织架构</CardTitle>
          <CardDescription>点击节点查看详情，4层层级：总经理 → 总监 → 经理 → 销售</CardDescription>
        </CardHeader>
        <CardContent>
          <OrgNode node={orgTree} level={0} onSelect={setSelectedNode} selectedId={selectedNode?.id} />
        </CardContent>
      </Card>

      {/* 选中节点详情 */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedNode ? (
              <div className="flex items-center gap-2">
                {selectedNode.level === "GM" && <Briefcase className="w-5 h-5 text-purple-500" />}
                {selectedNode.level === "Director" && <Building2 className="w-5 h-5 text-blue-500" />}
                {selectedNode.level === "Manager" && <Users className="w-5 h-5 text-green-500" />}
                {selectedNode.level === "Sales" && <User className="w-5 h-5 text-slate-500" />}
                {selectedNode.name}
              </div>
            ) : (
              "选择节点查看详情"
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedNode ? (
            <div className="space-y-4">
              {selectedNode.person && (
                <div>
                  <div className="text-sm text-slate-400">负责人</div>
                  <div className="font-medium">{selectedNode.person.name} · {selectedNode.person.title}</div>
                </div>
              )}

              {selectedNode.metrics && (
                <>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">业绩完成率</div>
                    <div className="flex items-center gap-3">
                      <span className={`text-3xl font-bold ${(selectedNode.metrics.achievement_rate || selectedNode.metrics.rate) >= 70 ? 'text-green-500' : (selectedNode.metrics.achievement_rate || selectedNode.metrics.rate) >= 60 ? 'text-blue-500' : 'text-orange-500'}`}>
                        {selectedNode.metrics.achievement_rate || selectedNode.metrics.rate}%
                      </span>
                      <Progress value={selectedNode.metrics.achievement_rate || selectedNode.metrics.rate} className="flex-1" />
                    </div>
                  </div>

                  {selectedNode.metrics.achieved_ytd && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-slate-400">已完成</div>
                        <div className="text-lg font-bold">¥{(selectedNode.metrics.achieved_ytd / 1000000).toFixed(1)}M</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400">年度指标</div>
                        <div className="text-lg font-bold">¥{(selectedNode.metrics.quota_annual / 1000000).toFixed(0)}M</div>
                      </div>
                      <div>
                        <div className="text-sm text-slate-400">团队人数</div>
                        <div className="text-lg font-bold">{selectedNode.metrics.team_size}人</div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {selectedNode.children && selectedNode.children.length > 0 && (
                <div>
                  <div className="text-sm text-slate-400 mb-2">下属团队/成员 ({selectedNode.children.length}个)</div>
                  <div className="space-y-2">
                    {selectedNode.children.map((child) => (
                      <div key={child.id} className="p-2 border rounded text-sm">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{child.name}</span>
                          <Badge variant="outline">{child.level}</Badge>
                        </div>
                        {child.metrics && (
                          <div className="text-xs text-slate-400 mt-1">
                            完成率：<span className={(child.metrics.rate || child.metrics.achievement_rate) >= 70 ? 'text-green-500' : (child.metrics.rate || child.metrics.achievement_rate) >= 60 ? 'text-blue-500' : 'text-orange-500'}>{child.metrics.rate || child.metrics.achievement_rate}%</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-slate-400 py-8">
              <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <div>点击左侧组织节点查看详情</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================
// 主页面组件
// ============================================

export default function SalesTeam({ embedded = false }) {
  const navigate = useNavigate();
  const location = useLocation();
  const defaultRange = useMemo(() => getDefaultDateRange(), []);

  // 当前激活的Tab
  const [activeTab, setActiveTab] = useState("organization");

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
    validateDateRange,
  } = useSalesTeamFilters(defaultRange);

  // 团队数据获取
  const {
    loading,
    teamMembers,
    teamStats,
    error: dataError,
    departmentOptions,
    regionOptions,
    fetchTeamData,
  } = useSalesTeamData(filters, defaultRange, triggerAutoRefreshToast);

  // 排名数据管理
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
    if (!openMember) return;
    setSelectedMember(openMember);
    setShowMemberDialog(true);
    setActiveTab("members");
    navigate(location.pathname, { replace: true, state: {} });
  }, [location.state?.openMember, navigate, location.pathname]);

  // 日期验证
  useEffect(() => {
    validateDateRange();
  }, [filters.startDate, filters.endDate, validateDateRange]);

  // 获取团队数据
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

  // 搜索过滤
  const filteredMembers = useMemo(() => {
    if (!searchTerm) return teamMembers;
    const keyword = searchTerm.toLowerCase();
    return (teamMembers || []).filter((member) => {
      const name = member.name?.toLowerCase?.() || "";
      const role = member.role?.toLowerCase?.() || "";
      const regionText = member.region?.toLowerCase?.() || "";
      return name.includes(keyword) || role.includes(keyword) || regionText.includes(keyword);
    });
  }, [teamMembers, searchTerm]);

  // 页面头部描述
  const headerDescription = `团队规模: ${teamStats.totalMembers}人 | 活跃成员: ${teamStats.activeMembers}人 | 平均完成率: ${teamStats.avgAchievementRate}%`;

  // 导出数据
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

  // 查看成员详情
  const handleViewMember = (member) => {
    setSelectedMember(member);
    setShowMemberDialog(true);
  };

  // 导航到绩效页面
  const handleNavigatePerformance = (member) => {
    if (!member?.id) return;
    navigate(`/performance/results/${member.id}`);
  };

  // 导航到CRM页面
  const handleNavigateCRM = (member) => {
    if (!member?.id) return;
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

      {/* 主内容区：三个Tab视角 */}
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

        {/* Tab 1: 组织架构 */}
        <TabsContent value="organization" className="mt-6">
          <OrganizationTree />

          {/* 层级定义说明 */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>销售组织层级定义</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-4">
                {[
                  { level: "L1", name: "销售总经理", code: "GM", scope: "全公司", report: "CEO", manage: "所有总监" },
                  { level: "L2", name: "销售总监", code: "Director", scope: "分公司", report: "销售总经理", manage: "2-3 个经理" },
                  { level: "L3", name: "销售经理", code: "Manager", scope: "销售团队", report: "销售总监", manage: "3-5 人" },
                  { level: "L4", name: "销售", code: "Sales", scope: "个人", report: "销售经理", manage: "-" },
                ].map((item) => (
                  <Card key={item.level}>
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline">{item.level}</Badge>
                        <span className="font-medium">{item.name}</span>
                      </div>
                      <div className="text-sm text-slate-400 space-y-1">
                        <div>范围：{item.scope}</div>
                        <div>汇报：{item.report}</div>
                        <div>管理：{item.manage}</div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: 成员列表 */}
        <TabsContent value="members" className="mt-6 space-y-6">
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
            highlightAutoRefresh={highlightAutoRefresh}
          />

          {/* 团队统计卡片 */}
          <TeamStatsCards teamStats={teamStats} />

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
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
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
            onNavigateCRM={handleNavigateCRM}
          />
        </TabsContent>

        {/* Tab 3: 业绩排行 */}
        <TabsContent value="ranking" className="mt-6 space-y-6">
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
            highlightAutoRefresh={highlightAutoRefresh}
          />

          {/* 业绩排名 */}
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

      {/* 成员详情对话框 */}
      <TeamMemberDetailDialog
        open={showMemberDialog}
        onOpenChange={setShowMemberDialog}
        member={selectedMember}
        onNavigatePerformance={handleNavigatePerformance}
        onNavigateCRM={handleNavigateCRM}
      />

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
    </motion.div>
  );
}
