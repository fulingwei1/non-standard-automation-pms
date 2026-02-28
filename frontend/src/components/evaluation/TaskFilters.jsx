import React from "react";
import { Search } from "lucide-react";

/**
 * 任务筛选器组件
 */
export const TaskFilters = ({
  searchTerm,
  setSearchTerm,
  periodFilter,
  setPeriodFilter,
  statusFilter,
  setStatusFilter,
  typeFilter,
  setTypeFilter,
  availablePeriods = [],
}) => {
  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50">
      <div className="flex flex-col md:flex-row gap-4">
        {/* 搜索框 */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="搜索员工姓名..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* 周期选择 */}
        <select
          value={periodFilter}
          onChange={(e) => setPeriodFilter(e.target.value)}
          className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          {(availablePeriods || []).map((period) => (
            <option key={period} value={period}>
              {period.split("-")[0]}年{period.split("-")[1]}月
            </option>
          ))}
        </select>

        {/* 状态筛选 */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="all">全部状态</option>
          <option value="pending">待评价</option>
          <option value="completed">已完成</option>
        </select>

        {/* 类型筛选 */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          <option value="all">全部类型</option>
          <option value="dept">部门评价</option>
          <option value="project">项目评价</option>
        </select>
      </div>
    </div>
  );
};
