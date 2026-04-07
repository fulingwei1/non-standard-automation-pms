
/**
 * Content for the "待审批" (Pending) tab.
 *
 * Props:
 *   stats             — summary stats object
 *   filteredApprovals — filtered pending approval list
 *   searchText        — string
 *   setSearchText     — setter
 *   typeFilter        — string
 *   setTypeFilter     — setter
 *   priorityFilter    — string
 *   setPriorityFilter — setter
 *   onApprove         — (id) => void
 *   onReject          — (id) => void
 */
export function PendingTab({
  stats,
  filteredApprovals,
  searchText,
  setSearchText,
  typeFilter,
  setTypeFilter,
  priorityFilter,
  setPriorityFilter,
  onApprove,
  onReject,
}) {
  return (
    <div className="space-y-4">
      <ApprovalCharts stats={stats} />

      <ApprovalFilters
        searchText={searchText}
        setSearchText={setSearchText}
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
        priorityFilter={priorityFilter}
        setPriorityFilter={setPriorityFilter}
      />

      <div className="space-y-4">
        {(filteredApprovals || []).map((approval) => (
          <ApprovalCard
            key={approval.id}
            approval={approval}
            showActions
            onApprove={onApprove}
            onReject={onReject}
          />
        ))}
      </div>
    </div>
  );
}
