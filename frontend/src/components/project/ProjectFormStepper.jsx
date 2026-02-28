/**
 * 项目创建/编辑表单 - 分步骤表单组件
 *
 * Issue 3.1: 使用 shadcn/ui 组件重构，分步骤表单
 * Issue 3.2: 智能提示和自动填充功能
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Button,
  Input,
  FormField,
  FormTextarea,
  FormSelect,
  Badge,
} from "../ui";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../ui";
import {
  ChevronRight,
  ChevronLeft,
  Check,
  Building2,
  DollarSign,
  Calendar,
  User,
  FileText,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { projectApi, customerApi, orgApi, stageViewsApi } from "../../services/api";
import { toast } from "../ui/toast";
import { BasicInfoStep } from "./steps/BasicInfoStep";
import { CustomerInfoStep } from "./steps/CustomerInfoStep";
import { FinanceInfoStep } from "./steps/FinanceInfoStep";
import { ScheduleInfoStep } from "./steps/ScheduleInfoStep";

// 步骤配置
const STEPS = [
  {
    id: "basic",
    name: "基本信息",
    icon: FileText,
    description: "项目编码、名称、类型等",
  },
  {
    id: "customer",
    name: "客户信息",
    icon: Building2,
    description: "客户、联系人、联系方式",
  },
  {
    id: "finance",
    name: "财务信息",
    icon: DollarSign,
    description: "合同金额、预算、收款计划",
  },
  {
    id: "schedule",
    name: "时间节点",
    icon: Calendar,
    description: "计划开始、结束日期",
  },
];

// 项目类型选项已移至 BasicInfoStep 组件

export default function ProjectFormStepper({
  open,
  onOpenChange,
  onSubmit,
  initialData = {},
  recommendedTemplates = [],
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  const [validatingCode, setValidatingCode] = useState(false);
  const [codeError, setCodeError] = useState("");

  // 表单数据
  const [formData, setFormData] = useState({
    project_code: "",
    project_name: "",
    short_name: "",
    project_type: "FIXED_PRICE",
    product_category: "",
    industry: "",
    customer_id: "",
    customer_name: "",
    customer_contact: "",
    customer_phone: "",
    contract_no: "",
    contract_date: "",
    contract_amount: 0,
    budget_amount: 0,
    pm_id: "",
    pm_name: "",
    planned_start_date: "",
    planned_end_date: "",
    description: "",
    requirements: "",
    template_id: null,
    stage_template_id: null, // 阶段模板ID
    ...initialData,
  });

  // 选项数据
  const [customers, setCustomers] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [stageTemplates, setStageTemplates] = useState([]); // 阶段模板列表
  const [filteredCustomers, setFilteredCustomers] = useState([]);
  const [customerSearch, setCustomerSearch] = useState("");
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [pmStats, setPmStats] = useState({}); // Sprint 3.2: 项目经理统计信息

  // 加载选项数据
  useEffect(() => {
    if (open) {
      const loadOptions = async () => {
        try {
          const [custRes, empRes, statsRes, stageTemplatesRes] = await Promise.all([
            customerApi.list(),
            orgApi.employees(),
            projectApi.getStats?.() || Promise.resolve({ data: { by_pm: [] } }), // Sprint 3.2: 加载项目经理统计
            stageViewsApi.templates.list({ is_active: true }), // 加载阶段模板
          ]);
          setCustomers(custRes.data?.items || custRes.data || []);
          setEmployees(empRes.data?.items || empRes.data || []);
          setFilteredCustomers(custRes.data?.items || custRes.data || []);
          setStageTemplates(stageTemplatesRes.data?.items || stageTemplatesRes.data?.items || stageTemplatesRes.data || []);

          // Sprint 3.2: 构建项目经理统计映射
          if (statsRes.data?.by_pm) {
            const statsMap = {};
            statsRes.data.by_pm.forEach((pm) => {
              statsMap[pm.pm_id] = pm.count;
            });
            setPmStats(statsMap);
          }
        } catch (err) {
          console.error("Failed to load form options:", err);
          toast.error("无法加载客户和员工数据");
        }
      };
      loadOptions();
    }
  }, [open, toast]);

  // 客户搜索
  useEffect(() => {
    if (customerSearch) {
      const filtered = customers.filter(
        (c) =>
          c.customer_name
            ?.toLowerCase()
            .includes(customerSearch.toLowerCase()) ||
          c.customer_code?.toLowerCase().includes(customerSearch.toLowerCase()),
      );
      setFilteredCustomers(filtered);
    } else {
      setFilteredCustomers(customers);
    }
  }, [customerSearch, customers]);

  // 选择客户时自动填充信息
  const handleCustomerSelect = (customerId) => {
    const customer = customers.find((c) => c.id === customerId);
    if (customer) {
      setSelectedCustomer(customer);
      setFormData((prev) => ({
        ...prev,
        customer_id: customer.id,
        customer_name: customer.customer_name,
        customer_contact: customer.contact_person || "",
        customer_phone: customer.contact_phone || "",
      }));
      setCustomerSearch("");
    }
  };

  // 项目编码唯一性检查
  const handleCodeBlur = async () => {
    if (!formData.project_code || initialData.id) {return;}

    setValidatingCode(true);
    setCodeError("");

    try {
      // 检查编码是否已存在
      const response = await projectApi.list({
        project_code: formData.project_code,
      });
      if (response.data?.items?.length > 0) {
        setCodeError("项目编码已存在，请使用其他编码");
      }
    } catch (err) {
      // 忽略错误，可能是网络问题
      console.error("Code validation error:", err);
    } finally {
      setValidatingCode(false);
    }
  };

  // 应用模板推荐
  const handleApplyTemplate = (template) => {
    if (template.template_config) {
      try {
        const config = JSON.parse(template.template_config);
        setFormData((prev) => ({
          ...prev,
          template_id: template.template_id,
          project_type: config.project_type || prev.project_type,
          product_category: config.product_category || prev.product_category,
          industry: config.industry || prev.industry,
          stage: config.default_stage || "S1",
          status: config.default_status || "ST01",
          health: config.default_health || "H1",
        }));
        toast.success(`已应用模板：${template.template_name}`);
      } catch (err) {
        console.error("Failed to parse template config:", err);
      }
    }
  };

  // 保存草稿
  const handleSaveDraft = async () => {
    setSavingDraft(true);
    try {
      // 保存到 localStorage
      const draftKey = `project_draft_${initialData.id || "new"}`;
      localStorage.setItem(draftKey, JSON.stringify(formData));
      toast.success("表单数据已保存为草稿");
    } catch (err) {
      console.error("Failed to save draft:", err);
    } finally {
      setSavingDraft(false);
    }
  };

  // 加载草稿
  useEffect(() => {
    if (open && !initialData.id) {
      const draftKey = "project_draft_new";
      const draft = localStorage.getItem(draftKey);
      if (draft) {
        try {
          const draftData = JSON.parse(draft);
          setFormData((prev) => ({ ...prev, ...draftData }));
        } catch (err) {
          console.error("Failed to load draft:", err);
        }
      }
    }
  }, [open, initialData.id]);

  // 表单验证
  const validateStep = (stepIndex) => {
    const step = STEPS[stepIndex];
    switch (step.id) {
      case "basic":
        if (!formData.project_code) {return "请输入项目编码";}
        if (!formData.project_name) {return "请输入项目名称";}
        if (codeError) {return codeError;}
        return null;
      case "customer":
        if (!formData.customer_id) {return "请选择客户";}
        return null;
      case "finance":
        // 财务信息可选
        return null;
      case "schedule":
        // 时间节点可选
        return null;
      default:
        return null;
    }
  };

  // 下一步
  const handleNext = () => {
    const error = validateStep(currentStep);
    if (error) {
      toast.error(error);
      return;
    }

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  // 上一步
  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // 提交表单
  const handleSubmit = async () => {
    const error = validateStep(currentStep);
    if (error) {
      toast.error(error);
      return;
    }

    // 验证所有步骤
    for (let i = 0; i < STEPS.length; i++) {
      const stepError = validateStep(i);
      if (stepError) {
        setCurrentStep(i);
        toast.error(`${STEPS[i].name}：${stepError}`);
        return;
      }
    }

    setLoading(true);
    try {
      await onSubmit(formData);
      // 清除草稿
      if (!initialData.id) {
        localStorage.removeItem("project_draft_new");
      }
      onOpenChange(false);
    } catch (err) {
      console.error("Failed to submit form:", err);
      toast.error(err.response?.data?.detail || "无法创建项目，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  // 渲染步骤内容
  const renderStepContent = () => {
    const step = STEPS[currentStep];

    switch (step.id) {
      case "basic":
        return (
          <BasicInfoStep
            formData={formData}
            setFormData={setFormData}
            recommendedTemplates={recommendedTemplates}
            stageTemplates={stageTemplates}
            currentStep={currentStep}
            initialData={initialData}
            validatingCode={validatingCode}
            codeError={codeError}
            onCodeBlur={handleCodeBlur}
            onApplyTemplate={handleApplyTemplate}
          />
        );

      case "customer":
        return (
          <CustomerInfoStep
            formData={formData}
            setFormData={setFormData}
            customerSearch={customerSearch}
            setCustomerSearch={setCustomerSearch}
            filteredCustomers={filteredCustomers}
            selectedCustomer={selectedCustomer}
            setSelectedCustomer={setSelectedCustomer}
            onCustomerSelect={handleCustomerSelect}
          />
        );

      case "finance":
        return (
          <FinanceInfoStep
            formData={formData}
            setFormData={setFormData}
            employees={employees}
            pmStats={pmStats}
          />
        );

      case "schedule":
        return (
          <ScheduleInfoStep formData={formData} setFormData={setFormData} />
        );

      default:
        return null;
    }
  };

  if (!open) {return null;}

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{initialData.id ? "编辑项目" : "新建项目"}</DialogTitle>
        </DialogHeader>

        {/* 步骤指示器 */}
        <div className="flex items-center justify-between mb-6 px-2">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;

            return (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center transition-all",
                      isActive
                        ? "bg-primary text-white"
                        : isCompleted
                          ? "bg-emerald-500 text-white"
                          : "bg-white/10 text-slate-400",
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <div className="mt-2 text-center">
                    <div
                      className={cn(
                        "text-xs font-medium",
                        isActive ? "text-white" : "text-slate-400",
                      )}
                    >
                      {step.name}
                    </div>
                  </div>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={cn(
                      "h-0.5 flex-1 mx-2 transition-colors",
                      isCompleted ? "bg-emerald-500" : "bg-white/10",
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* 步骤内容 */}
        <DialogBody>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>
        </DialogBody>

        {/* 底部操作 */}
        <DialogFooter className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={handleSaveDraft}
              disabled={savingDraft}
            >
              {savingDraft ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  保存中...
                </>
              ) : (
                "保存草稿"
              )}
            </Button>
          </div>

          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <Button
                type="button"
                variant="secondary"
                onClick={handlePrev}
                disabled={loading}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                上一步
              </Button>
            )}

            {currentStep < STEPS.length - 1 ? (
              <Button type="button" onClick={handleNext} disabled={loading}>
                下一步
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button type="button" onClick={handleSubmit} loading={loading}>
                {initialData.id ? "保存项目" : "创建项目"}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
