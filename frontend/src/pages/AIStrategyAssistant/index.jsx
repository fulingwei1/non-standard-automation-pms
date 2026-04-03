/**
 * AI 辅助战略管理助手
 * 向导式页面：战略分析 → 战略分解 → 年度经营计划 → 部门工作分解
 */
import { useState } from "react";
import { Brain } from "lucide-react";
import { PageHeader } from "@/components/layout";
import { aiStrategyApi } from "@/services/api/aiStrategy";
import { DEFAULT_COMPANY_INFO } from "./constants";
import StepNav from "./StepNav";
import LoadingOverlay from "./LoadingOverlay";
import Step1Analysis from "./Step1Analysis";
import Step2Decompose from "./Step2Decompose";
import Step3AnnualPlan from "./Step3AnnualPlan";
import Step4DeptObjectives from "./Step4DeptObjectives";

export default function AIStrategyAssistant() {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("");

  // Step 1 数据
  const [analysisInput, setAnalysisInput] = useState({
    companyInfo: `${DEFAULT_COMPANY_INFO.name}，专注于${DEFAULT_COMPANY_INFO.industry}领域，主要产品包括${DEFAULT_COMPANY_INFO.products}。`,
    financialData: "",
    marketInfo: "",
    challenges: "",
  });
  const [analysisResult, setAnalysisResult] = useState(null);

  // Step 2 数据
  const [decomposeInput, setDecomposeInput] = useState({
    strategyName: "",
    strategyVision: "",
    strategyYear: new Date().getFullYear(),
    industry: DEFAULT_COMPANY_INFO.industry,
  });
  const [decomposeResult, setDecomposeResult] = useState(null);

  // Step 3 数据
  const [annualPlanInput, setAnnualPlanInput] = useState({
    companyInfo: `${DEFAULT_COMPANY_INFO.name}，专注于${DEFAULT_COMPANY_INFO.industry}领域，主要产品包括${DEFAULT_COMPANY_INFO.products}。`,
    year: new Date().getFullYear(),
    revenueTarget: 0,
    additionalInfo: "",
  });
  const [annualPlanResult, setAnnualPlanResult] = useState(null);

  // Step 4 数据
  const [deptObjectivesInput, setDeptObjectivesInput] = useState({
    departmentName: "",
    departmentRole: "",
    year: new Date().getFullYear(),
  });
  const [deptObjectivesResult, setDeptObjectivesResult] = useState(null);

  // ============================================
  // AI 调用函数
  // ============================================

  const handleAnalyze = async () => {
    setLoading(true);
    setLoadingMessage("AI 正在分析战略环境...");
    try {
      const res = await aiStrategyApi.analyze(analysisInput);
      setAnalysisResult(res);
    } catch (error) {
      console.error("战略分析失败:", error);
      alert("战略分析失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
      setLoadingMessage("");
    }
  };

  const handleDecompose = async () => {
    setLoading(true);
    setLoadingMessage("AI 正在分解战略到 BSC 四维度...");
    try {
      const res = await aiStrategyApi.decompose(decomposeInput);
      setDecomposeResult(res);
    } catch (error) {
      console.error("战略分解失败:", error);
      alert("战略分解失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
      setLoadingMessage("");
    }
  };

  const handleAnnualPlan = async () => {
    setLoading(true);
    setLoadingMessage("AI 正在制定年度经营计划...");
    try {
      const res = await aiStrategyApi.annualPlan(annualPlanInput);
      setAnnualPlanResult(res);
    } catch (error) {
      console.error("年度计划生成失败:", error);
      alert("年度计划生成失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
      setLoadingMessage("");
    }
  };

  const handleDeptObjectives = async () => {
    setLoading(true);
    setLoadingMessage("AI 正在生成部门 OKR 目标...");
    try {
      const res = await aiStrategyApi.deptObjectives(deptObjectivesInput);
      setDeptObjectivesResult(res);
    } catch (error) {
      console.error("部门目标生成失败:", error);
      alert("部门目标生成失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
      setLoadingMessage("");
    }
  };

  // ============================================
  // 应用到数据库
  // ============================================

  const handleApplyDecompose = async () => {
    if (!decomposeResult) return;
    setLoading(true);
    try {
      await aiStrategyApi.apply("csf", decomposeResult, null);
      alert("战略分解已成功导入系统！");
    } catch (error) {
      console.error("导入失败:", error);
      alert("导入失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAnnualPlan = async () => {
    if (!annualPlanResult) return;
    setLoading(true);
    try {
      await aiStrategyApi.apply("annual_work", annualPlanResult, null);
      alert("重点工作已成功导入系统！");
    } catch (error) {
      console.error("导入失败:", error);
      alert("导入失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleApplyDeptObjectives = async () => {
    if (!deptObjectivesResult) return;
    setLoading(true);
    try {
      await aiStrategyApi.apply("dept_objective", {
        ...deptObjectivesResult,
        department_name: deptObjectivesInput.departmentName,
      }, null);
      alert("部门 OKR 已成功导入系统！");
    } catch (error) {
      console.error("导入失败:", error);
      alert("导入失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // 导航函数
  // ============================================

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleAdoptAndContinue = () => {
    if (analysisResult?.strategic_directions?.[0]) {
      setDecomposeInput({
        ...decomposeInput,
        strategyName: analysisResult.strategic_directions[0].direction,
        strategyVision: analysisResult.strategic_positioning,
      });
    }
    nextStep();
  };

  // ============================================
  // 主渲染
  // ============================================

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <PageHeader
        title="AI 辅助战略管理助手"
        description="从战略分析到部门 OKR，AI 全流程辅助"
        icon={Brain}
      />

      <div className="max-w-6xl mx-auto p-6">
        <StepNav currentStep={currentStep} />

        <div className="mt-8">
          {currentStep === 1 && (
            <Step1Analysis
              analysisInput={analysisInput}
              setAnalysisInput={setAnalysisInput}
              analysisResult={analysisResult}
              loading={loading}
              onAnalyze={handleAnalyze}
              onAdoptAndContinue={handleAdoptAndContinue}
            />
          )}
          {currentStep === 2 && (
            <Step2Decompose
              decomposeInput={decomposeInput}
              setDecomposeInput={setDecomposeInput}
              decomposeResult={decomposeResult}
              loading={loading}
              onDecompose={handleDecompose}
              onApply={handleApplyDecompose}
              onPrev={prevStep}
              onNext={nextStep}
            />
          )}
          {currentStep === 3 && (
            <Step3AnnualPlan
              annualPlanInput={annualPlanInput}
              setAnnualPlanInput={setAnnualPlanInput}
              annualPlanResult={annualPlanResult}
              loading={loading}
              onGenerate={handleAnnualPlan}
              onApply={handleApplyAnnualPlan}
              onPrev={prevStep}
              onNext={nextStep}
            />
          )}
          {currentStep === 4 && (
            <Step4DeptObjectives
              deptObjectivesInput={deptObjectivesInput}
              setDeptObjectivesInput={setDeptObjectivesInput}
              deptObjectivesResult={deptObjectivesResult}
              loading={loading}
              onGenerate={handleDeptObjectives}
              onApply={handleApplyDeptObjectives}
              onPrev={prevStep}
            />
          )}
        </div>
      </div>

      {loading && <LoadingOverlay message={loadingMessage} />}
    </div>
  );
}
