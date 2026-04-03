import { motion } from "framer-motion";
import {
  ClipboardCheck,
  AlertTriangle,
  DollarSign,
  CreditCard,
} from "lucide-react";
import { Card, CardContent } from "../../components/ui";
import { formatCurrency } from "../../lib/utils";
import { staggerContainer } from "../../lib/animations";

export function StatsCards({ stats }) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4"
    >
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">待审批</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-xs text-slate-500 mt-1">笔</p>
            </div>
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <ClipboardCheck className="w-5 h-5 text-blue-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">待审批金额</p>
              <p className="text-2xl font-bold text-amber-400">
                {formatCurrency(stats.totalAmount)}
              </p>
            </div>
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-amber-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">紧急事项</p>
              <p className="text-2xl font-bold text-red-400">{stats.urgent}</p>
              <p className="text-xs text-slate-500 mt-1">笔</p>
            </div>
            <div className="p-2 bg-red-500/20 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-2">紧急金额</p>
              <p className="text-2xl font-bold text-red-400">
                {formatCurrency(stats.urgentAmount)}
              </p>
            </div>
            <div className="p-2 bg-red-500/20 rounded-lg">
              <CreditCard className="w-5 h-5 text-red-400" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
