/**
 * 商机管理 - 常量和初始数据
 */

// 商机阶段配置
export const stageConfig = {
  DISCOVERY: {
    label: "需求澄清",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  QUALIFIED: {
    label: "商机合格",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  PROPOSAL: {
    label: "方案/报价中",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  REVIEW: {
    label: "方案评审",
    color: "bg-pink-500",
    textColor: "text-pink-400",
  },
  NEGOTIATION: {
    label: "商务谈判",
    color: "bg-purple-500",
    textColor: "text-purple-400",
  },
  WON: { label: "赢单", color: "bg-green-500", textColor: "text-green-400" },
  LOST: { label: "丢单", color: "bg-red-500", textColor: "text-red-400" },
  ON_HOLD: {
    label: "暂停",
    color: "bg-slate-500",
    textColor: "text-slate-400",
  },
};

// 判断阶段门是否通过
export const isGatePassed = (status) => {
  const normalized = String(status || "").toUpperCase();
  return normalized === "PASS" || normalized === "PASSED";
};

// 创建表单初始值
export const INITIAL_FORM_DATA = {
  customer_id: "",
  opp_name: "",
  project_type: "",
  equipment_type: "",
  stage: "DISCOVERY",
  est_amount: "",
  est_margin: "",
  budget_range: "",
  decision_chain: "",
  delivery_window: "",
  acceptance_basis: "",
  requirement: {
    product_object: "",
    ct_seconds: "",
    interface_desc: "",
    site_constraints: "",
    acceptance_criteria: "",
  },
};

// 阶段门表单初始值
export const INITIAL_GATE_DATA = {
  gate_status: "PASS",
  remark: "",
};

// 评审表单初始值
export const INITIAL_REVIEW_FORM = {
  title: "",
  description: "",
  urgency: "NORMAL",
  expected_date: "",
};

// 从商机数据构建详情编辑表单
export const buildDetailForm = (opp) => ({
  opp_name: opp?.opp_name || "",
  stage: opp?.stage || "DISCOVERY",
  project_type: opp?.project_type || "",
  equipment_type: opp?.equipment_type || "",
  probability: opp?.probability ?? "",
  est_amount: opp?.est_amount ?? "",
  est_margin: opp?.est_margin ?? "",
  expected_close_date: opp?.expected_close_date
    ? String(opp.expected_close_date).slice(0, 10)
    : "",
  budget_range: opp?.budget_range || "",
  decision_chain: opp?.decision_chain || "",
  delivery_window: opp?.delivery_window || "",
  acceptance_basis: opp?.acceptance_basis || "",
  risk_level: opp?.risk_level || "",
  score: opp?.score ?? "",
  priority_score: opp?.priority_score ?? "",
  requirement_maturity: opp?.requirement_maturity ?? "",
  assessment_status: opp?.assessment_status || "",
  requirement: {
    product_object: opp?.requirement?.product_object || "",
    ct_seconds: opp?.requirement?.ct_seconds ?? "",
    interface_desc: opp?.requirement?.interface_desc || "",
    site_constraints: opp?.requirement?.site_constraints || "",
    acceptance_criteria: opp?.requirement?.acceptance_criteria || "",
    safety_requirement: opp?.requirement?.safety_requirement || "",
    attachments: opp?.requirement?.attachments || "",
    extra_json: opp?.requirement?.extra_json || "",
  },
});

export const PAGE_SIZE = 20;
