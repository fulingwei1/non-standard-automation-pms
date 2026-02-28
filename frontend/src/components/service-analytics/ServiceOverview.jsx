import { motion } from "framer-motion";
import {
  FileText,
  Wrench,
  MessageSquare,
  Star,
  Clock,
  TrendingDown,
  CheckCircle2,
  TrendingUp
} from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";

export function ServiceOverview({ analytics }) {
  if (!analytics) return null;

  return (
    <>
      {/* Overview Stats */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <motion.div variants={fadeIn}>
          <Card className="bg-blue-500/10 border-blue-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">服务工单</p>
                  <p className="text-2xl font-bold text-blue-400">
                    {analytics.overview.totalTickets}
                  </p>
                </div>
                <FileText className="w-8 h-8 text-blue-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={fadeIn}>
          <Card className="bg-purple-500/10 border-purple-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">服务记录</p>
                  <p className="text-2xl font-bold text-purple-400">
                    {analytics.overview.totalRecords}
                  </p>
                </div>
                <Wrench className="w-8 h-8 text-purple-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={fadeIn}>
          <Card className="bg-emerald-500/10 border-emerald-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户沟通</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {analytics.overview.totalCommunications}
                  </p>
                </div>
                <MessageSquare className="w-8 h-8 text-emerald-400/50" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={fadeIn}>
          <Card className="bg-yellow-500/10 border-yellow-500/20">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">满意度调查</p>
                  <p className="text-2xl font-bold text-yellow-400">
                    {analytics.overview.totalSurveys}
                  </p>
                </div>
                <Star className="w-8 h-8 text-yellow-400/50 fill-yellow-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/30 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-400">平均响应时间</p>
                <Clock className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-white">
                {analytics.overview.averageResponseTime}小时
              </p>
              <div className="flex items-center gap-1 mt-1">
                <TrendingDown className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">
                  -0.5小时 vs 上月
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/30 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-400">平均解决时间</p>
                <CheckCircle2 className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-white">
                {analytics.overview.averageResolutionTime}小时
              </p>
              <div className="flex items-center gap-1 mt-1">
                <TrendingDown className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">
                  -1.2小时 vs 上月
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/30 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-400">平均满意度</p>
                <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
              </div>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-bold text-white">
                  {analytics.overview.averageSatisfaction}
                </p>
                <div className="flex items-center gap-0.5">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Star
                      key={i}
                      className={cn(
                        "w-3 h-3",
                        i <= Math.floor(analytics.overview.averageSatisfaction)
                          ? "fill-yellow-400 text-yellow-400"
                          : "text-slate-600"
                      )}
                    />
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">+0.2 vs 上月</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/30 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-400">完成率</p>
                <CheckCircle2 className="w-4 h-4 text-slate-400" />
              </div>
              <p className="text-2xl font-bold text-white">
                {analytics.overview.completionRate}%
              </p>
              <div className="flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                <span className="text-xs text-emerald-400">
                  +2.5% vs 上月
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </>
  );
}
