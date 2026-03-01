/**
 * AI 辅助战略管理助手
 * 向导式页面：战略分析 → 战略分解 → 年度经营计划 → 部门工作分解
 */
import { useState } from "react";
import { motion } from "framer-motion";
import {
  Target,
  TrendingUp,
  Calendar,
  Users,
  ChevronRight,
  Check,
  Sparkles,
  Brain,
  Building2,
  DollarSign,
  Globe,
  AlertTriangle,
  Edit2,
  Trash2,
  Save,
  Upload,
  Plus,
  X,
  ArrowRight,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Label,
} from "@/components/ui";
import { staggerContainer } from "@/lib/animations";
import { aiStrategyApi, getDimensionLabel, getDimensionColor, getPriorityLabel, getPriorityColor } from "@/services/api/aiStrategy";

// 默认公司信息（金凯博）
const DEFAULT_COMPANY_INFO = {
  name: "金凯博自动化测试（深圳）",
  industry: "非标自动化测试设备",
  products: "ICT/FCT/EOL/烧录/老化/视觉检测等测试设备",
};

// 步骤配置
const STEPS = [
  { id: 1, title: "战略分析", icon: Brain, description: "SWOT 分析与战略定位" },
  { id: 2, title: "战略分解", icon: Target, description: "BSC 四维度 CSF+KPI" },
  { id: 3, title: "年度经营计划", icon: Calendar, description: "重点工作规划" },
  { id: 4, title: "部门工作分解", icon: Users, description: "部门 OKR 目标" },
];

// ============================================
// 主组件
// ============================================
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
    companyInfo: analysisInput.companyInfo,
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

  // 部门选项
  const departments = [
    { value: "研发部", role: "负责产品研发、技术创新、技术难题攻关" },
    { value: "销售部", role: "负责市场开拓、客户维护、销售目标达成" },
    { value: "生产部", role: "负责生产计划执行、产品质量控制、交付保障" },
    { value: "采购部", role: "负责供应商管理、物料采购、成本控制" },
    { value: "质量部", role: "负责质量管理体系、来料检验、过程质量控制" },
    { value: "工程部", role: "负责工艺工程、设备维护、技术支持" },
    { value: "财务部", role: "负责财务管理、成本控制、资金规划" },
    { value: "人力资源部", role: "负责人才招聘、培训发展、绩效管理" },
  ];

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

  // ============================================
  // 渲染步骤导航
  // ============================================

  const renderStepNav = () => (
    <div className="flex items-center justify-center mb-8">
      {STEPS.map((step, index) => {
        const StepIcon = step.icon;
        const isActive = currentStep === step.id;
        const isCompleted = currentStep > step.id;

        return (
          <div key={step.id} className="flex items-center">
            <div
              className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                isActive
                  ? "border-blue-500 bg-blue-500/20 text-blue-400"
                  : isCompleted
                  ? "border-green-500 bg-green-500/20 text-green-400"
                  : "border-gray-600 bg-gray-800 text-gray-500"
              }`}
            >
              {isCompleted ? <Check className="w-6 h-6" /> : <StepIcon className="w-5 h-5" />}
            </div>
            <div className="ml-3 text-left">
              <div className={`text-sm font-medium ${isActive ? "text-white" : "text-gray-400"}`}>
                {step.title}
              </div>
              <div className="text-xs text-gray-500">{step.description}</div>
            </div>
            {index < STEPS.length - 1 && (
              <ChevronRight className="w-5 h-5 mx-4 text-gray-600" />
            )}
          </div>
        );
      })}
    </div>
  );

  // ============================================
  // 渲染各步骤内容
  // ============================================

  const renderStep1 = () => (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-400" />
            公司信息输入
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">公司简介</Label>
            <Textarea
              value={analysisInput.companyInfo}
              onChange={(e) => setAnalysisInput({ ...analysisInput, companyInfo: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[100px]"
              placeholder="请输入公司简介，包括主营业务、核心产品、市场定位等"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-gray-300 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-green-400" />
                财务数据
              </Label>
              <Textarea
                value={analysisInput.financialData}
                onChange={(e) => setAnalysisInput({ ...analysisInput, financialData: e.target.value })}
                className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
                placeholder="营收、利润、增长率等"
              />
            </div>
            <div>
              <Label className="text-gray-300 flex items-center gap-2">
                <Globe className="w-4 h-4 text-blue-400" />
                市场信息
              </Label>
              <Textarea
                value={analysisInput.marketInfo}
                onChange={(e) => setAnalysisInput({ ...analysisInput, marketInfo: e.target.value })}
                className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
                placeholder="市场规模、竞争格局、趋势等"
              />
            </div>
          </div>
          <div>
            <Label className="text-gray-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              当前挑战
            </Label>
            <Textarea
              value={analysisInput.challenges}
              onChange={(e) => setAnalysisInput({ ...analysisInput, challenges: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="面临的主要挑战和痛点"
            />
          </div>
          <Button
            onClick={handleAnalyze}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 分析中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 战略分析
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {analysisResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          {/* SWOT 四象限 */}
          <div className="grid grid-cols-2 gap-4">
            <Card className="bg-green-900/20 border-green-700/50">
              <CardHeader>
                <CardTitle className="text-green-400 text-lg">优势 (Strengths)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.strengths?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <Check className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-red-900/20 border-red-700/50">
              <CardHeader>
                <CardTitle className="text-red-400 text-lg">劣势 (Weaknesses)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.weaknesses?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-blue-900/20 border-blue-700/50">
              <CardHeader>
                <CardTitle className="text-blue-400 text-lg">机会 (Opportunities)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.opportunities?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <TrendingUp className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-yellow-900/20 border-yellow-700/50">
              <CardHeader>
                <CardTitle className="text-yellow-400 text-lg">威胁 (Threats)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.threats?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* 战略定位 */}
          <Card className="bg-purple-900/20 border-purple-700/50">
            <CardHeader>
              <CardTitle className="text-purple-400 text-lg">战略定位建议</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-300">{analysisResult.strategic_positioning}</p>
            </CardContent>
          </Card>

          {/* 核心竞争力 */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                核心竞争力分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {analysisResult.core_competencies?.map((item, i) => (
                  <Badge key={i} variant="secondary" className="bg-blue-500/20 text-blue-300 border-blue-500/30">
                    {item}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 战略方向建议 */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">战略方向建议</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {analysisResult.strategic_directions?.map((item, i) => (
                <div key={i} className="p-3 bg-gray-900/50 rounded-lg border border-gray-700">
                  <div className="font-medium text-white mb-1">{item.direction}</div>
                  <div className="text-sm text-gray-400">{item.description}</div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Button
            onClick={() => {
              if (analysisResult.strategic_directions?.[0]) {
                setDecomposeInput({
                  ...decomposeInput,
                  strategyName: analysisResult.strategic_directions[0].direction,
                  strategyVision: analysisResult.strategic_positioning,
                });
              }
              nextStep();
            }}
            className="w-full"
          >
            采纳建议并继续
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </motion.div>
      )}
    </motion.div>
  );

  const renderStep2 = () => (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-400" />
            战略信息
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">战略名称</Label>
            <Input
              value={decomposeInput.strategyName}
              onChange={(e) => setDecomposeInput({ ...decomposeInput, strategyName: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white"
              placeholder="如：2026 年高质量发展战略"
            />
          </div>
          <div>
            <Label className="text-gray-300">战略愿景</Label>
            <Textarea
              value={decomposeInput.strategyVision}
              onChange={(e) => setDecomposeInput({ ...decomposeInput, strategyVision: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="描述战略愿景"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-gray-300">战略年度</Label>
              <Input
                type="number"
                value={decomposeInput.strategyYear}
                onChange={(e) => setDecomposeInput({ ...decomposeInput, strategyYear: parseInt(e.target.value) })}
                className="bg-gray-900 border-gray-700 text-white"
              />
            </div>
            <div>
              <Label className="text-gray-300">行业</Label>
              <Input
                value={decomposeInput.industry}
                onChange={(e) => setDecomposeInput({ ...decomposeInput, industry: e.target.value })}
                className="bg-gray-900 border-gray-700 text-white"
              />
            </div>
          </div>
          <Button
            onClick={handleDecompose}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 分解中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 战略分解
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {decomposeResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">BSC 四维度分解结果</h3>
            <Button onClick={handleApplyDecompose} size="sm" variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              导入系统
            </Button>
          </div>

          {decomposeResult.csfs?.map((csf, csfIndex) => (
            <Card key={csfIndex} className={`border-l-4 ${getDimensionColor(csf.dimension).split(" ")[2]}`}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Badge className={getDimensionColor(csf.dimension)}>
                      {getDimensionLabel(csf.dimension)}
                    </Badge>
                    <span>{csf.name}</span>
                  </CardTitle>
                  <Badge variant="secondary" className="bg-gray-700 text-gray-300">
                    权重：{csf.weight}%
                  </Badge>
                </div>
                <p className="text-sm text-gray-400 mt-2">{csf.description}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {csf.kpis?.map((kpi, kpiIndex) => (
                    <div key={kpiIndex} className="p-3 bg-gray-900/50 rounded-lg border border-gray-700">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-blue-300">{kpi.name}</div>
                        <Badge variant="outline" className="text-xs">
                          {kpi.ipooc_type}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-400">{kpi.description}</div>
                      <div className="flex flex-wrap gap-2 mt-2 text-xs">
                        <Badge variant="secondary">目标：{kpi.target_value} {kpi.unit}</Badge>
                        <Badge variant="secondary">基线：{kpi.baseline_value}</Badge>
                        <Badge variant="secondary">方向：{kpi.direction === "UP" ? "↑" : "↓"}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}

          <div className="flex gap-4">
            <Button onClick={prevStep} variant="outline" className="flex-1">
              <ArrowLeft className="w-4 h-4 mr-2" />
              上一步
            </Button>
            <Button onClick={nextStep} className="flex-1">
              下一步
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );

  const renderStep3 = () => (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-400" />
            年度经营计划输入
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">年度</Label>
            <Input
              type="number"
              value={annualPlanInput.year}
              onChange={(e) => setAnnualPlanInput({ ...annualPlanInput, year: parseInt(e.target.value) })}
              className="bg-gray-900 border-gray-700 text-white"
            />
          </div>
          <div>
            <Label className="text-gray-300">年度营收目标（万元）</Label>
            <Input
              type="number"
              value={annualPlanInput.revenueTarget}
              onChange={(e) => setAnnualPlanInput({ ...annualPlanInput, revenueTarget: parseFloat(e.target.value) })}
              className="bg-gray-900 border-gray-700 text-white"
              placeholder="如：50000"
            />
          </div>
          <div>
            <Label className="text-gray-300">补充信息</Label>
            <Textarea
              value={annualPlanInput.additionalInfo}
              onChange={(e) => setAnnualPlanInput({ ...annualPlanInput, additionalInfo: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="其他需要说明的信息"
            />
          </div>
          <Button
            onClick={handleAnnualPlan}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 生成年度计划
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {annualPlanResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">重点工作（{annualPlanResult.annual_works?.length || 0}项）</h3>
            <Button onClick={handleApplyAnnualPlan} size="sm" variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              导入系统
            </Button>
          </div>

          <div className="grid gap-4">
            {annualPlanResult.annual_works?.map((work, i) => (
              <Card key={i} className="bg-gray-800/50 border-gray-700">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-semibold text-white text-lg">{work.name}</div>
                      <div className="text-sm text-gray-400 mt-1">{work.description}</div>
                    </div>
                    <Badge className={getPriorityColor(work.priority)}>
                      {getPriorityLabel(work.priority)}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="text-gray-400">
                      <span className="text-gray-500">目标：</span>
                      {work.target}
                    </div>
                    <div className="text-gray-400">
                      <span className="text-gray-500">时间：</span>
                      {work.start_date} ~ {work.end_date}
                    </div>
                    <div className="text-gray-400">
                      <span className="text-gray-500">预算：</span>
                      {work.budget ? `${work.budget.toLocaleString()}元` : "待定"}
                    </div>
                    <div className="text-gray-400">
                      <span className="text-gray-500">关联 CSF：</span>
                      {work.csf_code}
                    </div>
                  </div>
                  {work.pain_point && (
                    <div className="mt-3 p-2 bg-red-900/20 rounded border border-red-700/30">
                      <div className="text-xs text-red-400 font-medium mb-1">痛点：</div>
                      <div className="text-sm text-gray-300">{work.pain_point}</div>
                    </div>
                  )}
                  {work.solution && (
                    <div className="mt-2 p-2 bg-green-900/20 rounded border border-green-700/30">
                      <div className="text-xs text-green-400 font-medium mb-1">解决方案：</div>
                      <div className="text-sm text-gray-300">{work.solution}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex gap-4">
            <Button onClick={prevStep} variant="outline" className="flex-1">
              <ArrowLeft className="w-4 h-4 mr-2" />
              上一步
            </Button>
            <Button onClick={nextStep} className="flex-1">
              下一步
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );

  const renderStep4 = () => (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-400" />
            部门信息
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">选择部门</Label>
            <Select
              value={deptObjectivesInput.departmentName}
              onValueChange={(value) => {
                const dept = departments.find((d) => d.value === value);
                setDeptObjectivesInput({
                  ...deptObjectivesInput,
                  departmentName: value,
                  departmentRole: dept?.role || "",
                });
              }}
            >
              <SelectTrigger className="bg-gray-900 border-gray-700 text-white">
                <SelectValue placeholder="请选择部门" />
              </SelectTrigger>
              <SelectContent className="bg-gray-800 border-gray-700">
                {departments.map((dept) => (
                  <SelectItem key={dept.value} value={dept.value} className="text-white">
                    {dept.value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-gray-300">部门职能描述</Label>
            <Textarea
              value={deptObjectivesInput.departmentRole}
              onChange={(e) => setDeptObjectivesInput({ ...deptObjectivesInput, departmentRole: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="描述部门的主要职能和责任"
            />
          </div>
          <div>
            <Label className="text-gray-300">年度</Label>
            <Input
              type="number"
              value={deptObjectivesInput.year}
              onChange={(e) => setDeptObjectivesInput({ ...deptObjectivesInput, year: parseInt(e.target.value) })}
              className="bg-gray-900 border-gray-700 text-white"
            />
          </div>
          <Button
            onClick={handleDeptObjectives}
            disabled={loading || !deptObjectivesInput.departmentName}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 生成部门 OKR
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {deptObjectivesResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">
              {deptObjectivesInput.departmentName} OKR 目标
            </h3>
            <Button onClick={handleApplyDeptObjectives} size="sm" variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              导入系统
            </Button>
          </div>

          <div className="grid gap-4">
            {deptObjectivesResult.objectives?.map((obj, i) => (
              <Card key={i} className="bg-gray-800/50 border-gray-700 border-l-4 border-l-purple-500">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="text-sm text-purple-400 font-medium mb-1">
                        Objective {i + 1}
                      </div>
                      <div className="text-white text-lg font-semibold">{obj.objective}</div>
                    </div>
                    <Badge variant="secondary" className="bg-gray-700 text-gray-300">
                      权重：{obj.weight}%
                    </Badge>
                  </div>
                  <div className="space-y-2 mb-4">
                    <div className="text-sm text-gray-400 font-medium">Key Results:</div>
                    {obj.key_results?.map((kr, krIndex) => (
                      <div key={krIndex} className="flex items-start gap-2 text-sm">
                        <Target className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                        <span className="text-gray-300">{kr}</span>
                      </div>
                    ))}
                  </div>
                  {obj.related_kpis?.length > 0 && (
                    <div className="pt-3 border-t border-gray-700">
                      <div className="text-sm text-gray-400 font-medium mb-2">关联 KPI:</div>
                      <div className="flex flex-wrap gap-2">
                        {obj.related_kpis.map((kpi, kpiIndex) => (
                          <Badge key={kpiIndex} variant="outline" className="text-xs">
                            {kpi.kpi_name}: {kpi.target_value} {kpi.unit}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex gap-4">
            <Button onClick={prevStep} variant="outline" className="flex-1">
              <ArrowLeft className="w-4 h-4 mr-2" />
              上一步
            </Button>
            <Button onClick={() => alert("完成！所有数据已导入系统。")} className="flex-1 bg-green-600 hover:bg-green-700">
              <Check className="w-4 h-4 mr-2" />
              完成
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );

  // ============================================
  // Loading 遮罩
  // ============================================

  const renderLoading = () => (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-gray-800 rounded-xl p-8 text-center max-w-md"
      >
        <div className="relative w-20 h-20 mx-auto mb-4">
          <div className="absolute inset-0 border-4 border-blue-500/30 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <Sparkles className="absolute inset-0 m-auto w-8 h-8 text-blue-400 animate-pulse" />
        </div>
        <div className="text-white text-lg font-medium mb-2">AI 正在分析</div>
        <div className="text-gray-400 text-sm">{loadingMessage}</div>
      </motion.div>
    </div>
  );

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
        {renderStepNav()}

        <div className="mt-8">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
        </div>
      </div>

      {loading && renderLoading()}
    </div>
  );
}
