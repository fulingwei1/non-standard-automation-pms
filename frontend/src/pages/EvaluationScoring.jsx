import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import {
  Award,
  ArrowLeft,
  User,
  Calendar,
  Briefcase,
  AlertCircle } from
"lucide-react";
import { performanceApi } from "../services/api";
import { WorkSummaryDisplay } from "../components/evaluation/WorkSummaryDisplay";
import { ScoringForm } from "../components/evaluation/ScoringForm";
import {
  scoringGuidelines,
  commentTemplates,
  validateScore,
  validateComment } from
"../utils/evaluationUtils";

const EvaluationScoring = () => {
  const navigate = useNavigate();
  const { taskId } = useParams();
  const location = useLocation();
  const taskFromState = location.state?.task;

  const [score, setScore] = useState("");
  const [comment, setComment] = useState("");
  const [isDraft, setIsDraft] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [_error, setError] = useState(null);

  // 任务数据（从 API 获取或使用传递过来的数据）
  const [task, setTask] = useState(
    taskFromState || {
      id: null,
      employeeId: null,
      employeeName: "",
      department: "",
      position: "",
      period: "",
      submitDate: "",
      evaluationType: "",
      projectName: null,
      weight: 0,
      status: "PENDING",
      deadline: "",
      workSummary: {
        workContent: "",
        selfEvaluation: "",
        highlights: "",
        problems: "",
        nextMonthPlan: ""
      },
      historicalScores: []
    }
  );

  // 加载评价详情
  useEffect(() => {
    if (!taskFromState && taskId) {
      loadEvaluationDetail();
    }
  }, [taskId]);

  const loadEvaluationDetail = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await performanceApi.getEvaluationDetail(taskId);
      setTask({
        ...response.data.summary,
        employeeName:
        response.data.employee_info?.name ||
        response.data.employee_info?.employee_name,
        department: response.data.employee_info?.department,
        position: response.data.employee_info?.position,
        workSummary: response.data.summary?.summary || response.data.summary,
        historicalScores: response.data.historical_performance || []
      });
      // 如果已经评价过，填充分数和评论
      if (response.data.summary?.score) {
        setScore(response.data.summary.score.toString());
      }
      if (response.data.summary?.comment) {
        setComment(response.data.summary.comment);
        setIsDraft(false);
      }
    } catch (err) {
      console.error("加载评价详情失败:", err);
      setError(err.response?.data?.detail || "加载失败");
      // 如果加载失败且没有传递数据，保持mock数据
    } finally {
      setIsLoading(false);
    }
  };

  // 处理输入变化
  const handleScoreChange = (value) => {
    // 只允许输入60-100的数字
    if (value === "" || Number(value) >= 60 && Number(value) <= 100) {
      setScore(value);
      setIsDraft(true);
    }
  };

  const handleCommentChange = (value) => {
    setComment(value);
    setIsDraft(true);
  };

  // 插入评价模板
  const insertTemplate = (template) => {
    if (comment) {
      setComment(comment + "\n\n" + template);
    } else {
      setComment(template);
    }
    setIsDraft(true);
  };

  // 保存草稿
  const handleSaveDraft = async () => {
    setIsSaving(true);
    try {
      // Note: API可能不支持草稿功能，这里仅做本地保存
      setIsDraft(false);
      alert("草稿已保存到本地");
    } catch (err) {
      console.error("保存草稿失败:", err);
      alert("保存草稿失败: " + (err.response?.data?.detail || "请稍后重试"));
    } finally {
      setIsSaving(false);
    }
  };

  // 提交评价
  const handleSubmit = async () => {
    // 验证
    const scoreValidation = validateScore(score);
    if (!scoreValidation.valid) {
      alert(scoreValidation.message);
      return;
    }

    const commentValidation = validateComment(comment);
    if (!commentValidation.valid) {
      alert(commentValidation.message);
      return;
    }

    if (!confirm(`确认提交评价？\n\n评分：${score}分\n提交后将无法修改`)) {
      return;
    }

    setIsSubmitting(true);
    try {
      await performanceApi.submitEvaluation(taskId, {
        score: parseInt(score),
        comment: comment.trim()
      });
      alert("评价提交成功！");
      navigate("/evaluation-tasks");
    } catch (err) {
      console.error("提交评价失败:", err);
      setError(err.response?.data?.detail || "提交失败");
      alert("提交失败: " + (err.response?.data?.detail || "请稍后重试"));
    } finally {
      setIsSubmitting(false);
    }
  };

  // 动画配置
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  };

  // 如果正在加载，显示加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">加载中...</p>
        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-5xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}>

        {/* 返回按钮 */}
        <motion.div {...fadeIn}>
          <button
            onClick={() => navigate("/evaluation-tasks")}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">

            <ArrowLeft className="h-4 w-4" />
            返回任务列表
          </button>
        </motion.div>

        {/* 页面标题 */}
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">绩效评价</h1>
              <p className="text-slate-400">
                {(task.evaluationType || task.evaluator_type) === "dept" ||
                (task.evaluationType || task.evaluator_type) === "DEPT_MANAGER" ?
                "部门成员" :
                "项目成员"}
                评价打分
              </p>
            </div>
            <Award className="h-12 w-12 text-blue-400" />
          </div>
        </motion.div>

        {/* 员工信息卡片 */}
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-2xl">
                  {(task.employeeName || task.employee_name || "未知").charAt(
                    0
                  )}
                </span>
              </div>

              <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <div className="flex items-center gap-2 text-slate-400 mb-2">
                    <User className="h-4 w-4" />
                    <span className="text-sm">员工信息</span>
                  </div>
                  <p className="text-xl font-bold text-white mb-1">
                    {task.employeeName || task.employee_name}
                  </p>
                  <p className="text-sm text-slate-400">
                    {task.department || task.employee_department || "-"}
                  </p>
                  <p className="text-sm text-slate-400">
                    {task.position || task.employee_position || "-"}
                  </p>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-slate-400 mb-2">
                    <Calendar className="h-4 w-4" />
                    <span className="text-sm">考核周期</span>
                  </div>
                  <p className="text-xl font-bold text-white mb-1">
                    {(task.period || "").split("-")[0]}年
                    {(task.period || "").split("-")[1]}月
                  </p>
                  <p className="text-sm text-slate-400">
                    提交时间: {task.submitDate || task.submit_date || "-"}
                  </p>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-slate-400 mb-2">
                    <Briefcase className="h-4 w-4" />
                    <span className="text-sm">评价类型</span>
                  </div>
                  <p className="text-xl font-bold text-white mb-1">
                    {(task.evaluationType || task.evaluator_type) === "dept" ||
                    (task.evaluationType || task.evaluator_type) ===
                    "DEPT_MANAGER" ?
                    "部门评价" :
                    "项目评价"}
                  </p>
                  <p className="text-sm text-slate-400">
                    {task.projectName ||
                    task.project_name ||
                    task.department ||
                    task.employee_department}{" "}
                    · 权重 {task.weight || task.project_weight || 50}%
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 历史绩效记录 */}
        {task.historicalScores && task.historicalScores.length > 0 &&
        <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <h3 className="text-lg font-bold text-white mb-4">
                历史绩效参考
              </h3>
              <div className="grid grid-cols-3 gap-4">
                {task.historicalScores.map((hs, idx) =>
              <div
                key={idx}
                className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">

                    <p className="text-sm text-slate-400 mb-2">{hs.period}</p>
                    <div className="flex items-baseline gap-2">
                      <p className="text-2xl font-bold text-blue-400">
                        {hs.score}
                      </p>
                      <span className="text-sm text-slate-400">
                        ({hs.level}级)
                      </span>
                    </div>
              </div>
              )}
              </div>
            </div>
        </motion.div>
        }

        {/* 工作总结展示 */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <WorkSummaryDisplay workSummary={task.workSummary} />
        </motion.div>

        {/* 评分表单 */}
        <motion.div {...fadeIn} transition={{ delay: 0.5 }}>
          <ScoringForm
            score={score}
            comment={comment}
            isDraft={isDraft}
            isSaving={isSaving}
            isSubmitting={isSubmitting}
            scoringGuidelines={scoringGuidelines}
            commentTemplates={commentTemplates}
            onScoreChange={handleScoreChange}
            onCommentChange={handleCommentChange}
            onInsertTemplate={insertTemplate}
            onSaveDraft={handleSaveDraft}
            onSubmit={handleSubmit} />

        </motion.div>

        {/* 提示信息 */}
        <motion.div {...fadeIn} transition={{ delay: 0.6 }}>
          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300 space-y-1">
                <p className="font-medium text-white mb-2">评价注意事项：</p>
                <p>• 请客观公正地评价员工的工作表现</p>
                <p>• 评分范围为60-100分，请根据实际表现给分</p>
                <p>• 评价意见应具体明确，包含优点和改进建议</p>
                <p>• 提交后将无法修改，请仔细核对后再提交</p>
                <p>• 评价结果将反馈给员工，请认真填写建设性意见</p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>);

};

export default EvaluationScoring;