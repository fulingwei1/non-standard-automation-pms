// 节点类型枚举
export const NODE_TYPES = {
  TASK: { label: "任务节点", color: "bg-blue-500/20 text-blue-400" },
  APPROVAL: { label: "审批节点", color: "bg-amber-500/20 text-amber-400" },
  DELIVERABLE: { label: "交付物节点", color: "bg-emerald-500/20 text-emerald-400" },
};

// 完成方式枚举
export const COMPLETION_METHODS = {
  MANUAL: "手动完成",
  APPROVAL: "需要审批",
  UPLOAD: "上传附件",
  AUTO: "自动完成",
};

export const INITIAL_STAGE_FORM_DATA = {
  stage_code: "",
  stage_name: "",
  sequence: 1,
  estimated_days: 5,
  description: "",
  is_required: true,
};

export const INITIAL_NODE_FORM_DATA = {
  node_code: "",
  node_name: "",
  node_type: "TASK",
  sequence: 1,
  estimated_days: 1,
  completion_method: "MANUAL",
  is_required: true,
  required_attachments: false,
  description: "",
  approval_role_ids: [],
  auto_condition: "",
  dependency_node_ids: [],
};
