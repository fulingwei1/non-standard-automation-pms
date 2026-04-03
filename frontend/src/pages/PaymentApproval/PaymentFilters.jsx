import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { Card, CardContent, Input } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { typeConfig, PRIORITY_OPTIONS } from "./constants";

export function PaymentFilters({
  searchTerm,
  setSearchTerm,
  selectedType,
  setSelectedType,
  selectedPriority,
  setSelectedPriority,
}) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="搜索单号、项目、供应商、申请人..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">全部类型</option>
              {Object.entries(typeConfig).map(([key, val]) => (
                <option key={key} value={key}>
                  {val.label}
                </option>
              ))}
            </select>

            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {PRIORITY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
