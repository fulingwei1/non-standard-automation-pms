import { motion } from "framer-motion";
import {
  FileSignature,
  DollarSign,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { Card, CardContent } from "../../components/ui";
import { fadeIn } from "../../lib/animations";

export default function ContractStatsRow({ stats }) {
  return (
    <motion.div
      variants={fadeIn}
      className="grid grid-cols-2 sm:grid-cols-4 gap-4"
    >
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <FileSignature className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.active}</p>
            <p className="text-xs text-slate-400">执行中合同</p>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-amber-500/20 rounded-lg">
            <DollarSign className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">
              ¥{(stats.totalValue / 10000).toFixed(0)}万
            </p>
            <p className="text-xs text-slate-400">合同总额</p>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-emerald-500/20 rounded-lg">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-emerald-400">
              ¥{(stats.paidValue / 10000).toFixed(0)}万
            </p>
            <p className="text-xs text-slate-400">已回款</p>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Clock className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-purple-400">
              ¥{(stats.pendingValue / 10000).toFixed(0)}万
            </p>
            <p className="text-xs text-slate-400">待回款</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
