/**
 * Quote Management Page - Orchestrator
 * 报价管理页面 - 主入口
 * Features: Quote list, creation, version management, approval
 */

import { fadeIn, staggerContainer } from "../../lib/animations";

import useQuoteData from "./useQuoteData";

export default function QuoteManagement({ embedded = false } = {}) {
  const {
    quotes,
    opportunities,
    customers,
    selectedQuotes,
    loading,
    showCreateDialog,
    setShowCreateDialog,
    showEditDialog,
    setShowEditDialog,
    showDetailDialog,
    setShowDetailDialog,
    selectedQuote,
    stats,
    viewMode,
    setViewMode,
    searchTerm,
    setSearchTerm,
    filters,
    sortBy,
    setSortBy,
    timeRange,
    setTimeRange,
    costTimeRange,
    setCostTimeRange,
    costInsights,
    costLoading,
    handleRefresh,
    handleQuoteView,
    handleQuoteEdit,
    handleQuoteCopy,
    handleQuoteSend,
    handleQuoteApprove,
    handleQuoteReject,
    handleQuoteCreate,
    handleFilterChange,
    handleSelectionChange,
    handleExport,
    handleImport,
    topSupplier,
    trendItems,
    categories,
    suppliers,
    totalCostForRatio,
  } = useQuoteData();

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6">

      {!embedded && (
        <PageHeader
          title="报价管理"
          subtitle="管理销售报价，支持多版本管理和审批流程"
          breadcrumbs={[
          { label: "销售管理", href: "/sales" },
          { label: "报价管理", href: "/quotes" }]
          }
          actions={
          <div className="flex items-center gap-3">
              <Button
              variant="outline"
              onClick={() => window.location.href = "/quote-analytics"}>
                数据分析
              </Button>
              <Button
              onClick={handleQuoteCreate}
              className="bg-blue-600 hover:bg-blue-700 text-white">
                新建报价
              </Button>
          </div>
          } />
      )}

      {/* Tab 切换：报价列表 / 毛利分析 */}
      <Tabs defaultValue="quotes" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
          <TabsTrigger value="quotes" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            报价列表
          </TabsTrigger>
          <TabsTrigger value="margin" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            毛利分析
          </TabsTrigger>
        </TabsList>

        <TabsContent value="quotes">
      <motion.div variants={fadeIn} className="space-y-6">
        {/* 统计概览 */}
        <QuoteStatsOverview
          stats={stats}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          onRefresh={handleRefresh}
          loading={loading}
          timeRange={timeRange}
          onTimeRangeChange={setTimeRange} />

        {/* 成本洞察 */}
        <motion.div variants={fadeIn} className="grid gap-6 xl:grid-cols-3">
          <CostInsightsPanel
            costInsights={costInsights}
            costLoading={costLoading}
            costTimeRange={costTimeRange}
            setCostTimeRange={setCostTimeRange}
            topSupplier={topSupplier}
            trendItems={trendItems}
          />
          <CostStructurePanel
            categories={categories}
            suppliers={suppliers}
            totalCostForRatio={totalCostForRatio}
            costLoading={costLoading}
          />
        </motion.div>

        {/* 报价列表管理 */}
        <QuoteListManager
          quotes={quotes}
          opportunities={opportunities}
          customers={customers}
          viewMode={viewMode}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          filters={filters}
          onFilterChange={handleFilterChange}
          sortBy={sortBy}
          onSortChange={setSortBy}
          selectedQuotes={selectedQuotes}
          onSelectionChange={handleSelectionChange}
          onQuoteView={handleQuoteView}
          onQuoteEdit={handleQuoteEdit}
          onQuoteCreate={handleQuoteCreate}
          onQuoteCopy={handleQuoteCopy}
          onQuoteSend={handleQuoteSend}
          onQuoteApprove={handleQuoteApprove}
          onQuoteReject={handleQuoteReject}
          onExport={handleExport}
          onImport={handleImport}
          loading={loading} />

      </motion.div>
        </TabsContent>

        <TabsContent value="margin">
          <MarginAnalysis />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <QuoteDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedQuote={selectedQuote}
        onApprove={handleQuoteApprove}
        onReject={handleQuoteReject}
        onSend={handleQuoteSend}
        onEdit={handleQuoteEdit}
      />

      <QuoteCreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
      />

      <QuoteEditDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        selectedQuote={selectedQuote}
      />
    </motion.div>);
}
