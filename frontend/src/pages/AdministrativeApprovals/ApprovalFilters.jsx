import { TYPE_FILTER_OPTIONS, PRIORITY_FILTER_OPTIONS } from "./constants";

/**
 * Search + type + priority filter bar.
 *
 * Props:
 *   searchText        — string
 *   setSearchText     — (value: string) => void
 *   typeFilter        — string
 *   setTypeFilter     — (value: string) => void
 *   priorityFilter    — string
 *   setPriorityFilter — (value: string) => void
 */
export function ApprovalFilters({
  searchText,
  setSearchText,
  typeFilter,
  setTypeFilter,
  priorityFilter,
  setPriorityFilter,
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex gap-4">
          <Input
            placeholder="搜索申请标题、申请人..."
            value={searchText || ""}
            onChange={(e) => setSearchText(e.target.value)}
            className="flex-1"
          />

          <select
            value={typeFilter || "all"}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">
            {TYPE_FILTER_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select
            value={priorityFilter || "all"}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">
            {PRIORITY_FILTER_OPTIONS.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </CardContent>
    </Card>
  );
}
