// 基础漏斗阶段定义
export const stages = [
  { key: "leads", label: "线索", color: "slate", backendKey: "leads" },
  { key: "opportunities", label: "商机", color: "blue", backendKey: "opportunities" },
  { key: "quotes", label: "报价", color: "amber", backendKey: "quotes" },
  { key: "contracts", label: "合同", color: "purple", backendKey: "contracts" },
];

// 阶段名称映射（后端枚举 → 中文名）
export const STAGE_NAME_MAP = {
  DISCOVERY: "初步接触",
  QUALIFICATION: "需求挖掘",
  PROPOSAL: "方案介绍",
  NEGOTIATION: "价格谈判",
  CLOSING: "成交促成",
  WON: "赢单",
  LOST: "输单",
};
