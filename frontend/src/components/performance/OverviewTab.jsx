import React from "react";
import { motion } from "framer-motion";
import { Award, Target, TrendingUp, Users, Briefcase } from "lucide-react";
import { cn } from "../../lib/utils";
import {
  getStatusBadge,
  getLevelInfo,
  getTrendIcon,
  calculateQuarterComparison } from
"../../utils/performanceUtils";

const _fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 }
};

/**
 * 绩效概览Tab组件
 */
export const OverviewTab = ({ currentPeriod, latestScore, quarterlyTrend }) => {
  const quarterComparison = React.useMemo(
    () => calculateQuarterComparison(quarterlyTrend),
    [quarterlyTrend]
  );

  return (
    <motion.div
      key="overview"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6">

      {/* 当前季度评价状态 */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white">当前评价状态</h3>
          <span className="text-slate-400">
            {currentPeriod.year}年 Q{currentPeriod.quarter}
          </span>
        </div>

        <div className="space-y-4">
          {/* 总体状态 */}
          <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "h-10 w-10 rounded-full flex items-center justify-center",
                  getStatusBadge(currentPeriod.status).color
                )}>

                {React.createElement(
                  getStatusBadge(currentPeriod.status).icon,
                  {
                    className: "h-5 w-5"
                  }
                )}
              </div>
              <div>
                <p className="text-white font-medium">评价状态</p>
                <p className="text-sm text-slate-400">
                  提交时间: {currentPeriod.submitDate}
                </p>
              </div>
            </div>
            <span
              className={cn(
                "px-4 py-2 rounded-full text-sm font-medium",
                getStatusBadge(currentPeriod.status).color
              )}>

              {getStatusBadge(currentPeriod.status).label}
            </span>
          </div>

          {/* 部门经理评价 */}
          <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-blue-400" />
                <div>
                  <p className="text-white font-medium">部门经理评价 (50%)</p>
                  <p className="text-sm text-slate-400">
                    {currentPeriod.deptEvaluation.evaluator}
                  </p>
                </div>
              </div>
              {currentPeriod.deptEvaluation.score ?
              <div className="text-right">
                  <p className="text-2xl font-bold text-blue-400">
                    {currentPeriod.deptEvaluation.score}
                  </p>
                  <p className="text-xs text-slate-400">已评分</p>
              </div> :

              <span
                className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  getStatusBadge("PENDING").color
                )}>

                  {getStatusBadge("PENDING").label}
              </span>
              }
            </div>
          </div>

          {/* 项目经理评价 */}
          <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
            <div className="flex items-center gap-3 mb-3">
              <Briefcase className="h-5 w-5 text-purple-400" />
              <p className="text-white font-medium">项目经理评价 (50%)</p>
            </div>
            <div className="space-y-3">
              {currentPeriod.projectEvaluations.map((proj, idx) =>
              <div
                key={idx}
                className="flex items-center justify-between pl-8">

                  <div>
                    <p className="text-slate-300">{proj.projectName}</p>
                    <p className="text-xs text-slate-400">
                      {proj.evaluator} · 权重 {proj.weight}%
                    </p>
                  </div>
                  {proj.score ?
                <div className="text-right">
                      <p className="text-xl font-bold text-purple-400">
                        {proj.score}
                      </p>
                      <p className="text-xs text-slate-400">已评分</p>
                </div> :

                <span
                  className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium",
                    getStatusBadge("PENDING").color
                  )}>

                      {getStatusBadge("PENDING").label}
                </span>
                }
              </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 最新绩效结果 */}
      {latestScore &&
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-xl font-bold text-white mb-6">最新绩效结果</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {/* 综合得分 */}
            <div
            className={cn(
              "p-6 rounded-xl border-2",
              getLevelInfo(latestScore.level).bgColor,
              getLevelInfo(latestScore.level).borderColor
            )}>

              <div className="flex items-center gap-3 mb-3">
                <Award
                className={cn(
                  "h-6 w-6",
                  getLevelInfo(latestScore.level).color
                )} />

                <span className="text-slate-400">综合得分</span>
              </div>
              <p
              className={cn(
                "text-4xl font-bold mb-2",
                getLevelInfo(latestScore.level).color
              )}>

                {latestScore.totalScore}
              </p>
              <div className="flex items-center gap-2">
                <span
                className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  getLevelInfo(latestScore.level).color,
                  getLevelInfo(latestScore.level).bgColor
                )}>

                  {latestScore.level}级 · {getLevelInfo(latestScore.level).name}
                </span>
              </div>
            </div>

            {/* 部门排名 */}
            <div className="p-6 bg-blue-500/10 rounded-xl border-2 border-blue-500/20">
              <div className="flex items-center gap-3 mb-3">
                <Target className="h-6 w-6 text-blue-400" />
                <span className="text-slate-400">部门排名</span>
              </div>
              <p className="text-4xl font-bold text-blue-400 mb-2">
                #{latestScore.rank}
              </p>
              <p className="text-sm text-slate-400">
                共 {latestScore.totalEmployees} 人
              </p>
            </div>

            {/* 季度趋势 */}
            <div className="p-6 bg-purple-500/10 rounded-xl border-2 border-purple-500/20">
              <div className="flex items-center gap-3 mb-3">
                <TrendingUp className="h-6 w-6 text-purple-400" />
                <span className="text-slate-400">季度趋势</span>
              </div>
              {quarterComparison &&
            <>
                  <div className="flex items-baseline gap-2 mb-2">
                    <p className="text-4xl font-bold text-purple-400">
                      {quarterComparison.change > 0 ? "+" : ""}
                      {quarterComparison.change}
                    </p>
                    {React.createElement(
                  getTrendIcon(
                    quarterComparison.current,
                    quarterComparison.previous
                  ).icon,
                  {
                    className: cn(
                      "h-6 w-6",
                      getTrendIcon(
                        quarterComparison.current,
                        quarterComparison.previous
                      ).color
                    )
                  }
                )}
                  </div>
                  <p className="text-sm text-slate-400">
                    相比上季度 {quarterComparison.percentChange}%
                  </p>
            </>
            }
            </div>
          </div>

          {/* 评分构成 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 部门经理评分 */}
            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-400">部门经理评分</span>
                <span className="text-sm text-slate-500">(权重 50%)</span>
              </div>
              <p className="text-3xl font-bold text-blue-400">
                {latestScore.deptScore}
              </p>
            </div>

            {/* 项目经理评分 */}
            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-400">项目经理评分</span>
                <span className="text-sm text-slate-500">(权重 50%)</span>
              </div>
              <div className="space-y-2">
                {latestScore.projectScores.map((ps, idx) =>
              <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">
                      {ps.projectName}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-purple-400">
                        {ps.score}
                      </span>
                      <span className="text-xs text-slate-500">
                        ({ps.weight}%)
                      </span>
                    </div>
              </div>
              )}
              </div>
            </div>
          </div>
      </div>
      }

      {/* 季度趋势图 */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-xl font-bold text-white mb-6">季度绩效趋势</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {quarterlyTrend.map((item, idx) =>
          <div
            key={idx}
            className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors">

              <p className="text-sm text-slate-400 mb-2">{item.quarter}</p>
              <p
              className={cn(
                "text-2xl font-bold mb-1",
                getLevelInfo(item.level).color
              )}>

                {item.score}
              </p>
              <span
              className={cn(
                "inline-block px-2 py-0.5 rounded text-xs font-medium",
                getLevelInfo(item.level).color,
                getLevelInfo(item.level).bgColor
              )}>

                {item.level}级
              </span>
          </div>
          )}
        </div>
      </div>
    </motion.div>);

};