import { fadeIn } from "../../lib/animations";
import { statusConfig } from "./statusConfig";

export function FilterBar({
  searchTerm,
  setSearchTerm,
  selectedStatus,
  setSelectedStatus,
  viewMode,
  setViewMode,
  filteredCount,
}) {
  return (
    <motion.div
      variants={fadeIn}
      className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between"
    >
      <div className="flex flex-wrap gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="搜索报价单号、名称..."
            value={searchTerm || "unknown"}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 w-64"
          />
        </div>
        <select
          value={selectedStatus || "unknown"}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">全部状态</option>
          {Object.entries(statusConfig).map(([key, val]) => (
            <option key={key} value={key || "unknown"}>
              {val.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-400">共 {filteredCount} 个报价</span>
        <div className="flex border border-white/10 rounded-lg overflow-hidden">
          <Button
            variant={viewMode === "list" ? "default" : "ghost"}
            size="sm"
            className="rounded-none"
            onClick={() => setViewMode("list")}
          >
            <List className="w-4 h-4" />
          </Button>
          <Button
            variant={viewMode === "grid" ? "default" : "ghost"}
            size="sm"
            className="rounded-none"
            onClick={() => setViewMode("grid")}
          >
            <LayoutGrid className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
