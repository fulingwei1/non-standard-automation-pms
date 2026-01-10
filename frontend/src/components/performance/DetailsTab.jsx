import React from "react";
import { motion } from "framer-motion";
import { MessageSquare } from "lucide-react";
import { getLevelInfo } from "../../utils/performanceUtils";
import { cn } from "../../lib/utils";

/**
 * 评价详情Tab组件
 */
export const DetailsTab = ({ history }) => {
  const recordsWithComments = history.filter(
    (record) => record.comments && record.comments.length > 0,
  );

  if (recordsWithComments.length === 0) {
    return (
      <motion.div
        key="details"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-4"
      >
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-12 border border-slate-700/50 text-center">
          <MessageSquare className="h-12 w-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">暂无评价详情</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      key="details"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      {recordsWithComments.map((record, index) => (
        <motion.div
          key={record.period}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50"
        >
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-bold text-white">
              {record.period.split("-")[0]}年{record.period.split("-")[1]}月
              评价
            </h4>
            <span
              className={cn(
                "px-3 py-1 rounded-full text-sm font-medium",
                getLevelInfo(record.level).color,
                getLevelInfo(record.level).bgColor,
              )}
            >
              综合得分: {record.totalScore} ({record.level}级)
            </span>
          </div>

          <div className="space-y-4">
            {record.comments.map((comment, idx) => (
              <div
                key={idx}
                className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                      <span className="text-white font-bold">
                        {comment.evaluator.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <p className="text-white font-medium">
                        {comment.evaluator}
                      </p>
                      <p className="text-sm text-slate-400">{comment.role}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-400">
                      {comment.score}
                    </p>
                    <p className="text-xs text-slate-400">评分</p>
                  </div>
                </div>
                <div className="pl-13">
                  <p className="text-slate-300 leading-relaxed">
                    {comment.comment}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
};
