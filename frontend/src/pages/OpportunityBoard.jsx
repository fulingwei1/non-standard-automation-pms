/**
 * Opportunity Board Page - Sales pipeline kanban view (Refactored)
 * Features: Stage columns, drag-and-drop, opportunity cards, funnel visualization
 */

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Plus,
  LayoutGrid,
  List,
  AlertTriangle,
  Flame,
  TrendingUp,
  BarChart3,
  Trash2 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui";
import { cn } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import { OpportunityCard, SalesFunnel } from "../components/sales";
import { opportunityApi, salesStatisticsApi } from "../services/api";

// 导入重构后的组件
import {
  OpportunityBoardOverview,
  OPPORTUNITY_STAGES,
  OPPORTUNITY_STAGE_CONFIGS,
  OPPORTUNITY_PRIORITY,
  OPPORTUNITY_PRIORITY_CONFIGS,
  SALES_SOURCE,
  SALES_SOURCE_CONFIGS,
  OPPORTUNITY_TYPE,
  OPPORTUNITY_TYPE_CONFIGS,
  OpportunityUtils } from
"../components/opportunity-board";

// 阶段映射函数
import { confirmAction } from "@/lib/confirmAction";
import { Eye } from "lucide-react";
const mapStageToFrontend = (backendStage) => {
  const config = OpportunityUtils.getStageConfig(backendStage);
  return config?.frontendKey || "lead";
};

export default function OpportunityBoard() {
  const [viewMode, setViewMode] = useState("board"); // 'board', 'list', 'funnel', 'overview'
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedPriority, setSelectedPriority] = useState("all");
  const [selectedOwner, setSelectedOwner] = useState("all");
  const [selectedSource, setSelectedSource] = useState("all");
  const [selectedType, setSelectedType] = useState("all");
  const [showHotOnly, setShowHotOnly] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [hideLost, setHideLost] = useState(true);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [owners, setOwners] = useState([]);
  const [_statistics, setStatistics] = useState(null);

  // Form states
  const [newOpportunity, setNewOpportunity] = useState({
    name: "",
    customerId: "",
    expectedAmount: "",
    expectedCloseDate: "",
    stage: OPPORTUNITY_STAGES.DISCOVERY,
    priority: OPPORTUNITY_PRIORITY.MEDIUM,
    source: SALES_SOURCE.WEBSITE,
    type: OPPORTUNITY_TYPE.NEW_BUSINESS,
    description: "",
    ownerId: ""
  });

  // Load opportunities from API
  const loadOpportunities = async () => {
    setLoading(true);
    try {
      const response = await opportunityApi.list({ page: 1, page_size: 1000 });
      const data = response.data?.items || response.data || [];

      // 转换数据格式
      const transformedOpps = data.map((opp) => {
        // 计算在当前阶段的停留天数
        const stageChangedAt =
        opp.gate_passed_at || opp.updated_at || opp.created_at;
        const daysInStage = stageChangedAt ?
        Math.floor(
          (new Date() - new Date(stageChangedAt)) / (1000 * 60 * 60 * 24)
        ) :
        0;

        // 根据评分和阶段判断是否为热门商机
        const isHot =
        (opp.score || 0) >= 70 ||
        opp.stage === "PROPOSAL" ||
        opp.stage === "NEGOTIATION";

        // 根据风险等级确定优先级
        const priorityMap = {
          HIGH: OPPORTUNITY_PRIORITY.HIGH,
          MEDIUM: OPPORTUNITY_PRIORITY.MEDIUM,
          LOW: OPPORTUNITY_PRIORITY.LOW
        };
        const priority = priorityMap[opp.risk_level] || OPPORTUNITY_PRIORITY.MEDIUM;

        // 计算成交概率（基于阶段）
        const stageConf = OpportunityUtils.getStageConfig(opp.stage);
        const probability = stageConf?.probability || 0;

        return {
          id: opp.id,
          opp_code: opp.opp_code,
          name: opp.opp_name || "",
          customerName: opp.customer_name || "",
          customerShort: opp.customer_name || "",
          customerId: opp.customer_id,
          stage: mapStageToFrontend(opp.stage),
          backendStage: opp.stage,
          expectedAmount: parseFloat(opp.est_amount || 0),
          probability: probability,
          owner: opp.owner_name || opp.owner_id?.toString() || "",
          ownerId: opp.owner_id,
          isHot: isHot,
          priority: priority,
          daysInStage: daysInStage,
          score: opp.score || 0,
          source: opp.source || SALES_SOURCE.OTHER,
          type: opp.type || OPPORTUNITY_TYPE.NEW_BUSINESS,
          expectedCloseDate: opp.expected_close_date,
          createdDate: opp.created_at,
          description: opp.description || "",
          contactName: opp.contact_name || "",
          contactPhone: opp.contact_phone || "",
          contactEmail: opp.contact_email || "",
          nextAction: opp.next_action || "",
          nextActionDate: opp.next_action_date,
          competition: opp.competition || "",
          riskLevel: opp.risk_level || "MEDIUM",
          winProbability: opp.win_probability || probability,
          products: opp.products || [],
          tags: opp.tags || [],
          activities: opp.activities || [],
          documents: opp.documents || []
        };
      });

      // 提取所有负责人
      const uniqueOwners = [
      ...new Set(transformedOpps.map((opp) => opp.ownerId).filter(Boolean))].
      map((ownerId) => {
        const opp = transformedOpps.find((o) => o.ownerId === ownerId);
        return { id: ownerId, name: opp?.owner || "未知" };
      });

      setOpportunities(transformedOpps);
      setOwners(uniqueOwners);
    } catch (err) {
      console.error("Failed to load opportunities:", err);
      setOpportunities([]);
      setOwners([]);
    } finally {
      setLoading(false);
    }
  };

  // Load statistics
  const loadStatistics = async () => {
    try {
      const response = await salesStatisticsApi.getPipelineStats();
      setStatistics(response.data);
    } catch (err) {
      console.error("Failed to load statistics:", err);
      setStatistics(null);
    }
  };

  // Initial load
  useEffect(() => {
    loadOpportunities();
    loadStatistics();
  }, []);

  // Filter opportunities
  const filteredOpportunities = useMemo(() => {
    return OpportunityUtils.filterOpportunities(opportunities, {
      searchQuery: searchTerm,
      priority: selectedPriority,
      source: selectedSource,
      type: selectedType,
      showHotOnly: showHotOnly,
      hideLost: hideLost
    });
  }, [opportunities, searchTerm, selectedPriority, selectedSource, selectedType, showHotOnly, hideLost]);

  // Group by stage for board view
  const groupedOpportunities = useMemo(() => {
    return OpportunityUtils.groupByStage(filteredOpportunities);
  }, [filteredOpportunities]);

  // Sort opportunities for list view
  const sortedOpportunities = useMemo(() => {
    return [...filteredOpportunities].sort((a, b) => {
      // 优先显示热门机会
      if (a.isHot && !b.isHot) {return -1;}
      if (!a.isHot && b.isHot) {return 1;}

      // 按评分排序
      return b.score - a.score;
    });
  }, [filteredOpportunities]);

  // Funnel data
  const funnelData = useMemo(() => {
    return OpportunityUtils.generateFunnelData(filteredOpportunities);
  }, [filteredOpportunities]);

  // Sales forecast
  const _salesForecast = useMemo(() => {
    return OpportunityUtils.generateSalesForecast(filteredOpportunities);
  }, [filteredOpportunities]);

  // Event handlers
  const handleOpportunityClick = (opportunity) => {
    setSelectedOpportunity(opportunity);
    setShowDetailDialog(true);
  };

  const handleCreateOpportunity = async () => {
    try {
      const errors = OpportunityUtils.validateOpportunity(newOpportunity);
      if (errors.length > 0) {
        alert(errors.join("\n"));
        return;
      }

      const opportunityData = {
        ...newOpportunity,
        expectedAmount: parseFloat(newOpportunity.expectedAmount),
        stage: OPPORTUNITY_STAGES.DISCOVERY, // New opportunities start at discovery
        score: 0 // Will be calculated by backend
      };

      await opportunityApi.create(opportunityData);
      setShowCreateDialog(false);
      setNewOpportunity({
        name: "",
        customerId: "",
        expectedAmount: "",
        expectedCloseDate: "",
        stage: OPPORTUNITY_STAGES.DISCOVERY,
        priority: OPPORTUNITY_PRIORITY.MEDIUM,
        source: SALES_SOURCE.WEBSITE,
        type: OPPORTUNITY_TYPE.NEW_BUSINESS,
        description: "",
        ownerId: ""
      });
      loadOpportunities();
    } catch (err) {
      console.error("Failed to create opportunity:", err);
      alert("创建销售机会失败");
    }
  };

  const _handleUpdateOpportunity = async (updates) => {
    try {
      await opportunityApi.update(selectedOpportunity.id, updates);
      setShowDetailDialog(false);
      setSelectedOpportunity(null);
      loadOpportunities();
    } catch (err) {
      console.error("Failed to update opportunity:", err);
      alert("更新销售机会失败");
    }
  };

  const handleDeleteOpportunity = async () => {
    if (!await confirmAction("确定要删除这个销售机会吗？")) {return;}

    try {
      await opportunityApi.delete(selectedOpportunity.id);
      setShowDetailDialog(false);
      setSelectedOpportunity(null);
      loadOpportunities();
    } catch (err) {
      console.error("Failed to delete opportunity:", err);
      alert("删除销售机会失败");
    }
  };

  const handleStageChange = async (opportunity, newStage) => {
    try {
      await opportunityApi.updateStage(opportunity.id, newStage);
      loadOpportunities();
    } catch (err) {
      console.error("Failed to update stage:", err);
      alert("更新销售阶段失败");
    }
  };

  // Loading state
  if (loading && opportunities.length === 0) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4" />
          <p className="text-text-secondary">加载销售机会...</p>
        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title="销售机会看板"
        description="管理和跟踪销售机会，分析销售漏斗和预测收入" />


      <div className="container mx-auto px-4 py-6">
        {/* View Mode Tabs */}
        <div className="flex border-b border-border mb-6">
          {[
          { key: "board", label: "看板视图", icon: LayoutGrid },
          { key: "overview", label: "概览统计", icon: BarChart3 },
          { key: "funnel", label: "销售漏斗", icon: TrendingUp },
          { key: "list", label: "列表视图", icon: List }].
          map(({ key, label, icon: Icon }) =>
          <button
            key={key}
            onClick={() => setViewMode(key)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 border-b-2 transition-colors",
              viewMode === key ?
              "border-accent text-accent" :
              "border-transparent text-text-secondary hover:text-white"
            )}>

              <Icon className="w-4 h-4" />
              {label}
          </button>
          )}
        </div>

        {/* Controls Section */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeIn}
          className="bg-surface-1 rounded-xl border border-border p-4 mb-6">

          <div className="flex flex-col lg:flex-row gap-4 items-center justify-between">
            {/* Search and Filters */}
            <div className="flex-1 flex flex-col lg:flex-row gap-2 items-center">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
                <Input
                  placeholder="搜索机会名称、客户..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-surface-2 border-border" />

              </div>

              <div className="flex gap-2 flex-wrap">
                <Select value={selectedPriority} onValueChange={setSelectedPriority}>
                  <SelectTrigger className="w-32 bg-surface-2 border-border">
                    <SelectValue placeholder="优先级" />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-2 border-border">
                    <SelectItem value="all">全部优先级</SelectItem>
                    {Object.entries(OPPORTUNITY_PRIORITY_CONFIGS).map(([key, config]) =>
                    <SelectItem key={key} value={key}>
                        {config.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>

                <Select value={selectedSource} onValueChange={setSelectedSource}>
                  <SelectTrigger className="w-32 bg-surface-2 border-border">
                    <SelectValue placeholder="来源" />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-2 border-border">
                    <SelectItem value="all">全部来源</SelectItem>
                    {Object.entries(SALES_SOURCE_CONFIGS).map(([key, config]) =>
                    <SelectItem key={key} value={key}>
                        {config.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>

                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger className="w-32 bg-surface-2 border-border">
                    <SelectValue placeholder="类型" />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-2 border-border">
                    <SelectItem value="all">全部类型</SelectItem>
                    {Object.entries(OPPORTUNITY_TYPE_CONFIGS).map(([key, config]) =>
                    <SelectItem key={key} value={key}>
                        {config.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>

                <Select value={selectedOwner} onValueChange={setSelectedOwner}>
                  <SelectTrigger className="w-32 bg-surface-2 border-border">
                    <SelectValue placeholder="负责人" />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-2 border-border">
                    <SelectItem value="all">全部负责人</SelectItem>
                    {owners.map((owner) =>
                    <SelectItem key={owner.id} value={owner.id}>
                        {owner.name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* View Options and Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant={showHotOnly ? "default" : "outline"}
                size="sm"
                onClick={() => setShowHotOnly(!showHotOnly)}
                className="flex items-center gap-1">

                <Flame className={cn("w-4 h-4", showHotOnly && "text-amber-400")} />
                热门
              </Button>
              <Button
                variant={!hideLost ? "default" : "outline"}
                size="sm"
                onClick={() => setHideLost(!hideLost)}>

                {hideLost ? "显示输单" : "隐藏输单"}
              </Button>
              <Button
                onClick={() => setShowCreateDialog(true)}
                className="bg-accent hover:bg-accent/90">

                <Plus className="w-4 h-4 mr-2" />
                新建机会
              </Button>
            </div>
          </div>
        </motion.div>

        {/* Content */}
        <motion.div variants={fadeIn}>
          {viewMode === "overview" &&
          <OpportunityBoardOverview opportunities={filteredOpportunities} />
          }

          {viewMode === "board" &&
          <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
              {Object.values(OPPORTUNITY_STAGE_CONFIGS).
            filter((s) => !hideLost || s.frontendKey !== "lost").
            map((stage) => {
              const stageOpps = groupedOpportunities[stage.frontendKey] || [];
              const stageTotal = stageOpps.reduce(
                (sum, o) => sum + (o.expectedAmount || 0),
                0
              );

              return (
                <div key={stage.key} className="flex-shrink-0 w-80">
                      {/* Column Header */}
                      <div className="flex items-center justify-between mb-3 p-3 bg-surface-1 rounded-lg">
                        <div className="flex items-center gap-2">
                          <div
                        className={cn("w-3 h-3 rounded-full", stage.color)} />

                          <span className="font-medium text-white">
                            {stage.label}
                          </span>
                          <Badge variant="secondary" className="text-xs">
                            {stageOpps.length}
                          </Badge>
                        </div>
                        <span className="text-xs text-slate-400">
                          ¥{(stageTotal / 10000).toFixed(0)}万
                        </span>
                      </div>

                      {/* Column Content */}
                      <div className="space-y-3 min-h-[200px]">
                        {stageOpps.map((opportunity) =>
                    <OpportunityCard
                      key={opportunity.id}
                      opportunity={opportunity}
                      onClick={handleOpportunityClick}
                      draggable
                      onDragEnd={(newStage) => {
                        // Handle drag end to change stage
                        handleStageChange(opportunity, newStage);
                      }} />

                    )}
                      </div>
                </div>);

            })}
          </div>
          }

          {viewMode === "funnel" &&
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SalesFunnel data={funnelData} />
              <Card className="bg-surface-1 border-border">
                <CardHeader>
                  <CardTitle className="text-white">转化分析</CardTitle>
                </CardHeader>
                <CardContent>
                  {/* Conversion analysis content */}
                  <div className="space-y-4">
                    {funnelData.slice(0, -1).map((stage, index) => {
                    const nextStage = funnelData[index + 1];
                    const conversionRate = stage.count > 0 ?
                    ((nextStage?.count || 0) / stage.count * 100).toFixed(1) :
                    0;

                    return (
                      <div key={stage.stage} className="flex items-center justify-between">
                          <span className="text-sm text-white">
                            {stage.label} → {nextStage?.label || "完成"}
                          </span>
                          <div className="flex items-center gap-2">
                            <div className="w-32 bg-surface-2 rounded-full h-2">
                              <div
                              className="bg-accent h-2 rounded-full"
                              style={{ width: `${conversionRate}%` }} />

                            </div>
                            <span className="text-sm text-white font-medium">
                              {conversionRate}%
                            </span>
                          </div>
                      </div>);

                  })}
                  </div>
                </CardContent>
              </Card>
          </div>
          }

          {viewMode === "list" &&
          <div className="bg-surface-1 rounded-xl border border-border">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-surface-2 border-b border-border">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">机会名称</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">客户</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">阶段</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary">预期金额</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">负责人</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">优先级</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {sortedOpportunities.map((opportunity) =>
                  <tr key={opportunity.id} className="hover:bg-surface-2/50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {opportunity.isHot &&
                        <Flame className="w-3 h-3 text-amber-400" />
                        }
                            <span className="text-sm text-white font-medium">
                              {opportunity.name}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-white">
                          {opportunity.customerName}
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                        variant="outline"
                        className={cn(
                          "text-xs",
                          OpportunityUtils.getStageConfig(opportunity.stage).textColor
                        )}>

                            {OpportunityUtils.getStageConfig(opportunity.stage).label}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-white">
                          ¥{OpportunityUtils.formatCurrency(opportunity.expectedAmount)}
                        </td>
                        <td className="px-4 py-3 text-sm text-white">
                          {opportunity.owner}
                        </td>
                        <td className="px-4 py-3">
                          <Badge
                        variant="outline"
                        className={cn(
                          "text-xs",
                          OpportunityUtils.getPriorityConfig(opportunity.priority).color
                        )}>

                            {OpportunityUtils.getPriorityConfig(opportunity.priority).label}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpportunityClick(opportunity)}>

                            <Eye className="w-4 h-4" />
                          </Button>
                        </td>
                  </tr>
                  )}
                  </tbody>
                </table>
              </div>
          </div>
          }
        </motion.div>

        {/* Create Opportunity Modal */}
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-surface-1 border-border">
            <DialogHeader>
              <DialogTitle className="text-white">创建销售机会</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">机会名称 *</label>
                  <Input
                    value={newOpportunity.name}
                    onChange={(e) => setNewOpportunity({ ...newOpportunity, name: e.target.value })}
                    placeholder="输入机会名称"
                    className="bg-surface-2 border-border" />

                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">客户 *</label>
                  <Input
                    value={newOpportunity.customerId}
                    onChange={(e) => setNewOpportunity({ ...newOpportunity, customerId: e.target.value })}
                    placeholder="选择客户"
                    className="bg-surface-2 border-border" />

                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">预期金额 *</label>
                  <Input
                    type="number"
                    value={newOpportunity.expectedAmount}
                    onChange={(e) => setNewOpportunity({ ...newOpportunity, expectedAmount: e.target.value })}
                    placeholder="输入金额"
                    className="bg-surface-2 border-border" />

                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">预期成交日期 *</label>
                  <Input
                    type="date"
                    value={newOpportunity.expectedCloseDate}
                    onChange={(e) => setNewOpportunity({ ...newOpportunity, expectedCloseDate: e.target.value })}
                    className="bg-surface-2 border-border" />

                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">优先级</label>
                  <Select
                    value={newOpportunity.priority}
                    onValueChange={(value) => setNewOpportunity({ ...newOpportunity, priority: value })}>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {Object.entries(OPPORTUNITY_PRIORITY_CONFIGS).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">来源</label>
                  <Select
                    value={newOpportunity.source}
                    onValueChange={(value) => setNewOpportunity({ ...newOpportunity, source: value })}>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {Object.entries(SALES_SOURCE_CONFIGS).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">类型</label>
                  <Select
                    value={newOpportunity.type}
                    onValueChange={(value) => setNewOpportunity({ ...newOpportunity, type: value })}>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {Object.entries(OPPORTUNITY_TYPE_CONFIGS).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm text-text-secondary mb-1 block">负责人</label>
                  <Select
                    value={newOpportunity.ownerId}
                    onValueChange={(value) => setNewOpportunity({ ...newOpportunity, ownerId: value })}>

                    <SelectTrigger className="bg-surface-2 border-border">
                      <SelectValue placeholder="选择负责人" />
                    </SelectTrigger>
                    <SelectContent className="bg-surface-2 border-border">
                      {owners.map((owner) =>
                      <SelectItem key={owner.id} value={owner.id}>
                          {owner.name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm text-text-secondary mb-1 block">描述</label>
                <textarea
                  value={newOpportunity.description}
                  onChange={(e) => setNewOpportunity({ ...newOpportunity, description: e.target.value })}
                  placeholder="描述销售机会详情..."
                  rows={3}
                  className="w-full bg-surface-2 border border-border rounded-lg p-2 text-white" />

              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                className="bg-surface-2 border-border">

                取消
              </Button>
              <Button
                onClick={handleCreateOpportunity}
                className="bg-accent hover:bg-accent/90">

                创建机会
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Opportunity Detail Modal */}
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-surface-1 border-border">
            {selectedOpportunity &&
            <>
                <DialogHeader>
                  <DialogTitle className="text-white">{selectedOpportunity.name}</DialogTitle>
                </DialogHeader>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Basic Information */}
                  <div className="space-y-4">
                    <Card className="bg-surface-2 border-border">
                      <CardHeader>
                        <CardTitle className="text-sm text-white">基本信息</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-text-secondary">客户</span>
                          <span className="text-white">{selectedOpportunity.customerName}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">预期金额</span>
                          <span className="text-white font-semibold">
                            ¥{OpportunityUtils.formatCurrency(selectedOpportunity.expectedAmount)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">预期成交日期</span>
                          <span className="text-white">
                            {OpportunityUtils.formatDate(selectedOpportunity.expectedCloseDate)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">当前阶段</span>
                          <Badge className={OpportunityUtils.getStageConfig(selectedOpportunity.stage).color}>
                            {OpportunityUtils.getStageConfig(selectedOpportunity.stage).label}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">优先级</span>
                          <Badge variant="outline">
                            {OpportunityUtils.getPriorityConfig(selectedOpportunity.priority).label}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">机会评分</span>
                          <span className="text-white font-semibold">{selectedOpportunity.score}分</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Status and Actions */}
                  <div className="space-y-4">
                    <Card className="bg-surface-2 border-border">
                      <CardHeader>
                        <CardTitle className="text-sm text-white">状态信息</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-text-secondary">负责人</span>
                          <span className="text-white">{selectedOpportunity.owner}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">创建时间</span>
                          <span className="text-white">
                            {OpportunityUtils.formatDate(selectedOpportunity.createdDate)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-secondary">在当前阶段</span>
                          <span className="text-white">{selectedOpportunity.daysInStage}天</span>
                        </div>
                        {selectedOpportunity.nextActionDate &&
                      <div className="flex justify-between">
                            <span className="text-text-secondary">下次行动时间</span>
                            <span className="text-white">
                              {OpportunityUtils.formatDate(selectedOpportunity.nextActionDate)}
                            </span>
                      </div>
                      }
                        {OpportunityUtils.isOverdue(selectedOpportunity) &&
                      <div className="p-2 rounded-lg bg-red-500/10 text-red-300 text-sm">
                            <AlertTriangle className="w-4 h-4 inline mr-1" />
                            已超期 {OpportunityUtils.getOverdueDays(selectedOpportunity)} 天
                      </div>
                      }
                      </CardContent>
                    </Card>
                  </div>
                </div>

                <DialogFooter>
                  <Button
                  variant="outline"
                  onClick={() => setShowDetailDialog(false)}
                  className="bg-surface-2 border-border">

                    关闭
                  </Button>
                  <Button
                  variant="destructive"
                  onClick={handleDeleteOpportunity}
                  className="bg-red-500 hover:bg-red-600">

                    <Trash2 className="w-4 h-4 mr-2" />
                    删除
                  </Button>
                </DialogFooter>
            </>
            }
          </DialogContent>
        </Dialog>
      </div>
    </div>);

}