// 规则类型选项
export const ruleTypeOptions = [
  { value: "SCHEDULE_DELAY", label: "进度延期" },
  { value: "COST_OVERRUN", label: "成本超支" },
  { value: "MILESTONE_DUE", label: "里程碑到期" },
  { value: "DELIVERY_DUE", label: "交期预警" },
  { value: "MATERIAL_SHORTAGE", label: "物料短缺" },
  { value: "QUALITY_ISSUE", label: "质量问题" },
  { value: "PAYMENT_DUE", label: "付款到期" },
  { value: "SPECIFICATION_MISMATCH", label: "规格不匹配" },
  { value: "CUSTOM", label: "自定义" },
];

// 监控对象类型选项
export const targetTypeOptions = [
  { value: "PROJECT", label: "项目" },
  { value: "MACHINE", label: "设备" },
  { value: "TASK", label: "任务" },
  { value: "PURCHASE_ORDER", label: "采购订单" },
  { value: "OUTSOURCING_ORDER", label: "外协订单" },
  { value: "MATERIAL", label: "物料" },
  { value: "MILESTONE", label: "里程碑" },
  { value: "ACCEPTANCE", label: "验收" },
];

// 条件类型选项
export const conditionTypeOptions = [
  { value: "THRESHOLD", label: "阈值" },
  { value: "DEVIATION", label: "偏差" },
  { value: "OVERDUE", label: "逾期" },
  { value: "CUSTOM", label: "自定义表达式" },
];

// 条件运算符选项
export const operatorOptions = [
  { value: "GT", label: "大于 (>)" },
  { value: "GTE", label: "大于等于 (>=)" },
  { value: "LT", label: "小于 (<)" },
  { value: "LTE", label: "小于等于 (<=)" },
  { value: "EQ", label: "等于 (=)" },
  { value: "BETWEEN", label: "区间" },
];

// 预警级别选项
export const alertLevelOptions = [
  { value: "INFO", label: "提示", color: "blue" },
  { value: "WARNING", label: "注意", color: "amber" },
  { value: "CRITICAL", label: "严重", color: "orange" },
  { value: "URGENT", label: "紧急", color: "red" },
];

// 检查频率选项
export const frequencyOptions = [
  { value: "REALTIME", label: "实时" },
  { value: "HOURLY", label: "每小时" },
  { value: "DAILY", label: "每天" },
  { value: "WEEKLY", label: "每周" },
];

// 通知渠道选项
export const channelOptions = [
  { value: "SYSTEM", label: "站内消息" },
  { value: "EMAIL", label: "邮件" },
  { value: "WECHAT", label: "企业微信" },
  { value: "SMS", label: "短信" },
];

// 初始表单数据
export const initialFormData = {
  rule_code: "",
  rule_name: "",
  rule_type: "",
  target_type: "",
  target_field: "",
  condition_type: "THRESHOLD",
  condition_operator: "GT",
  threshold_value: "",
  threshold_min: "",
  threshold_max: "",
  condition_expr: "",
  alert_level: "WARNING",
  advance_days: 0,
  notify_channels: ["SYSTEM"],
  notify_roles: [],
  notify_users: [],
  check_frequency: "DAILY",
  is_enabled: true,
  description: "",
  solution_guide: "",
};

// 格式化辅助函数
export const formatFrequency = (freq) => {
  const option = frequencyOptions.find((o) => o.value === freq);
  return option?.label || freq;
};

export const formatLevel = (level) => {
  const option = alertLevelOptions.find((o) => o.value === level);
  return option?.label || level;
};

export const getLevelColor = (level) => {
  const option = alertLevelOptions.find((o) => o.value === level);
  return option?.color || "slate";
};
