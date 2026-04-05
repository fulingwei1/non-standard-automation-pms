/**
 * 投标统计卡片组件
 */
import { motion } from "framer-motion";
import {
  Target,
  Clock,
  Award,
  DollarSign,
} from "lucide-react";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import { fadeIn } from "../../lib/animations";

export function StatsCards({ stats }) {
  return (
    <motion.div
      variants={fadeIn}
      className="grid grid-cols-2 sm:grid-cols-4 gap-4">

      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-500/10 flex items-center justify-center">
              <Target className="w-5 h-5 text-slate-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500">全部项目</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <Clock className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500">进行中</p>
              <p className="text-2xl font-bold text-blue-400">
                {stats.active}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <Award className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500">已中标</p>
              <p className="text-2xl font-bold text-emerald-400">
                {stats.won}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500">中标金额</p>
              <p className="text-2xl font-bold text-violet-400">
                ¥{stats.totalAmount}万
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
