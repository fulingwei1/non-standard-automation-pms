/**
 * Common Constants - 通用常量配置
 * 包含项目、任务、设备、物料等通用常量
 */

// 项目阶段配置
export const PROJECT_STAGES = [
  {
    key: "S1",
    code: "S1",
    name: "需求进入",
    shortName: "需求进入",
    color: "blue",
  },
  {
    key: "S2",
    code: "S2",
    name: "方案设计",
    shortName: "方案设计",
    color: "purple",
  },
  {
    key: "S3",
    code: "S3",
    name: "采购备料",
    shortName: "采购备料",
    color: "orange",
  },
  {
    key: "S4",
    code: "S4",
    name: "加工制造",
    shortName: "加工制造",
    color: "cyan",
  },
  {
    key: "S5",
    code: "S5",
    name: "装配调试",
    shortName: "装配调试",
    color: "teal",
  },
  {
    key: "S6",
    code: "S6",
    name: "出厂验收",
    shortName: "出厂验收",
    color: "emerald",
  },
  {
    key: "S7",
    code: "S7",
    name: "包装发运",
    shortName: "包装发运",
    color: "lime",
  },
  {
    key: "S8",
    code: "S8",
    name: "现场安装",
    shortName: "现场安装",
    color: "amber",
  },
  {
    key: "S9",
    code: "S9",
    name: "质保结项",
    shortName: "质保结项",
    color: "green",
  },
];

// 项目健康度配置
export const HEALTH_CONFIG = {
  H1: {
    code: "H1",
    name: "正常",
    label: "正常",
    color: "emerald",
    bgColor: "bg-emerald-500/20",
    textColor: "text-emerald-400",
    borderColor: "border-emerald-500/30",
    description: "项目进展顺利，无风险",
  },
  H2: {
    code: "H2",
    name: "有风险",
    label: "有风险",
    color: "amber",
    bgColor: "bg-amber-500/20",
    textColor: "text-amber-400",
    borderColor: "border-amber-500/30",
    description: "存在潜在风险，需关注",
  },
  H3: {
    code: "H3",
    name: "阻塞",
    label: "阻塞",
    color: "red",
    bgColor: "bg-red-500/20",
    textColor: "text-red-400",
    borderColor: "border-red-500/30",
    description: "项目被阻塞，需立即处理",
  },
  H4: {
    code: "H4",
    name: "已完结",
    label: "已完结",
    color: "slate",
    bgColor: "bg-slate-500/20",
    textColor: "text-slate-400",
    borderColor: "border-slate-500/30",
    description: "项目已完成或关闭",
  },
};

// 项目状态配置
export const PROJECT_STATUS = {
  ACTIVE: { label: "进行中", color: "emerald" },
  PENDING: { label: "待启动", color: "amber" },
  COMPLETED: { label: "已完成", color: "blue" },
  SUSPENDED: { label: "暂停", color: "orange" },
  CANCELLED: { label: "取消", color: "red" },
};

// 获取健康度配置
export function getHealthConfig(healthCode) {
  return HEALTH_CONFIG[healthCode] || HEALTH_CONFIG.H1;
}

// 获取阶段配置
export function getStageConfig(stageCode) {
  return PROJECT_STAGES.find((s) => s.code === stageCode) || PROJECT_STAGES[0];
}

// 优先级配置
export const PRIORITY_CONFIG = {
  URGENT: { label: "紧急", color: "red", value: 4 },
  HIGH: { label: "高", color: "orange", value: 3 },
  MEDIUM: { label: "中", color: "amber", value: 2 },
  LOW: { label: "低", color: "blue", value: 1 },
};

// 任务状态
export const TASK_STATUS = {
  PENDING: { label: "待处理", color: "slate" },
  IN_PROGRESS: { label: "进行中", color: "blue" },
  COMPLETED: { label: "已完成", color: "emerald" },
  BLOCKED: { label: "阻塞", color: "red" },
  CANCELLED: { label: "取消", color: "slate" },
};

// 设备类型
export const MACHINE_TYPES = [
  { value: "ICT", label: "ICT测试设备" },
  { value: "FCT", label: "FCT测试设备" },
  { value: "EOL", label: "EOL测试设备" },
  { value: "BURN_IN", label: "烧录设备" },
  { value: "AGING", label: "老化设备" },
  { value: "VISION", label: "视觉检测设备" },
  { value: "ASSEMBLY", label: "自动化组装线体" },
  { value: "OTHER", label: "其他" },
];

// 物料类型
export const MATERIAL_TYPES = [
  { value: "STANDARD", label: "标准件" },
  { value: "MECHANICAL", label: "机械件" },
  { value: "ELECTRICAL", label: "电气件" },
  { value: "PNEUMATIC", label: "气动件" },
  { value: "CONSUMABLE", label: "易耗品" },
  { value: "OTHER", label: "其他" },
];

// ECN 类型
export const ECN_TYPES = [
  { value: "DESIGN", label: "设计变更" },
  { value: "MATERIAL", label: "物料变更" },
  { value: "PROCESS", label: "工艺变更" },
  { value: "SPEC", label: "规格变更" },
  { value: "PLAN", label: "计划变更" },
];

// 预警级别
export const ALERT_LEVELS = [
  { value: "INFO", label: "提示", color: "blue" },
  { value: "WARNING", label: "警告", color: "amber" },
  { value: "SEVERE", label: "严重", color: "orange" },
  { value: "CRITICAL", label: "紧急", color: "red" },
];

// 验收类型
export const ACCEPTANCE_TYPES = [
  { value: "FAT", label: "出厂验收 (FAT)" },
  { value: "SAT", label: "现场验收 (SAT)" },
  { value: "FINAL", label: "终验收" },
];
