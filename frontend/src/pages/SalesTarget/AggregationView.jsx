import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

export default function AggregationView({ aggregationMode, setAggregationMode, aggregationRows }) {
  return (
    <motion.div variants={fadeIn}>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <span>目标汇总视图</span>
            <Select value={aggregationMode} onValueChange={setAggregationMode}>
              <SelectTrigger className="w-[220px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="organization">按组织架构汇总</SelectItem>
                <SelectItem value="industry">按行业汇总</SelectItem>
                <SelectItem value="region">按大区汇总</SelectItem>
                <SelectItem value="target_customer">按目标客户汇总</SelectItem>
              </SelectContent>
            </Select>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {aggregationRows.slice(0, 12).map((row) => (
            <div key={row.key} className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white font-medium">{row.key}</span>
                <span className="text-slate-300">{row.completion.toFixed(1)}%</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">目标 {formatCurrency(row.targetValue)} · 实际 {formatCurrency(row.actualValue)} · {row.count} 条</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </motion.div>
  );
}
