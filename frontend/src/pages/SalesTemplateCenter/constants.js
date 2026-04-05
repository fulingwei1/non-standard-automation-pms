import { Layers, ClipboardList, Sparkles } from "lucide-react";

export const tabs = [
  { key: "quote", label: "报价模板", icon: Layers },
  { key: "contract", label: "合同模板", icon: ClipboardList },
  { key: "cpq", label: "CPQ规则", icon: Sparkles },
];

export const INITIAL_QUOTE_TEMPLATE = {
  template_code: "",
  template_name: "",
  category: "",
  visibility_scope: "TEAM",
  version_no: "v1",
  sections: '{"sections":[]}',
  pricing_rules: '{"base_price":0}',
};

export const INITIAL_CONTRACT_TEMPLATE = {
  template_code: "",
  template_name: "",
  contract_type: "",
  visibility_scope: "TEAM",
  version_no: "v1",
  clause_sections: '{"sections":[]}',
};

export const INITIAL_RULE_SET = {
  rule_code: "",
  rule_name: "",
  base_price: 0,
  config_schema: '{"options":[]}',
  pricing_matrix: '{"items":{}}',
  approval_threshold: '{"max_discount_pct":10}',
};

export const templateTypeConfigs = {
    proposal: { label: '技术方案', icon: 'FileText' },
    quotation: { label: '报价单', icon: 'DollarSign' },
    contract: { label: '合同', icon: 'FileCheck' },
    presentation: { label: '演示文稿', icon: 'Presentation' },
    email: { label: '邮件模板', icon: 'Mail' },
};

export const statusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    active: { label: '启用', color: 'bg-emerald-500' },
    archived: { label: '归档', color: 'bg-amber-500' },
};
