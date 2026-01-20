import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  Progress,
} from "../../components/ui";
import {
  TrendingUp,
  Award,
} from "lucide-react";
import { formatCurrency } from "../../lib/utils";

export default function PerformanceMetrics({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-slate-400">预算使用率</p>
              <p className="text-lg font-bold text-white">
                {stats?.budgetUsed || 0}%
              </p>
            </div>
            <Progress value={stats?.budgetUsed || 0} className="h-2" />
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-slate-400">按期到货率</p>
              <p className="text-lg font-bold text-white">
                {stats?.onTimeRate || 0}%
              </p>
            </div>
            <Progress value={stats?.onTimeRate || 0} className="h-2" />
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">本月采购额</p>
                <p className="text-xl font-bold text-white">
                  {formatCurrency(stats?.monthlySpending || 0)}
                </p>
              </div>
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">成本节省</p>
                <p className="text-xl font-bold text-white">
                  {formatCurrency(stats?.costSavings || 0)}
                </p>
              </div>
              <Award className="w-5 h-5 text-amber-400" />
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
