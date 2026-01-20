export const getPriorityStyle = (priority) => {
  switch (priority) {
    case "high":
      return "text-red-400 bg-red-500/10";
    case "medium":
      return "text-amber-400 bg-amber-500/10";
    case "low":
      return "text-slate-400 bg-slate-500/10";
    default:
      return "text-slate-400 bg-slate-500/10";
  }
};

export const getPriorityText = (priority) => {
  switch (priority) {
    case "high":
      return "紧急";
    case "medium":
      return "中等";
    case "low":
      return "普通";
    default:
      return "普通";
  }
};

export const getTypeColor = (type) => {
  const colorMap = {
    方案设计: "bg-violet-500",
    成本核算: "bg-emerald-500",
    成本支持: "bg-emerald-500",
    技术交流: "bg-blue-500",
    需求调研: "bg-emerald-500",
    投标支持: "bg-amber-500",
    方案评审: "bg-pink-500",
    可行性评估: "bg-cyan-500"
  };
  return colorMap[type] || "bg-slate-500";
};
