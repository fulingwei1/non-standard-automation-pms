import { BarChart3, Wallet, Target, Receipt, FileText } from "lucide-react";

export const reportTypes = [
  { id: "profit-loss", label: "损益表", icon: BarChart3 },
  { id: "cash-flow", label: "现金流量表", icon: Wallet },
  { id: "budget", label: "预算执行", icon: Target },
  { id: "cost", label: "成本分析", icon: Receipt },
  { id: "project", label: "项目盈利", icon: FileText },
];
