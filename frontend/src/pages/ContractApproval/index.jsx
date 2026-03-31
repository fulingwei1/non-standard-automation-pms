/**
 * Contract Approval Page - Contract approval workflow for sales directors
 * Features: Pending approvals, Approval history, Contract review, Approval actions
 */

import { motion } from "framer-motion";
import { Filter, History } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { useContractApproval } from "./hooks";
import { ApprovalStatsCards } from "./ApprovalStatsCards";
import { ApprovalList } from "./ApprovalList";
import { ApprovalDetailDialog } from "./ApprovalDetailDialog";

export default function ContractApproval() {
  const {
    activeTab,
    setActiveTab,
    searchTerm,
    setSearchTerm,
    pendingApprovals,
    approvalHistory,
    filteredApprovals,
    selectedApproval,
    showDetailDialog,
    approvalComments,
    setApprovalComments,
    actionLoading,
    actionError,
    handleViewDetail,
    handleCloseDialog,
    handleApprove,
    handleReject,
  } = useContractApproval();

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="合同审批"
        description={`待审批: ${pendingApprovals.length}项 | 已审批: ${approvalHistory.length}项`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              筛选
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              审批历史
            </Button>
          </motion.div>
        }
      />

      {/* Stats Cards */}
      <ApprovalStatsCards
        pendingApprovals={pendingApprovals}
        approvalHistory={approvalHistory}
      />

      {/* Search + Tabbed List */}
      <ApprovalList
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        filteredApprovals={filteredApprovals}
        pendingApprovals={pendingApprovals}
        approvalHistory={approvalHistory}
        onViewDetail={handleViewDetail}
      />

      {/* Approval Detail Dialog */}
      <ApprovalDetailDialog
        open={showDetailDialog}
        onOpenChange={(open) => {
          if (!open) handleCloseDialog();
        }}
        approval={selectedApproval}
        approvalComments={approvalComments}
        setApprovalComments={setApprovalComments}
        actionLoading={actionLoading}
        actionError={actionError}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </motion.div>
  );
}
