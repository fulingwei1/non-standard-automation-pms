import { motion } from "framer-motion";
import {
  Card,
  CardContent,
} from "../../components/ui";
import {
  AlertTriangle,
  FileCheck,
  Truck,
  TrendingUp,
  TrendingDown,
  Building2,
} from "lucide-react";

export default function StatsCards({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">待审批订单</p>
                <p className="text-3xl font-bold text-white">
                  {stats?.pendingApprovals || 0}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                <FileCheck className="w-6 h-6 text-amber-400" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-red-400">3 项紧急</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">在途订单</p>
                <p className="text-3xl font-bold text-white">
                  {stats?.inTransitOrders || 0}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center">
                <Truck className="w-6 h-6 text-cyan-400" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">+5 本周</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">缺料预警</p>
                <p className="text-3xl font-bold text-white">
                  {stats?.shortageAlerts || 0}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">-2 较上周</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}>

        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">在用供应商</p>
                <p className="text-3xl font-bold text-white">
                  {stats?.activeSuppliers || 0}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                <Building2 className="w-6 h-6 text-purple-400" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400">+2 本月</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
