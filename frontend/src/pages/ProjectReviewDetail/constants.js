export const reviewStatusConfigs = {
    pending: { label: '待评审', color: 'bg-amber-500' },
    in_review: { label: '评审中', color: 'bg-blue-500' },
    approved: { label: '已通过', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
    revised: { label: '需修改', color: 'bg-purple-500' },
};

export const reviewTypeConfigs = {
    kickoff: { label: '项目启动评审', icon: 'PlayCircle' },
    design: { label: '设计评审', icon: 'Pencil' },
    procurement: { label: '采购评审', icon: 'ShoppingCart' },
    production: { label: '生产评审', icon: 'Factory' },
    delivery: { label: '交付评审', icon: 'Truck' },
    closure: { label: '结项评审', icon: 'CheckCircle' },
};

export const decisionOptions = [
    { value: 'approve', label: '通过', color: 'bg-emerald-500' },
    { value: 'reject', label: '驳回', color: 'bg-red-500' },
    { value: 'revise', label: '需修改', color: 'bg-amber-500' },
];

export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
};

export const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export const INITIAL_LESSON_FORM = {
  title: "",
  description: "",
  category: "",
  impact: "",
  actions: "",
  tags: [],
};

export const INITIAL_PRACTICE_FORM = {
  title: "",
  description: "",
  category: "",
  applicability: "",
  benefits: "",
  implementation: "",
  tags: [],
};
