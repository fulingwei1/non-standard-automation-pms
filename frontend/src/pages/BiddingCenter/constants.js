export const bidStatusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    pending: { label: '待提交', color: 'bg-amber-500' },
    submitted: { label: '已投标', color: 'bg-blue-500' },
    won: { label: '中标', color: 'bg-emerald-500' },
    lost: { label: '未中标', color: 'bg-red-500' },
    cancelled: { label: '已取消', color: 'bg-slate-400' },
};

export const bidTypeConfigs = {
    public: { label: '公开招标', icon: 'Globe' },
    invited: { label: '邀请招标', icon: 'Mail' },
    negotiation: { label: '竞争性谈判', icon: 'MessageSquare' },
    single: { label: '单一来源', icon: 'Target' },
};

export const evaluationCriteria = [
    { id: 'price', label: '价格', weight: 30 },
    { id: 'technical', label: '技术方案', weight: 30 },
    { id: 'experience', label: '项目经验', weight: 20 },
    { id: 'service', label: '售后服务', weight: 10 },
    { id: 'delivery', label: '交付周期', weight: 10 },
];

// 投标阶段配置
export const biddingStages = [
  { id: "tracking", name: "跟踪中", color: "bg-slate-500" },
  { id: "preparing", name: "准备中", color: "bg-blue-500" },
  { id: "submitted", name: "已投标", color: "bg-violet-500" },
  { id: "evaluating", name: "待开标", color: "bg-amber-500" },
  { id: "won", name: "已中标", color: "bg-emerald-500" },
  { id: "lost", name: "未中标", color: "bg-red-500" },
];

// 获取阶段样式
export const getStageStyle = (stage) => {
  const config = (biddingStages || []).find((s) => s.id === stage);
  return config?.color || "bg-slate-500";
};

// 获取阶段名称
export const getStageName = (stage) => {
  const config = (biddingStages || []).find((s) => s.id === stage);
  return config?.name || stage;
};

// Map backend status to frontend stage
export const mapTenderStatus = (backendStatus) => {
  const normalizedStatus = String(backendStatus || "").toUpperCase();
  const statusMap = {
    TRACKING: "tracking",
    PENDING: "tracking",
    PREPARING: "preparing",
    SUBMITTED: "submitted",
    EVALUATING: "evaluating",
    WON: "won",
    LOST: "lost",
  };
  return statusMap[normalizedStatus] || "tracking";
};
