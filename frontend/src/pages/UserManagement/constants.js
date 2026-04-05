import {
  USER_STATUS,
  USER_STATUS_LABELS,
  USER_STATUS_COLORS,
  USER_ROLE,
  USER_ROLE_LABELS,
  getRoleColor,
} from "../../components/user-management";

export const statusConfig = {
  [USER_STATUS.ACTIVE]: {
    label: USER_STATUS_LABELS[USER_STATUS.ACTIVE],
    color: USER_STATUS_COLORS[USER_STATUS.ACTIVE],
  },
  [USER_STATUS.INACTIVE]: {
    label: USER_STATUS_LABELS[USER_STATUS.INACTIVE],
    color: USER_STATUS_COLORS[USER_STATUS.INACTIVE],
  },
  [USER_STATUS.SUSPENDED]: {
    label: USER_STATUS_LABELS[USER_STATUS.SUSPENDED],
    color: USER_STATUS_COLORS[USER_STATUS.SUSPENDED],
  },
  [USER_STATUS.PENDING]: {
    label: USER_STATUS_LABELS[USER_STATUS.PENDING],
    color: USER_STATUS_COLORS[USER_STATUS.PENDING],
  },
};

export const roleConfig = {
  [USER_ROLE.ADMIN]: {
    label: USER_ROLE_LABELS[USER_ROLE.ADMIN],
    color: getRoleColor(USER_ROLE.ADMIN),
  },
  [USER_ROLE.MANAGER]: {
    label: USER_ROLE_LABELS[USER_ROLE.MANAGER],
    color: getRoleColor(USER_ROLE.MANAGER),
  },
  [USER_ROLE.SUPERVISOR]: {
    label: USER_ROLE_LABELS[USER_ROLE.SUPERVISOR],
    color: getRoleColor(USER_ROLE.SUPERVISOR),
  },
  [USER_ROLE.ENGINEER]: {
    label: USER_ROLE_LABELS[USER_ROLE.ENGINEER],
    color: getRoleColor(USER_ROLE.ENGINEER),
  },
  [USER_ROLE.TECHNICIAN]: {
    label: USER_ROLE_LABELS[USER_ROLE.TECHNICIAN],
    color: getRoleColor(USER_ROLE.TECHNICIAN),
  },
  [USER_ROLE.SALESPERSON]: {
    label: USER_ROLE_LABELS[USER_ROLE.SALESPERSON],
    color: getRoleColor(USER_ROLE.SALESPERSON),
  },
  [USER_ROLE.CUSTOMER_SERVICE]: {
    label: USER_ROLE_LABELS[USER_ROLE.CUSTOMER_SERVICE],
    color: getRoleColor(USER_ROLE.CUSTOMER_SERVICE),
  },
  [USER_ROLE.FINANCE]: {
    label: USER_ROLE_LABELS[USER_ROLE.FINANCE],
    color: getRoleColor(USER_ROLE.FINANCE),
  },
  [USER_ROLE.HR]: {
    label: USER_ROLE_LABELS[USER_ROLE.HR],
    color: getRoleColor(USER_ROLE.HR),
  },
  [USER_ROLE.OPERATIONS]: {
    label: USER_ROLE_LABELS[USER_ROLE.OPERATIONS],
    color: getRoleColor(USER_ROLE.OPERATIONS),
  },
};

export const ROLE_TEMPLATES = {
  presales: {
    label: "售前技术包",
    codes: ["SALES_DIR", "SA", "SALES", "CTO", "ENGINEER"],
  },
  project: {
    label: "项目管理包",
    codes: ["PM", "ENGINEER", "ME", "EE", "SW"],
  },
  sales: {
    label: "销售管理包",
    codes: ["SALES_DIR", "SA", "SALES"],
  },
  rnd: {
    label: "研发设计包",
    codes: ["CTO", "ME", "EE", "SW", "ENGINEER"],
  },
  production: {
    label: "生产装配包",
    codes: ["PM", "ASSEMBLER", "DEBUG", "ENGINEER"],
  },
  purchase: {
    label: "采购供应包",
    codes: ["PU_MGR", "PU", "PURCHASER"],
  },
  finance: {
    label: "财务核算包",
    codes: ["CFO", "FI", "FINANCE"],
  },
  quality: {
    label: "质量管控包",
    codes: ["QA_MGR", "QA"],
  },
  pmc: {
    label: "计划调度包",
    codes: ["PMC", "PM", "ENGINEER"],
  },
  executive: {
    label: "高管总览包",
    codes: ["GM", "CTO", "CFO", "SALES_DIR"],
  },
};
