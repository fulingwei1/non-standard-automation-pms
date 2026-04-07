/**
 * Payment Approval Page - Payment approval workflow for finance manager
 * Features: Payment approval, Payment query, Approval history, Batch approval
 */

import { ClipboardCheck } from "lucide-react";
import { fadeIn, staggerContainer } from "../../lib/animations";

import { usePaymentApprovalPage } from "./hooks/usePaymentApprovalPage";

export default function PaymentApproval() {
  const {
    searchTerm,
    setSearchTerm,
    selectedType,
    setSelectedType,
    selectedPriority,
    setSelectedPriority,
    filteredPayments,
    stats,
    selectedPayment,
    setSelectedPayment,
    showApprovalDialog,
    approvalAction,
    approvalComment,
    setApprovalComment,
    handleApprove,
    handleReject,
    handleCloseApprovalDialog,
    handleConfirmApproval,
  } = usePaymentApprovalPage();

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="付款审批"
        description="审批付款申请、查询审批历史"
        icon={ClipboardCheck}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              批量审批
            </Button>
          </motion.div>
        }
      />

      {/* Statistics */}
      <StatsCards stats={stats} />

      {/* Filters */}
      <PaymentFilters
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        selectedType={selectedType}
        setSelectedType={setSelectedType}
        selectedPriority={selectedPriority}
        setSelectedPriority={setSelectedPriority}
      />

      {/* Payment List */}
      <PaymentList
        filteredPayments={filteredPayments}
        onView={(payment) => setSelectedPayment(payment)}
        onApprove={handleApprove}
        onReject={handleReject}
      />

      {/* Approval Dialog */}
      <ApprovalDialog
        open={showApprovalDialog}
        onOpenChange={handleCloseApprovalDialog}
        approvalAction={approvalAction}
        approvalComment={approvalComment}
        onCommentChange={setApprovalComment}
        selectedPayment={selectedPayment}
        onConfirm={handleConfirmApproval}
      />

      {/* Payment Detail Dialog — only shown when no approval dialog is active */}
      <PaymentDetailDialog
        payment={!showApprovalDialog ? selectedPayment : null}
        onClose={() => setSelectedPayment(null)}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </motion.div>
  );
}
