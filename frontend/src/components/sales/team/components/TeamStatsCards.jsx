/**
 * TeamStatsCards - 团队统计卡片组件
 * 显示4个关键团队指标：目标、完成、项目、客户
 */

import { motion } from "framer-motion";
import {
  Target,
  DollarSign,
  Activity,
  Users,
} from "lucide-react";
import { Card, CardContent } from "../../../ui";
import { formatCurrency } from "@/lib/constants/salesTeam";

export default function TeamStatsCards({ teamStats }) {
  return (
    <motion.div
      variants={{
        visible: {
          transition: {
            staggerChildren: 0.1,
          },
        },
      }}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      {/* 团队目标卡片 */}
      <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">团队目标</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(teamStats.totalTarget)}
                </p>
                <p className="text-xs text-slate-500 mt-1">本月总目标</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Target className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 团队完成卡片 */}
      <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">团队完成</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(teamStats.totalAchieved)}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <Activity className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">
                    {teamStats.avgAchievementRate}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 进行中项目卡片 */}
      <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">进行中项目</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {teamStats.totalProjects}
                </p>
                <p className="text-xs text-slate-500 mt-1">团队项目总数</p>
              </div>
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Activity className="w-5 h-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 客户总数卡片 */}
      <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">客户总数</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {teamStats.totalCustomers}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  本月新增 {teamStats.newCustomersThisMonth}
                </p>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <Users className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
