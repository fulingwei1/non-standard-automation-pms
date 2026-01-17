import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { ClipboardList, AlertCircle } from "lucide-react";
import { useEvaluationTasks } from "../hooks/useEvaluationTasks";
import { TaskStatistics } from "../components/evaluation/TaskStatistics";
import { TaskFilters } from "../components/evaluation/TaskFilters";
import { TaskItem } from "../components/evaluation/TaskItem";

const EvaluationTaskList = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [periodFilter, setPeriodFilter] = useState("2025-01");

  // 获取当前用户信息
  const currentUser = useMemo(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (e) {
        console.error("解析用户信息失败:", e);
      }
    }
    return {
      id: 1,
      name: "李经理",
      role: "dept_manager",
      department: "技术开发部",
      projects: ["项目A", "项目B"]
    };
  }, []);

  // 使用自定义Hook管理任务数据
  const { filteredTasks, statistics, availablePeriods, isLoading, error: _error } =
  useEvaluationTasks(
    periodFilter,
    statusFilter,
    searchTerm,
    typeFilter,
    []
  );

  // 处理评价
  const handleEvaluate = (task) => {
    navigate(`/evaluation/${task.id}`, { state: { task } });
  };

  // 动画配置
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-7xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}>

        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                绩效评价任务
              </h1>
              <p className="text-slate-400">
                {currentUser.role === "dept_manager" ? "部门成员" : "项目成员"}
                绩效评价和打分
              </p>
            </div>
            <ClipboardList className="h-12 w-12 text-blue-400" />
          </div>
        </motion.div>

        {/* 统计卡片 */}
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <TaskStatistics statistics={statistics} />
        </motion.div>

        {/* 筛选和搜索栏 */}
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <TaskFilters
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            periodFilter={periodFilter}
            setPeriodFilter={setPeriodFilter}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            typeFilter={typeFilter}
            setTypeFilter={setTypeFilter}
            availablePeriods={availablePeriods} />

        </motion.div>

        {/* 任务列表 */}
        <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
          <div className="space-y-4">
            {isLoading ?
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-12 border border-slate-700/50 text-center">
                <div className="animate-spin h-12 w-12 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-slate-400">加载中...</p>
              </div> :
            filteredTasks.length === 0 ?
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-12 border border-slate-700/50 text-center">
                <AlertCircle className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">暂无评价任务</p>
              </div> :

            filteredTasks.map((task, index) =>
            <TaskItem
              key={task.id}
              task={task}
              index={index}
              onEvaluate={handleEvaluate} />

            )
            }
          </div>
        </motion.div>

        {/* 提示信息 */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300 space-y-1">
                <p className="font-medium text-white mb-2">评价说明：</p>
                <p>• 请在截止日期前完成所有待评价任务</p>
                <p>• 评分范围：60-100分，建议参考员工工作表现客观评分</p>
                <p>• 部门经理评价权重默认50%，项目经理评价权重默认50%</p>
                <p>• 员工最终得分 = 部门经理评分 × 50% + 项目经理评分 × 50%</p>
                <p>• 评价意见将反馈给员工，请认真填写建设性意见</p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>);

};

export default EvaluationTaskList;