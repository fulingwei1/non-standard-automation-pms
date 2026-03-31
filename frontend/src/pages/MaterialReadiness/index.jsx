/**
 * Material Readiness - 齐套管理
 * 统一管理物料齐套检查（工单级别）和齐套分析（项目级别）
 */

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Download } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { MATERIAL_TYPE, PRIORITY_LEVEL, MATERIAL_STATUS } from "../../components/material-readiness";
import { toast } from "../../components/ui/toast";
import { useMaterialReadiness } from "./hooks/useMaterialReadiness";
import FilterBar from "./FilterBar";
import OverviewPanel from "./OverviewPanel";
import MaterialListView from "./MaterialListView";
import AnalyticsView from "./AnalyticsView";
import MaterialDetailDialog from "./MaterialDetailDialog";

export default function MaterialReadiness() {
  const [viewMode, setViewMode] = useState("overview"); // overview | list | analytics
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);

  const {
    loading,
    materials,
    projects,
    selectedProject,
    setSelectedProject,
    searchQuery,
    setSearchQuery,
    filterStatus,
    setFilterStatus,
    filterType,
    setFilterType,
    setFilterPriority,
    fetchData,
    stats,
    urgentMaterials,
    arrivingMaterials,
  } = useMaterialReadiness();

  // 获取类型分布
  const typeDistribution = useMemo(() => {
    const distribution = {};

    Object.values(MATERIAL_TYPE).forEach((type) => {
      distribution[type] = 0;
    });

    (materials || []).forEach((material) => {
      if (material.type) {
        distribution[material.type] = (distribution[material.type] || 0) + 1;
      }
    });

    return distribution;
  }, [materials]);

  const handleViewMaterial = (material) => {
    setSelectedMaterial(material);
    setShowDetailDialog(true);
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case "createMaterial":
        toast.info("创建物料功能开发中...");
        break;
      case "criticalShortages":
        setFilterPriority(PRIORITY_LEVEL.URGENT);
        setFilterStatus(MATERIAL_STATUS.OUT_OF_STOCK);
        setViewMode("list");
        break;
      case "readinessAnalysis":
        setViewMode("analytics");
        break;
      case "materialRequest":
        toast.info("物料申请功能开发中...");
        break;
      default:
        break;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      <PageHeader
        title="物料齐套管理"
        description="统一管理物料齐套检查和分析"
        actions={
          <div className="flex space-x-2">
            <Button variant="outline" onClick={fetchData}>
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              导出
            </Button>
          </div>
        }
      />

      <FilterBar
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        filterStatus={filterStatus}
        onFilterStatusChange={setFilterStatus}
        filterType={filterType}
        onFilterTypeChange={setFilterType}
        selectedProject={selectedProject}
        onProjectChange={setSelectedProject}
        projects={projects}
      />

      {/* 主要内容区域 */}
      {viewMode === "overview" && (
        <OverviewPanel
          stats={stats}
          urgentMaterials={urgentMaterials}
          arrivingMaterials={arrivingMaterials}
          typeDistribution={typeDistribution}
          onQuickAction={handleQuickAction}
        />
      )}

      {viewMode === "list" && (
        <MaterialListView
          loading={loading}
          materials={materials}
          onViewMaterial={handleViewMaterial}
        />
      )}

      {viewMode === "analytics" && <AnalyticsView />}

      <MaterialDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        material={selectedMaterial}
      />
    </motion.div>
  );
}
