import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Award,
  Calendar,
  MessageSquare,
  Download,
  AlertCircle } from
"lucide-react";
import { cn } from "../lib/utils";
import { usePerformanceData } from "../hooks/usePerformanceData";
import { OverviewTab } from "../components/performance/OverviewTab";
import { HistoryTab } from "../components/performance/HistoryTab";
import { DetailsTab } from "../components/performance/DetailsTab";

// Fallback mock data
const mockMonthlyHistory = [];

const performanceOverview = {
  currentPeriod: {
    year: 2025,
    quarter: 1,
    status: "EVALUATING",
    submitDate: "2025-01-28",
    deptEvaluation: {
      status: "PENDING",
      evaluator: "李经理",
      score: null
    },
    projectEvaluations: [
    {
      projectId: 1,
      projectName: "项目A",
      status: "COMPLETED",
      evaluator: "王经理",
      score: 92,
      weight: 60
    },
    {
      projectId: 2,
      projectName: "项目B",
      status: "PENDING",
      evaluator: "刘经理",
      score: null,
      weight: 40
    }]

  },
  latestScore: {
    period: "2024-Q4",
    totalScore: 90,
    level: "A",
    rank: 5,
    totalEmployees: 48,
    deptScore: 88,
    projectScores: [
    { projectName: "项目A", score: 92, weight: 60 },
    { projectName: "项目C", score: 85, weight: 40 }]

  },
  quarterlyTrend: [
  { quarter: "2024-Q1", score: 85, level: "B" },
  { quarter: "2024-Q2", score: 88, level: "B" },
  { quarter: "2024-Q3", score: 87, level: "B" },
  { quarter: "2024-Q4", score: 90, level: "A" }]

};

const fallbackData = {
  current_status: performanceOverview.currentPeriod,
  latest_result: performanceOverview.latestScore,
  quarterly_trend: performanceOverview.quarterlyTrend,
  history: mockMonthlyHistory
};

const MyPerformance = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const { performanceData, isLoading: _isLoading, error: _error } =
  usePerformanceData(fallbackData);

  // 获取当前用户信息
  const rawUser = JSON.parse(
    localStorage.getItem("user") ||
      '{"name":"用户","department":"未知部门","position":"未知职位"}',
  );
  const displayName =
    rawUser.real_name ||
    rawUser.username ||
    rawUser.name ||
    "用户";
  const department =
    rawUser.department ||
    rawUser.department_name ||
    "未知部门";
  const position =
    rawUser.position ||
    rawUser.role ||
    "未知职位";

  // 使用加载的数据或fallback到mock
  const currentData = performanceData || fallbackData;

  // 动画配置
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-6xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}>

        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">我的绩效</h1>
              <p className="text-slate-400">查看个人绩效评价结果和历史记录</p>
            </div>
            <button className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg font-medium transition-colors flex items-center gap-2">
              <Download className="h-4 w-4" />
              导出报告
            </button>
          </div>
        </motion.div>

        {/* 个人信息卡片 */}
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-blue-500/20">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                <span className="text-white font-bold text-2xl">
                  {displayName.charAt(0)}
                </span>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white mb-1">
                  {displayName}
                </h2>
                <p className="text-slate-400">
                  {department} · {position}
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Tab 导航 */}
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <div className="flex gap-2">
            {[
            { key: "overview", label: "绩效概览", icon: Award },
            { key: "history", label: "历史记录", icon: Calendar },
            { key: "details", label: "评价详情", icon: MessageSquare }].
            map((tab) =>
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                "px-6 py-3 rounded-lg font-medium transition-all flex items-center gap-2",
                activeTab === tab.key ?
                "bg-blue-500 text-white" :
                "bg-slate-800/50 text-slate-400 hover:text-white hover:bg-slate-700/50"
              )}>

                <tab.icon className="h-4 w-4" />
                {tab.label}
            </button>
            )}
          </div>
        </motion.div>

        {/* Tab 内容 */}
        {activeTab === "overview" &&
        <OverviewTab
          currentPeriod={
          currentData.current_status || currentData.currentPeriod
          }
          latestScore={currentData.latest_result || currentData.latestScore}
          quarterlyTrend={
          currentData.quarterly_trend || currentData.quarterlyTrend
          } />

        }

        {activeTab === "history" &&
        <HistoryTab history={currentData.history || mockMonthlyHistory} />
        }

        {activeTab === "details" &&
        <DetailsTab history={currentData.history || mockMonthlyHistory} />
        }

        {/* 提示信息 */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300 space-y-1">
                <p className="font-medium text-white mb-2">绩效评价说明：</p>
                <p>• 每月需在月底前提交工作总结，逾期将影响绩效评价</p>
                <p>• 综合得分 = 部门经理评分 × 50% + 项目经理评分 × 50%</p>
                <p>• 参与多个项目时，项目经理评分按各项目权重加权平均</p>
                <p>• 季度绩效分数 = 三个月分数的加权平均</p>
                <p>• 等级标准：A级(90-100) B级(80-89) C级(70-79) D级(60-69)</p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>);

};

export default MyPerformance;
