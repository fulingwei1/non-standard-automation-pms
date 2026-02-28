import React from "react";
import { motion } from "framer-motion";
import { getStatusBadge, getLevelInfo } from "../../utils/performanceUtils";
import { cn } from "../../lib/utils";

/**
 * 历史记录Tab组件
 */
export const HistoryTab = ({ history }) => {
  return (
    <motion.div
      key="history"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="p-6 border-b border-slate-700/50">
          <h3 className="text-xl font-bold text-white">月度绩效记录</h3>
          <p className="text-sm text-slate-400 mt-1">
            共 {history.length} 条记录
          </p>
        </div>

        <div className="divide-y divide-slate-700/50">
          {history.map((record, index) => (
            <motion.div
              key={record.period}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-6 hover:bg-slate-700/20 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="text-lg font-bold text-white mb-1">
                    {record.period.split("-")[0]}年{record.period.split("-")[1]}
                    月
                  </h4>
                  <p className="text-sm text-slate-400">
                    提交时间: {record.submitDate}
                  </p>
                </div>
                <span
                  className={cn(
                    "px-4 py-2 rounded-full text-sm font-medium",
                    getStatusBadge(record.status).color,
                  )}
                >
                  {getStatusBadge(record.status).label}
                </span>
              </div>

              {record.status === "COMPLETED" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-900/30 rounded-lg">
                  <div>
                    <p className="text-xs text-slate-400 mb-2">综合得分</p>
                    <div className="flex items-baseline gap-2">
                      <p
                        className={cn(
                          "text-3xl font-bold",
                          getLevelInfo(record.level).color,
                        )}
                      >
                        {record.totalScore}
                      </p>
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-xs font-medium",
                          getLevelInfo(record.level).color,
                          getLevelInfo(record.level).bgColor,
                        )}
                      >
                        {record.level}级
                      </span>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-slate-400 mb-2">部门经理评分</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {record.deptScore}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-slate-400 mb-2">项目经理评分</p>
                    {(record.projectScores || []).map((ps, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between text-sm mb-1"
                      >
                        <span className="text-slate-400">{ps.projectName}</span>
                        <span className="text-purple-400 font-medium">
                          {ps.score} ({ps.weight}%)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};
