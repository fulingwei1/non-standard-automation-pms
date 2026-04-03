/**
 * Administrative Approvals - Administrative approval center
 * Features: Approval list, approval workflow, approval history
 */

import { motion } from "framer-motion";
import { Download } from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui";
import { staggerContainer } from "../../lib/animations";

import { useAdministrativeApprovals } from "./hooks/useAdministrativeApprovals";
import { ApprovalStatsGrid } from "./ApprovalStatsGrid";
import { PendingTab } from "./PendingTab";
import { ApprovedTab, RejectedTab, HistoryTab } from "./HistoryTabs";

export default function AdministrativeApprovals() {
  const {
    approvedList,
    rejectedList,
    filteredApprovals,
    stats,
    searchText,
    setSearchText,
    typeFilter,
    setTypeFilter,
    priorityFilter,
    setPriorityFilter,
    handleApprove,
    handleReject,
  } = useAdministrativeApprovals();

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="行政审批中心"
        description="行政类审批事项管理、审批流程、审批历史"
        actions={
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            导出
          </Button>
        }
      />

      <ApprovalStatsGrid stats={stats} />

      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending">待审批</TabsTrigger>
          <TabsTrigger value="approved">已批准</TabsTrigger>
          <TabsTrigger value="rejected">已拒绝</TabsTrigger>
          <TabsTrigger value="history">审批历史</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          <PendingTab
            stats={stats}
            filteredApprovals={filteredApprovals}
            searchText={searchText}
            setSearchText={setSearchText}
            typeFilter={typeFilter}
            setTypeFilter={setTypeFilter}
            priorityFilter={priorityFilter}
            setPriorityFilter={setPriorityFilter}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </TabsContent>

        <TabsContent value="approved" className="space-y-4">
          <ApprovedTab approvedList={approvedList} />
        </TabsContent>

        <TabsContent value="rejected" className="space-y-4">
          <RejectedTab rejectedList={rejectedList} />
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <HistoryTab
            approvedList={approvedList}
            rejectedList={rejectedList}
          />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
