import { RefreshCw } from "lucide-react";
import usePresaleTickets from "./usePresaleTickets";

export default function PresaleTicketBoard() {
  const {
    loading,
    loadError,
    searchKeyword,
    setSearchKeyword,
    statusFilter,
    setStatusFilter,
    priorityFilter,
    setPriorityFilter,
    selectedTicketId,
    setSelectedTicketId,
    priorityUpdatingId,
    flowUpdatingId,
    loadTickets,
    filteredTickets,
    selectedTicket,
    groupedByStatus,
    stats,
    priorityDistribution,
    handlePriorityChange,
    handleAdvanceFlow,
    renderFlowActionLabel,
  } = usePresaleTickets();

  return (
    <div className="space-y-6">
      <PageHeader
        title="售前工单看板"
        description="统一查看工单列表、流转状态、优先级与处理效率统计。"
        actions={[
          {
            label: "刷新数据",
            icon: RefreshCw,
            variant: "outline",
            onClick: loadTickets,
            disabled: loading,
          },
        ]}
      />

      {loadError && (
        <Card className="border-red-500/30 bg-red-500/5">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-sm text-red-200">
              <AlertTriangle className="h-4 w-4" />
              数据加载失败：{loadError}，请点击"刷新数据"重试。
            </div>
          </CardContent>
        </Card>
      )}

      <StatsCards stats={stats} />

      <TicketTable
        filteredTickets={filteredTickets}
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        priorityFilter={priorityFilter}
        setPriorityFilter={setPriorityFilter}
        selectedTicketId={selectedTicketId}
        setSelectedTicketId={setSelectedTicketId}
        priorityUpdatingId={priorityUpdatingId}
        flowUpdatingId={flowUpdatingId}
        handlePriorityChange={handlePriorityChange}
        handleAdvanceFlow={handleAdvanceFlow}
        renderFlowActionLabel={renderFlowActionLabel}
      />

      <div className="grid gap-4 xl:grid-cols-[1.5fr,1fr]">
        <KanbanBoard
          groupedByStatus={groupedByStatus}
          selectedTicketId={selectedTicketId}
          setSelectedTicketId={setSelectedTicketId}
        />

        <PriorityPanel
          priorityDistribution={priorityDistribution}
          stats={stats}
        />
      </div>

      <ProcessingStats
        stats={stats}
        selectedTicket={selectedTicket}
        flowUpdatingId={flowUpdatingId}
        handleAdvanceFlow={handleAdvanceFlow}
        renderFlowActionLabel={renderFlowActionLabel}
      />
    </div>
  );
}
