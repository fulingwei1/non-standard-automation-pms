export const levelConfigs = {
    VIP: { label: 'VIP', color: 'bg-purple-500', priority: 1 },
    A: { label: 'A级', color: 'bg-emerald-500', priority: 2 },
    B: { label: 'B级', color: 'bg-blue-500', priority: 3 },
    C: { label: 'C级', color: 'bg-amber-500', priority: 4 },
    D: { label: 'D级', color: 'bg-slate-500', priority: 5 },
};

export const industryConfigs = {
    electronics: '电子电器',
    automotive: '汽车制造',
    medical: '医疗器械',
    semiconductor: '半导体',
    new_energy: '新能源',
    other: '其他',
};

export const regionConfigs = {
    east: '华东',
    south: '华南',
    north: '华北',
    central: '华中',
    west: '西部',
    overseas: '海外',
};

export const gradeOptions = [
  { value: "all", label: "全部等级" },
  { value: "A", label: "A级客户" },
  { value: "B", label: "B级客户" },
  { value: "C", label: "C级客户" },
  { value: "D", label: "D级客户" },
];

export const statusOptions = [
  { value: "all", label: "全部状态" },
  { value: "active", label: "活跃客户" },
  { value: "potential", label: "潜在客户" },
  { value: "dormant", label: "沉睡客户" },
  { value: "lost", label: "流失客户" },
];

export const industryOptions = [
  { value: "all", label: "全部行业" },
  { value: "新能源电池", label: "新能源电池" },
  { value: "消费电子", label: "消费电子" },
  { value: "汽车零部件", label: "汽车零部件" },
  { value: "储能系统", label: "储能系统" },
  { value: "智能制造", label: "智能制造" },
  { value: "电子制造", label: "电子制造" },
];

export const gradeColors = {
  A: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  B: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  C: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  D: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

export const statusConfig = {
  active: {
    label: "活跃",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  potential: {
    label: "潜在",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  dormant: {
    label: "沉睡",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  lost: { label: "流失", color: "bg-red-500", textColor: "text-red-400" },
};
