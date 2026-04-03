// 收款状态配置（API 返回值 → 显示样式）
export const paymentStatusConfig = {
  PENDING: {
    label: "待收款",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  PARTIAL: {
    label: "部分收款",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  PAID: {
    label: "已收款",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  OVERDUE: {
    label: "已逾期",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
};

// 账龄分区排序权重
export const agingBucketOrder = {
  "0-30": 1,
  "31-60": 2,
  "61-90": 3,
  "90+": 4,
};

// 账龄分区显示标签
export const agingBucketLabelMap = {
  "0-30": "0-30天",
  "31-60": "31-60天",
  "61-90": "61-90天",
  "90+": "90+天",
};

// 账龄分区颜色
export const agingBucketColorMap = {
  "0-30": "bg-emerald-500",
  "31-60": "bg-blue-500",
  "61-90": "bg-amber-500",
  "90+": "bg-red-500",
};

// 以下保留原有别名以兼容已有测试 / hooks
export const statusConfigs = {
  pending: { label: "待收款", color: "bg-amber-500" },
  partial: { label: "部分收款", color: "bg-blue-500" },
  completed: { label: "已收款", color: "bg-emerald-500" },
  overdue: { label: "逾期", color: "bg-red-500" },
};

export const agingConfigs = {
  current: { label: "未到期", color: "bg-emerald-500", range: "0天" },
  "1-30": { label: "1-30天", color: "bg-amber-500", range: "1-30天" },
  "31-60": { label: "31-60天", color: "bg-orange-500", range: "31-60天" },
  "61-90": { label: "61-90天", color: "bg-red-400", range: "61-90天" },
  "90+": { label: "90天以上", color: "bg-red-600", range: ">90天" },
};
