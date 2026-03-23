/**
 * 登录页常量配置
 */

import {
  BarChart3, Clock, Users, AlertTriangle,
  Award, Settings, Shield, TrendingUp,
  DollarSign, Briefcase, ShoppingCart, Hammer,
  Target, GitBranch, UserCog, UserCircle, Headphones,
} from 'lucide-react';

// 功能特性展示
export const FEATURES = [
  { icon: BarChart3, title: "实时进度追踪", desc: "甘特图、看板多视图" },
  { icon: Clock, title: "智能工时管理", desc: "自动统计、负荷预警" },
  { icon: Users, title: "团队高效协作", desc: "任务分配、实时同步" },
  { icon: AlertTriangle, title: "AI 智能预警", desc: "风险识别、提前预警" },
];

// 后端配置
export const DEFAULT_BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || "8002";
export const DEFAULT_BACKEND_TARGET =
  import.meta.env.VITE_BACKEND_URL || `127.0.0.1:${DEFAULT_BACKEND_PORT}`;

// 快捷登录账户列表
export const DEMO_ACCOUNTS = [
  { username: 'zhengrucai', name: '郑汝才', role: '常务副总', icon: Award, colorFrom: 'emerald', colorClass: 'from-emerald-50 to-emerald-100 border-emerald-200 hover:border-emerald-300', iconBg: 'bg-emerald-100 group-hover:bg-emerald-200', iconColor: 'text-emerald-600' },
  { username: 'luoyixing', name: '骆奕兴', role: '副总经理', icon: Settings, colorFrom: 'cyan', colorClass: 'from-cyan-50 to-cyan-100 border-cyan-200 hover:border-cyan-300', iconBg: 'bg-cyan-100 group-hover:bg-cyan-200', iconColor: 'text-cyan-600' },
  { username: 'fulingwei', name: '符凌维', role: '副总经理（董秘）', icon: Shield, colorFrom: 'violet', colorClass: 'from-violet-50 to-violet-100 border-violet-200 hover:border-violet-300', iconBg: 'bg-violet-100 group-hover:bg-violet-200', iconColor: 'text-violet-600' },
  { username: 'songkui', name: '宋魁', role: '营销总监', icon: TrendingUp, colorFrom: 'rose', colorClass: 'from-rose-50 to-rose-100 border-rose-200 hover:border-rose-300', iconBg: 'bg-rose-100 group-hover:bg-rose-200', iconColor: 'text-rose-600' },
  { username: 'zhengqin', name: '郑琴', role: '销售经理', icon: DollarSign, colorFrom: 'teal', colorClass: 'from-teal-50 to-teal-100 border-teal-200 hover:border-teal-300', iconBg: 'bg-teal-100 group-hover:bg-teal-200', iconColor: 'text-teal-600' },
  { username: 'yaohong', name: '姚洪', role: '销售工程师', icon: Briefcase, colorFrom: 'pink', colorClass: 'from-pink-50 to-pink-100 border-pink-200 hover:border-pink-300', iconBg: 'bg-pink-100 group-hover:bg-pink-200', iconColor: 'text-pink-600' },
  { username: 'changxiong', name: '常雄', role: 'PMC主管', icon: ShoppingCart, colorFrom: 'green', colorClass: 'from-green-50 to-green-100 border-green-200 hover:border-green-300', iconBg: 'bg-green-100 group-hover:bg-green-200', iconColor: 'text-green-600' },
  { username: 'gaoyong', name: '高勇', role: '生产部经理', icon: Hammer, colorFrom: 'amber', colorClass: 'from-amber-50 to-amber-100 border-amber-200 hover:border-amber-300', iconBg: 'bg-amber-100 group-hover:bg-amber-200', iconColor: 'text-amber-600' },
  { username: 'chenliang', name: '陈亮', role: '项目管理部总监', icon: Target, colorFrom: 'indigo', colorClass: 'from-indigo-50 to-indigo-100 border-indigo-200 hover:border-indigo-300', iconBg: 'bg-indigo-100 group-hover:bg-indigo-200', iconColor: 'text-indigo-600' },
  { username: 'tanzhangbin', name: '谭章斌', role: '项目经理', icon: GitBranch, colorFrom: 'blue', colorClass: 'from-blue-50 to-blue-100 border-blue-200 hover:border-blue-300', iconBg: 'bg-blue-100 group-hover:bg-blue-200', iconColor: 'text-blue-600' },
  { username: 'yuzhenhua', name: '于振华', role: '经理', icon: UserCog, colorFrom: 'slate', colorClass: 'from-slate-50 to-slate-100 border-slate-200 hover:border-slate-300', iconBg: 'bg-slate-100 group-hover:bg-slate-200', iconColor: 'text-slate-600' },
  { username: 'wangjun', name: '王俊', role: '经理', icon: UserCircle, colorFrom: 'violet', colorClass: 'from-violet-50 to-violet-100 border-violet-200 hover:border-violet-300', iconBg: 'bg-violet-100 group-hover:bg-violet-200', iconColor: 'text-violet-600' },
  { username: 'wangzhihong', name: '王志红', role: '客服主管', icon: Headphones, colorFrom: 'teal', colorClass: 'from-teal-50 to-teal-100 border-teal-200 hover:border-teal-300', iconBg: 'bg-teal-100 group-hover:bg-teal-200', iconColor: 'text-teal-600' },
];

// 角色名称到前端角色代码的映射
export const ROLE_NAME_MAP = {
  "系统管理员": "admin", ADMIN: "admin", Administrator: "admin",
  SUPER_ADMIN: "super_admin", SuperAdmin: "super_admin",
  总经理: "gm", GM: "gm", GeneralManager: "gm",
  常务副总: "vice_chairman", 副总经理: "vice_chairman",
  董秘: "dongmi", 董事长: "chairman", Chairman: "chairman",
  项目经理: "pm", PM: "pm", ProjectManager: "pm",
  项目管理部总监: "project_dept_manager",
  PMC: "pmc", PMC主管: "pmc",
  销售总监: "sales_director", SALES_DIR: "sales_director", SalesDirector: "sales_director", 营销中心总监: "sales_director",
  销售经理: "sales_manager", SalesManager: "sales_manager",
  销售工程师: "sales", SalesEngineer: "sales",
  生产部经理: "production_manager", 电机生产部经理: "production_manager", ProductionManager: "production_manager", PRODUCTION_MANAGER: "production_manager",
  制造总监: "manufacturing_director", ManufacturingDirector: "manufacturing_director", MANUFACTURING_DIRECTOR: "manufacturing_director",
  计划管理: "pmc",
  采购部经理: "procurement_manager", 采购经理: "procurement_manager", ProcurementManager: "procurement_manager", PROCUREMENT_MANAGER: "procurement_manager",
  采购工程师: "procurement_engineer", ProcurementEngineer: "procurement_engineer", PROCUREMENT_ENGINEER: "procurement_engineer",
  采购员: "buyer", Buyer: "buyer", BUYER: "buyer",
  客服主管: "customer_service_manager", CustomerServiceManager: "customer_service_manager",
};

/**
 * 从角色名称解析前端角色代码
 * 先精确匹配，再忽略大小写匹配，最后关键词匹配
 */
export function resolveRoleCode(roleName) {
  // 精确匹配
  if (ROLE_NAME_MAP[roleName]) return ROLE_NAME_MAP[roleName];

  // 忽略大小写匹配
  const caseInsensitiveMatch = Object.keys(ROLE_NAME_MAP).find(
    (key) => key.toLowerCase() === roleName.toLowerCase()
  );
  if (caseInsensitiveMatch) return ROLE_NAME_MAP[caseInsensitiveMatch];

  // 关键词智能匹配
  if (roleName.includes("董事长")) return "chairman";
  if (roleName.includes("常务") && roleName.includes("副总")) return "vice_chairman";
  if (roleName.includes("总经理") && roleName.includes("副")) return "vice_chairman";
  if (roleName.includes("董秘")) return "dongmi";
  if (roleName.includes("总经理") || roleName.includes("GeneralManager") || roleName === "GM") return "gm";
  if (roleName.includes("生产") && !roleName.includes("制造")) return "production_manager";
  if (roleName.includes("制造") && roleName.includes("总监")) return "manufacturing_director";
  if (roleName.includes("采购") && (roleName.includes("经理") || roleName.includes("Manager"))) return "procurement_manager";
  if (roleName.includes("采购") && (roleName.includes("工程师") || roleName.includes("Engineer"))) return "procurement_engineer";
  if (roleName.includes("采购") && roleName.includes("员")) return "buyer";

  // 最后转为下划线格式
  return roleName.toLowerCase().replace(/\s+/g, "_").replace(/-/g, "_");
}
