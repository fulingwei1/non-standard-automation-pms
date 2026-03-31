// Empty fallback data (no mock)
export const emptyFallback = {
  ticketTrends: [],
  serviceTypeDistribution: [],
  problemTypeDistribution: [],
  satisfactionTrends: [],
  responseTimeDistribution: [],
  topCustomers: [],
  engineerPerformance: []
};

// Period options for the toolbar selector
export const PERIOD_OPTIONS = [
  { value: "DAILY",   label: "今日" },
  { value: "WEEKLY",  label: "本周" },
  { value: "MONTHLY", label: "本月" },
  { value: "YEARLY",  label: "本年" }
];

// Map a period value to its display label
export const PERIOD_LABEL = Object.fromEntries(
  PERIOD_OPTIONS.map(({ value, label }) => [value, label])
);

// Response-time bucket ranges used when building the distribution
export const RESPONSE_TIME_RANGES = [
  { key: "0-2小时",  max: 2 },
  { key: "2-4小时",  max: 4 },
  { key: "4-8小时",  max: 8 },
  { key: "8-24小时", max: 24 },
  { key: ">24小时",  max: Infinity }
];

// Metric display config (used by overview cards)
export const metricConfigs = {
  tickets:      { label: "工单数",   icon: "FileText",    color: "bg-blue-500"    },
  satisfaction: { label: "满意度",   icon: "ThumbsUp",    color: "bg-emerald-500" },
  responseTime: { label: "响应时间", icon: "Clock",       color: "bg-amber-500"   },
  resolution:   { label: "解决率",   icon: "CheckCircle", color: "bg-purple-500"  }
};
