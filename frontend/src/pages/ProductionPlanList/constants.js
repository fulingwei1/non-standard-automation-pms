export const statusConfigs = {
  DRAFT:     { label: "草稿",   color: "bg-slate-500" },
  SUBMITTED: { label: "已提交", color: "bg-blue-500" },
  APPROVED:  { label: "已批准", color: "bg-emerald-500" },
  PUBLISHED: { label: "已发布", color: "bg-violet-500" },
  EXECUTING: { label: "执行中", color: "bg-amber-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};

export const typeConfigs = {
  MASTER:   { label: "主计划",   color: "bg-blue-500" },
  WORKSHOP: { label: "车间计划", color: "bg-purple-500" },
};

export const INITIAL_NEW_PLAN = {
  plan_name:       "",
  plan_type:       "MASTER",
  project_id:      null,
  workshop_id:     null,
  plan_start_date: "",
  plan_end_date:   "",
  description:     "",
  remark:          "",
};
