/**
 * QualificationManagement - 常量和配置
 */

export const qualificationStatusConfigs = {
    valid: { label: '有效', color: 'bg-emerald-500' },
    expiring: { label: '即将到期', color: 'bg-amber-500' },
    expired: { label: '已过期', color: 'bg-red-500' },
    revoked: { label: '已撤销', color: 'bg-slate-500' },
};

export const qualificationTypeConfigs = {
    iso9001: { label: 'ISO 9001', category: '质量管理' },
    iso14001: { label: 'ISO 14001', category: '环境管理' },
    safety: { label: '安全生产许可证', category: '安全' },
    ce: { label: 'CE认证', category: '产品认证' },
    ul: { label: 'UL认证', category: '产品认证' },
};

export const LEVEL_BADGE_COLORS = {
  ASSISTANT: "bg-gray-100 text-gray-800",
  JUNIOR: "bg-blue-100 text-blue-800",
  MIDDLE: "bg-green-100 text-green-800",
  SENIOR: "bg-purple-100 text-purple-800",
  EXPERT: "bg-yellow-100 text-yellow-800",
};

export const STATUS_MAP = {
  PENDING: { label: "待认证", color: "bg-yellow-100 text-yellow-800" },
  APPROVED: { label: "已认证", color: "bg-green-100 text-green-800" },
  EXPIRED: { label: "已过期", color: "bg-red-100 text-red-800" },
  REVOKED: { label: "已撤销", color: "bg-gray-100 text-gray-800" },
};

export const LEVEL_CODES = ["ASSISTANT", "JUNIOR", "MIDDLE", "SENIOR", "EXPERT"];

export const LEVEL_LABELS = {
  ASSISTANT: "助理级",
  JUNIOR: "初级",
  MIDDLE: "中级",
  SENIOR: "高级",
  EXPERT: "专家级",
};

export const POSITION_TYPES = ["ENGINEER", "SALES", "CUSTOMER_SERVICE", "WORKER"];

export const POSITION_LABELS = {
  ENGINEER: "工程师",
  SALES: "销售",
  CUSTOMER_SERVICE: "客服",
  WORKER: "生产工人",
};

export function getLevelBadgeColor(levelCode) {
  return LEVEL_BADGE_COLORS[levelCode] || "bg-gray-100 text-gray-800";
}

export function getStatusInfo(status) {
  return STATUS_MAP[status] || {
    label: status,
    color: "bg-gray-100 text-gray-800",
  };
}
