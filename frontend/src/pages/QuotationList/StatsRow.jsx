import { motion } from "framer-motion";
import { FileText, Clock, CheckCircle2, Percent } from "lucide-react";
import { Card, CardContent } from "../../components/ui";
import { fadeIn } from "../../lib/animations";

export function StatsRow({ stats }) {
  return (
    <motion.div
      variants={fadeIn}
      className="grid grid-cols-2 sm:grid-cols-4 gap-4"
    >
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <FileText className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.total}</p>
            <p className="text-xs text-slate-400">报价总数</p>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-amber-500/20 rounded-lg">
            <Clock className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.pending}</p>
            <p className="text-xs text-slate-400">待确认</p>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-emerald-500/20 rounded-lg">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">{stats.accepted}</p>
            <p className="text-xs text-slate-400">已接受</p>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="p-2 bg-purple-500/20 rounded-lg">
            <Percent className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <p className="text-2xl font-bold text-white">
              {stats.avgDiscount}%
            </p>
            <p className="text-xs text-slate-400">平均折扣</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
