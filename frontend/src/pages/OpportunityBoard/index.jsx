/**
 * Opportunity Board Page - Sales pipeline kanban view (Refactored)
 * Features: Stage columns, drag-and-drop, opportunity cards, funnel visualization
 */

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../../components/layout";
import { fadeIn } from "../../lib/animations";
import {
  OpportunityBoardOverview,
  OPPORTUNITY_STAGES,
  OPPORTUNITY_PRIORITY,
  SALES_SOURCE,
  OPPORTUNITY_TYPE,
  OpportunityUtils,
} from "../../components/opportunity-board";
import { opportunityApi, salesStatisticsApi } from "../../services/api";
import { confirmAction } from "@/lib/confirmAction";

import ViewModeTabs from "./ViewModeTabs";
import FilterControls from "./FilterControls";
import BoardView from "./BoardView";
import ListView from "./ListView";
import FunnelView from "./FunnelView";
import CreateOpportunityDialog from "./CreateOpportunityDialog";
import OpportunityDetailDialog from "./OpportunityDetailDialog";

// 阶段映射函数
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
      const data = response.data?.items || response.data?.items || response.data || [];

      // 转换数据格式
      const transformedOpps = (data || []).map((opp) => {
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
      ...new Set((transformedOpps || []).map((opp) => opp.ownerId).filter(Boolean))].
      map((ownerId) => {
        const opp = (transformedOpps || []).find((o) => o.ownerId === ownerId);
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
        <ViewModeTabs viewMode={viewMode} setViewMode={setViewMode} />

        <FilterControls
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          selectedPriority={selectedPriority}
          setSelectedPriority={setSelectedPriority}
          selectedSource={selectedSource}
          setSelectedSource={setSelectedSource}
          selectedType={selectedType}
          setSelectedType={setSelectedType}
          selectedOwner={selectedOwner}
          setSelectedOwner={setSelectedOwner}
          owners={owners}
          showHotOnly={showHotOnly}
          setShowHotOnly={setShowHotOnly}
          hideLost={hideLost}
          setHideLost={setHideLost}
          onCreateClick={() => setShowCreateDialog(true)}
        />

        {/* Content */}
        <motion.div variants={fadeIn}>
          {viewMode === "overview" &&
          <OpportunityBoardOverview opportunities={filteredOpportunities} />
          }

          {viewMode === "board" &&
          <BoardView
            groupedOpportunities={groupedOpportunities}
            hideLost={hideLost}
            onOpportunityClick={handleOpportunityClick}
            onStageChange={handleStageChange}
          />
          }

          {viewMode === "funnel" &&
          <FunnelView funnelData={funnelData} />
          }

          {viewMode === "list" &&
          <ListView
            sortedOpportunities={sortedOpportunities}
            onOpportunityClick={handleOpportunityClick}
          />
          }
        </motion.div>

        <CreateOpportunityDialog
          open={showCreateDialog}
          onOpenChange={setShowCreateDialog}
          newOpportunity={newOpportunity}
          setNewOpportunity={setNewOpportunity}
          owners={owners}
          onSubmit={handleCreateOpportunity}
        />

        <OpportunityDetailDialog
          open={showDetailDialog}
          onOpenChange={setShowDetailDialog}
          selectedOpportunity={selectedOpportunity}
          onDelete={handleDeleteOpportunity}
        />
      </div>
    </div>);

}
