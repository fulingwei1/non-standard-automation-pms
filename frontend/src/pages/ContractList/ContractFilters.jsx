import { fadeIn } from "../../lib/animations";
import { statusConfig } from "./constants";

export default function ContractFilters({
  searchTerm,
  onSearchChange,
  selectedStatus,
  onStatusChange,
  resultCount,
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
            placeholder="搜索合同号、名称..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 w-64"
          />
        </div>

        <select
          value={selectedStatus}
          onChange={(e) => onStatusChange(e.target.value)}
          className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">全部状态</option>
          {Object.entries(statusConfig).map(([key, val]) => (
            <option key={key} value={key}>
              {val.label}
            </option>
          ))}
        </select>
      </div>

      <span className="text-sm text-slate-400">共 {resultCount} 份合同</span>
    </motion.div>
  );
}
