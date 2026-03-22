/**
 * 用户管理 - 常量与配置
 */

import {
  USER_STATUS, USER_STATUS_LABELS, USER_STATUS_COLORS,
  USER_ROLE, USER_ROLE_LABELS, USER_DEPARTMENT, USER_DEPARTMENT_LABELS,
  getRoleColor,
} from "../../components/user-management";

// 状态显示配置
export const statusConfig = {
  [USER_STATUS.ACTIVE]: { label: USER_STATUS_LABELS[USER_STATUS.ACTIVE], color: USER_STATUS_COLORS[USER_STATUS.ACTIVE] },
  [USER_STATUS.INACTIVE]: { label: USER_STATUS_LABELS[USER_STATUS.INACTIVE], color: USER_STATUS_COLORS[USER_STATUS.INACTIVE] },
  [USER_STATUS.SUSPENDED]: { label: USER_STATUS_LABELS[USER_STATUS.SUSPENDED], color: USER_STATUS_COLORS[USER_STATUS.SUSPENDED] },
  [USER_STATUS.PENDING]: { label: USER_STATUS_LABELS[USER_STATUS.PENDING], color: USER_STATUS_COLORS[USER_STATUS.PENDING] },
};

// 角色显示配置
export const roleConfig = Object.fromEntries(
  Object.values(USER_ROLE).map((role) => [
    role,
    { label: USER_ROLE_LABELS[role], color: getRoleColor(role) },
  ])
);

// 新建用户默认值
export const INITIAL_NEW_USER = {
  username: "",
  email: "",
  password: "",
  full_name: "",
  phone: "",
  role: USER_ROLE.ENGINEER,
  department: USER_DEPARTMENT.ENGINEERING,
  status: USER_STATUS.ACTIVE,
};

// 快速角色模板 —— 按业务场景预设角色组合
export const ROLE_TEMPLATES = {
  presales: { label: "售前技术包", codes: ["SALES_DIR", "SA", "SALES", "CTO", "ENGINEER"] },
  project: { label: "项目管理包", codes: ["PM", "ENGINEER", "ME", "EE", "SW"] },
  sales: { label: "销售管理包", codes: ["SALES_DIR", "SA", "SALES"] },
  rnd: { label: "研发设计包", codes: ["CTO", "ME", "EE", "SW", "ENGINEER"] },
  production: { label: "生产装配包", codes: ["PM", "ASSEMBLER", "DEBUG", "ENGINEER"] },
  purchase: { label: "采购供应包", codes: ["PU_MGR", "PU", "PURCHASER"] },
  finance: { label: "财务核算包", codes: ["CFO", "FI", "FINANCE"] },
  quality: { label: "质量管控包", codes: ["QA_MGR", "QA"] },
  pmc: { label: "计划调度包", codes: ["PMC", "PM", "ENGINEER"] },
  executive: { label: "高管总览包", codes: ["GM", "CTO", "CFO", "SALES_DIR"] },
};
