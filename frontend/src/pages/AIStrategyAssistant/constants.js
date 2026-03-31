import { Brain, Target, Calendar, Users } from "lucide-react";

// 默认公司信息（金凯博）
export const DEFAULT_COMPANY_INFO = {
  name: "金凯博自动化测试（深圳）",
  industry: "非标自动化测试设备",
  products: "ICT/FCT/EOL/烧录/老化/视觉检测等测试设备",
};

// 步骤配置
export const STEPS = [
  { id: 1, title: "战略分析", icon: Brain, description: "SWOT 分析与战略定位" },
  { id: 2, title: "战略分解", icon: Target, description: "BSC 四维度 CSF+KPI" },
  { id: 3, title: "年度经营计划", icon: Calendar, description: "重点工作规划" },
  { id: 4, title: "部门工作分解", icon: Users, description: "部门 OKR 目标" },
];

// 部门选项
export const DEPARTMENTS = [
  { value: "研发部", role: "负责产品研发、技术创新、技术难题攻关" },
  { value: "销售部", role: "负责市场开拓、客户维护、销售目标达成" },
  { value: "生产部", role: "负责生产计划执行、产品质量控制、交付保障" },
  { value: "采购部", role: "负责供应商管理、物料采购、成本控制" },
  { value: "质量部", role: "负责质量管理体系、来料检验、过程质量控制" },
  { value: "工程部", role: "负责工艺工程、设备维护、技术支持" },
  { value: "财务部", role: "负责财务管理、成本控制、资金规划" },
  { value: "人力资源部", role: "负责人才招聘、培训发展、绩效管理" },
];
