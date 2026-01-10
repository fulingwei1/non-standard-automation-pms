import React, { useEffect } from "react";
import { motion } from "framer-motion";
import { FileText } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useMonthlySummary } from "../hooks/useMonthlySummary";
import { fadeIn } from "../utils/monthlySummaryUtils";
import { PeriodInfoCard } from "../components/monthlySummary/PeriodInfoCard";
import { SummaryForm } from "../components/monthlySummary/SummaryForm";
import { HistoryList } from "../components/monthlySummary/HistoryList";
import { TipsCard } from "../components/monthlySummary/TipsCard";

const MonthlySummary = () => {
  const navigate = useNavigate();

  // 获取当前用户信息
  const currentUser = JSON.parse(
    localStorage.getItem("user") ||
      '{"name":"用户","department":"未知部门","position":"未知职位"}',
  );

  const {
    currentPeriod,
    formData,
    isDraft,
    isSaving,
    isSubmitting,
    showHistory,
    setShowHistory,
    isLoading,
    history,
    error,
    handleInputChange,
    loadHistory,
    handleSaveDraft,
    handleSubmit,
  } = useMonthlySummary();

  // 页面加载时加载历史记录
  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 提交处理（需要 navigate）
  const onSubmit = () => {
    handleSubmit(navigate);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-5xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                月度工作总结
              </h1>
              <p className="text-slate-400">
                记录本月工作成果，为绩效评价提供依据
              </p>
            </div>
            <FileText className="h-12 w-12 text-blue-400" />
          </div>
        </motion.div>

        {/* 当前周期信息卡片 */}
        <PeriodInfoCard currentPeriod={currentPeriod} />

        {/* 表单主体 */}
        <SummaryForm
          currentUser={currentUser}
          formData={formData}
          isDraft={isDraft}
          isSaving={isSaving}
          isSubmitting={isSubmitting}
          error={error}
          onInputChange={handleInputChange}
          onSaveDraft={handleSaveDraft}
          onSubmit={onSubmit}
        />

        {/* 历史记录 */}
        <HistoryList
          showHistory={showHistory}
          onToggle={() => setShowHistory(!showHistory)}
          isLoading={isLoading}
          history={history}
        />

        {/* 提示信息 */}
        <TipsCard />
      </motion.div>
    </div>
  );
};

export default MonthlySummary;
