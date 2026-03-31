/**
 * Acceptance Management (客户验收管理 FAT/SAT)
 * 验收记录管理 - 检查清单 + 问题追踪 + 签收
 *
 * Orchestrator — composes sub-components; owns no direct state.
 */

import { motion } from "framer-motion";
import { ClipboardCheck } from "lucide-react";

import { PageHeader } from "../../components/layout";

import useAcceptanceManagement from "./useAcceptanceManagement";
import StatsCards from "./StatsCards";
import FilterBar from "./FilterBar";
import RecordsTable from "./RecordsTable";
import CreateFormDialog from "./CreateFormDialog";
import DetailDialog from "./DetailDialog";

const AcceptanceManagement = () => {
  const {
    loading,
    projects,
    stats,
    filteredRecords,
    searchText,
    setSearchText,
    filters,
    setFilters,
    showCreateDialog,
    setShowCreateDialog,
    selectedRecord,
    showDetailDialog,
    setShowDetailDialog,
    handleCreate,
    handleViewDetail,
    loadRecords,
  } = useAcceptanceManagement();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="p-6 bg-slate-900 min-h-screen"
    >
      {/* 页面头部 */}
      <PageHeader
        icon={ClipboardCheck}
        title="验收管理"
        description="客户验收管理 (FAT/SAT) - 检查清单 + 问题追踪 + 签收"
      />

      {/* 统计卡片 */}
      <StatsCards stats={stats} />

      {/* 搜索和筛选 */}
      <FilterBar
        searchText={searchText}
        setSearchText={setSearchText}
        filters={filters}
        setFilters={setFilters}
        onCreate={() => setShowCreateDialog(true)}
        onRefresh={loadRecords}
      />

      {/* 数据表格 */}
      <RecordsTable
        loading={loading}
        filteredRecords={filteredRecords}
        onViewDetail={handleViewDetail}
      />

      {/* 创建对话框 */}
      <CreateFormDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        projects={projects}
        onSubmit={handleCreate}
      />

      {/* 详情对话框 */}
      <DetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        record={selectedRecord}
      />
    </motion.div>
  );
};

export default AcceptanceManagement;
