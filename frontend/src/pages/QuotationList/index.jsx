/**
 * Quotation List Page - Sales quotation management
 * Features: Quotation list, creation, approval, version history
 */

import { useState, useMemo } from "react";
import { fadeIn, staggerContainer } from "../../lib/animations";


export default function QuotationList() {
  const mockQuotations = [];
  const [viewMode, setViewMode] = useState("list");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedQuotation, setSelectedQuotation] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Filter quotations
  const filteredQuotations = useMemo(() => {
    return (mockQuotations || []).filter((quote) => {
      const searchLower = (searchTerm || "").toLowerCase();
      const matchesSearch =
        !searchTerm ||
        (quote.name || "").toLowerCase().includes(searchLower) ||
        (quote.id || "").toLowerCase().includes(searchLower) ||
        (quote.customerShort || "").toLowerCase().includes(searchLower);

      const matchesStatus =
        selectedStatus === "all" || quote.status === selectedStatus;

      return matchesSearch && matchesStatus;
    });
  }, [searchTerm, selectedStatus]);

  // Stats
  const stats = useMemo(() => {
    if (mockQuotations.length === 0) {
      return {
        total: 0,
        pending: 0,
        accepted: 0,
        rejected: 0,
        totalValue: 0,
        avgDiscount: "0.0",
      };
    }

    return {
      total: mockQuotations.length,
      pending: (mockQuotations || []).filter(
        (q) => q.status === "sent" || q.status === "pending_approval"
      ).length,
      accepted: (mockQuotations || []).filter((q) => q.status === "accepted")
        .length,
      rejected: (mockQuotations || []).filter((q) => q.status === "rejected")
        .length,
      totalValue: (mockQuotations || []).reduce(
        (sum, q) => sum + q.finalAmount,
        0
      ),
      avgDiscount: (
        (mockQuotations || []).reduce((sum, q) => sum + q.discountPercent, 0) /
        mockQuotations.length
      ).toFixed(1),
    };
  }, []);

  const handleQuotationClick = (quotation) => {
    setSelectedQuotation(quotation);
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="报价管理"
        description="创建和管理销售报价单"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button
              className="flex items-center gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              新建报价
            </Button>
          </motion.div>
        }
      />

      {/* Stats Row */}
      <StatsRow stats={stats} />

      {/* Filters */}
      <FilterBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        selectedStatus={selectedStatus}
        setSelectedStatus={setSelectedStatus}
        viewMode={viewMode}
        setViewMode={setViewMode}
        filteredCount={filteredQuotations.length}
      />

      {/* Content */}
      <motion.div variants={fadeIn}>
        {viewMode === "list" ? (
          <QuotationTableView
            quotations={filteredQuotations}
            onQuotationClick={handleQuotationClick}
          />
        ) : (
          <QuotationGridView
            quotations={filteredQuotations}
            onQuotationClick={handleQuotationClick}
          />
        )}

        {filteredQuotations.length === 0 && (
          <EmptyState onCreateClick={() => setShowCreateDialog(true)} />
        )}
      </motion.div>

      {/* Quotation Detail Panel */}
      <AnimatePresence>
        {selectedQuotation && (
          <QuotationDetailPanel
            quotation={selectedQuotation}
            onClose={() => setSelectedQuotation(null)}
          />
        )}
      </AnimatePresence>

      {/* Create Dialog */}
      <CreateQuotationDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
      />
    </motion.div>
  );
}
