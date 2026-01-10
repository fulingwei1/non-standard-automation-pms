import { History, Users, Briefcase } from "lucide-react";
import { fadeIn } from "../../utils/weightConfigUtils";
import { motion } from "framer-motion";

/**
 * 配置历史记录组件
 */
export const ConfigHistory = ({ history }) => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="p-6 border-b border-slate-700/50">
          <div className="flex items-center gap-3">
            <History className="h-5 w-5 text-slate-400" />
            <h3 className="text-xl font-bold text-white">配置历史记录</h3>
          </div>
        </div>

        <div className="divide-y divide-slate-700/50">
          {history.map((record, index) => (
            <motion.div
              key={record.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="p-6 hover:bg-slate-700/20 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-2">
                    <span className="text-white font-medium">
                      {record.date}
                    </span>
                    <span className="text-slate-400">·</span>
                    <span className="text-slate-400">{record.operator}</span>
                  </div>
                  <div className="flex items-center gap-6 text-sm text-slate-300 mb-2">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-blue-400" />
                      <span>部门经理 {record.deptWeight}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Briefcase className="h-4 w-4 text-purple-400" />
                      <span>项目经理 {record.projectWeight}%</span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-400">{record.reason}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};
