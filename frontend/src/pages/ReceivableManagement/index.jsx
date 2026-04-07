/**
 * Receivable Management Page - Accounts receivable tracking and collection
 * Features: Receivable list, payment recording, aging analysis, overdue tracking
 */

import { staggerContainer } from "../../lib/animations";

import { useReceivableManagement } from "./hooks";

export default function ReceivableManagement() {
  const {
    // list
    receivables,
    loading,
    // pagination
    page,
    setPage,
    total,
    pageSize,
    // filters
    searchTerm,
    setSearchTerm,
    statusFilter,
    setStatusFilter,
    overdueOnly,
    setOverdueOnly,
    // aging & stats
    agingData,
    stats,
    // dialog
    selectedReceivable,
    setSelectedReceivable,
    showPaymentDialog,
    setShowPaymentDialog,
    paymentData,
    setPaymentData,
    // actions
    loadAging,
    handleReceivePayment,
    handleExport,
    formatCurrency,
  } = useReceivableManagement();

  // Derived values for PaymentDialog
  const receivableBaseAmount = selectedReceivable
    ? (selectedReceivable.invoice_amount ?? selectedReceivable.total_amount ?? 0)
    : 0;
  const receivablePendingAmount = selectedReceivable
    ? (selectedReceivable.unpaid_amount ??
        receivableBaseAmount - (selectedReceivable.paid_amount ?? 0))
    : 0;
  const receivableMaxAmount = selectedReceivable
    ? (selectedReceivable.unpaid_amount ?? receivableBaseAmount)
    : undefined;
  const paymentDateMax = new Date().toISOString().split("T")[0];
  const paymentAmountPlaceholder = selectedReceivable
    ? `最大可收: ${formatCurrency(receivableMaxAmount)}`
    : "请输入收款金额";

  const handleRecordPayment = (receivable) => {
    setSelectedReceivable(receivable);
    setShowPaymentDialog(true);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <PageHeader
        title="应收账款管理"
        description="跟踪和管理应收账款，记录收款，分析账龄"
        action={
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadAging}>
              <BarChart3 className="mr-2 h-4 w-4" />
              刷新账龄
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="mr-2 h-4 w-4" />
              导出数据
            </Button>
          </div>
        }
      />

      <StatsCards stats={stats} formatCurrency={formatCurrency} />

      <AgingAnalysis agingData={agingData} formatCurrency={formatCurrency} />

      <FilterBar
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        overdueOnly={overdueOnly}
        onOverdueChange={setOverdueOnly}
      />

      <ReceivableList
        loading={loading}
        receivables={receivables}
        total={total}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onRecordPayment={handleRecordPayment}
        formatCurrency={formatCurrency}
      />

      <PaymentDialog
        open={showPaymentDialog}
        onOpenChange={setShowPaymentDialog}
        paymentData={paymentData}
        setPaymentData={setPaymentData}
        invoiceLabel={selectedReceivable?.invoice_code}
        pendingAmount={receivablePendingAmount}
        amountStep="0.01"
        amountMin={0}
        amountMax={receivableMaxAmount}
        amountPlaceholder={paymentAmountPlaceholder}
        dateMax={paymentDateMax}
        showPaymentMethod
        showBankAccount
        formatAmount={formatCurrency}
        onConfirm={handleReceivePayment}
      />
    </motion.div>
  );
}
