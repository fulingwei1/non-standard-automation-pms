/**
 * Invoice Constants - 发票相关常量配置
 * 包含发票状态映射、支付状态映射、表单默认值等
 */
import { FileText, Clock, Check, X, AlertTriangle, TrendingUp } from "lucide-react";

// Invoice status mapping (API -> UI)
// 发票状态映射：将后端枚举转换为前端UI状态标识
export const statusMap = {
  DRAFT: "draft",
  APPLIED: "applied",
  APPROVED: "approved",
  ISSUED: "issued",
  VOID: "void"
};

// Payment status mapping (API -> UI)
// 收款状态映射：将后端枚举转换为前端UI状态标识
export const paymentStatusMap = {
  PENDING: "pending",
  PARTIAL: "partial",
  PAID: "paid",
  OVERDUE: "overdue"
};

// Invoice status configuration
// 发票状态的UI展示配置（标签、颜色、图标）
export const statusConfig = {
  draft: {
    label: "草稿",
    color: "bg-slate-500/20 text-slate-400",
    icon: FileText
  },
  applied: {
    label: "申请中",
    color: "bg-blue-500/20 text-blue-400",
    icon: Clock
  },
  approved: {
    label: "已批准",
    color: "bg-purple-500/20 text-purple-400",
    icon: Check
  },
  issued: {
    label: "已开票",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check
  },
  void: {
    label: "作废",
    color: "bg-red-500/20 text-red-400",
    icon: X
  }
};

// Payment status configuration
// 收款状态的UI展示配置（标签、颜色、图标）
export const paymentStatusConfig = {
  pending: {
    label: "未收款",
    color: "bg-slate-500/20 text-slate-400",
    icon: Clock
  },
  partial: {
    label: "部分收款",
    color: "bg-amber-500/20 text-amber-400",
    icon: TrendingUp
  },
  paid: {
    label: "已收款",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check
  },
  overdue: {
    label: "已逾期",
    color: "bg-red-500/20 text-red-400",
    icon: AlertTriangle
  }
};

// Default form data
// 发票申请表单默认值
export const defaultFormData = {
  contract_id: "",
  invoice_type: "SPECIAL",
  amount: "",
  tax_rate: "13",
  issue_date: "",
  due_date: "",
  remark: ""
};

// Default issue data
// 开票确认表单默认值
export const defaultIssueData = {
  invoice_no: "",
  issue_date: new Date().toISOString().split("T")[0],
  remark: ""
};

// Default payment data
// 收款登记表单默认值
export const defaultPaymentData = {
  paid_amount: "",
  paid_date: new Date().toISOString().split("T")[0],
  remark: ""
};
