import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { Input } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { stageConfig, healthConfig } from "./constants";

/**
 * ProjectFilters — search input, stage select, health select, and result count.
 */
export function ProjectFilters({
  searchTerm,
  onSearchChange,
  selectedStage,
  onStageChange,
  selectedHealth,
  onHealthChange,
  resultCount,
}) {
  return (
    <motion.div
      variants={fadeIn}
      className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between"
    >
      <div className="flex flex-wrap gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="搜索项目..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 w-56"
          />
        </div>

        {/* Stage filter */}
        <select
          value={selectedStage}
          onChange={(e) => onStageChange(e.target.value)}
          className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">全部阶段</option>
          {Object.entries(stageConfig).map(([key, val]) => (
            <option key={key} value={key}>
              {val.label}
            </option>
          ))}
        </select>

        {/* Health filter */}
        <select
          value={selectedHealth}
          onChange={(e) => onHealthChange(e.target.value)}
          className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="all">全部状态</option>
          {Object.entries(healthConfig).map(([key, val]) => (
            <option key={key} value={key}>
              {val.label}
            </option>
          ))}
        </select>
      </div>

      <span className="text-sm text-slate-400">共 {resultCount} 个项目</span>
    </motion.div>
  );
}
