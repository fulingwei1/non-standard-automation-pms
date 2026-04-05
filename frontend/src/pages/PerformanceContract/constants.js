import { Target, Users, User } from "lucide-react";

// 指标类别选项
export const CATEGORY_OPTIONS = [
  { value: "业绩指标", label: "业绩指标" },
  { value: "管理指标", label: "管理指标" },
  { value: "能力指标", label: "能力指标" },
  { value: "态度指标", label: "态度指标" },
];

// 合约类型选项
export const CONTRACT_TYPE_OPTIONS = [
  { value: "L1", label: "公司级 (L1)", icon: Target },
  { value: "L2", label: "部门级 (L2)", icon: Users },
  { value: "L3", label: "个人级 (L3)", icon: User },
];

// 初始创建表单
export const INITIAL_CREATE_FORM = {
  contract_type: "L1",
  year: new Date().getFullYear(),
  signer_name: "",
  signer_title: "",
  counterpart_name: "",
  counterpart_title: "",
  department_name: "",
  remarks: "",
};

// 初始指标条目表单
export const INITIAL_ITEM_FORM = {
  category: "业绩指标",
  indicator_name: "",
  indicator_description: "",
  weight: "",
  unit: "",
  target_value: "",
  challenge_value: "",
  baseline_value: "",
  scoring_rule: "",
  data_source: "",
  evaluation_method: "",
};
