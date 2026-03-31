import { Building2, Network, FolderTree, Users } from "lucide-react";

// 组织单元类型配置
export const UNIT_TYPES = [
  { value: "COMPANY", label: "公司", icon: Building2, color: "text-purple-600" },
  { value: "BUSINESS_UNIT", label: "事业部", icon: Network, color: "text-blue-600" },
  { value: "DEPARTMENT", label: "部门", icon: FolderTree, color: "text-green-600" },
  { value: "TEAM", label: "团队", icon: Users, color: "text-orange-600" },
];

// 获取类型配置
export const getUnitTypeConfig = (type) => {
  return UNIT_TYPES.find((t) => t.value === type) || UNIT_TYPES[2];
};
