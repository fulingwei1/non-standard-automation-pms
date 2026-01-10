import React from "react";
import { ClipboardList, Clock, CheckCircle2, Users, Award } from "lucide-react";

/**
 * 任务统计卡片组件
 */
export const TaskStatistics = ({ statistics }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-xl p-4 border border-blue-500/20">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <ClipboardList className="h-4 w-4" />
          <span className="text-sm">总任务</span>
        </div>
        <p className="text-3xl font-bold text-white">{statistics.total}</p>
      </div>

      <div className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 rounded-xl p-4 border border-amber-500/20">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <Clock className="h-4 w-4" />
          <span className="text-sm">待评价</span>
        </div>
        <p className="text-3xl font-bold text-amber-400">
          {statistics.pending}
        </p>
      </div>

      <div className="bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 rounded-xl p-4 border border-emerald-500/20">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <CheckCircle2 className="h-4 w-4" />
          <span className="text-sm">已完成</span>
        </div>
        <p className="text-3xl font-bold text-emerald-400">
          {statistics.completed}
        </p>
      </div>

      <div className="bg-gradient-to-br from-purple-500/10 to-purple-500/5 rounded-xl p-4 border border-purple-500/20">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <Users className="h-4 w-4" />
          <span className="text-sm">部门 / 项目</span>
        </div>
        <p className="text-3xl font-bold text-purple-400">
          {statistics.dept} / {statistics.project}
        </p>
      </div>

      <div className="bg-gradient-to-br from-pink-500/10 to-pink-500/5 rounded-xl p-4 border border-pink-500/20">
        <div className="flex items-center gap-2 text-slate-400 mb-2">
          <Award className="h-4 w-4" />
          <span className="text-sm">平均分</span>
        </div>
        <p className="text-3xl font-bold text-pink-400">
          {statistics.avgScore > 0 ? statistics.avgScore.toFixed(1) : "-"}
        </p>
      </div>
    </div>
  );
};
